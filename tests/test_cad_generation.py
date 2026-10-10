"""Focused regression tests for the dependency-free G0 CAD export path."""

from pathlib import Path
import json
import re

import pytest

from scripts.generate_cad import generate, load_sources, read_ascii_stl, validate_export_dir


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "cad/parametric/configurations"


def test_regeneration_is_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate(CONFIGS / "iphone15_g0.json", first)
    generate(CONFIGS / "iphone15_g0.json", second)
    first_files = sorted(p.relative_to(first) for p in first.iterdir())
    second_files = sorted(p.relative_to(second) for p in second.iterdir())
    assert first_files == second_files
    for relative in first_files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes(), relative


def test_profile_variation_changes_the_editable_phone_envelope(tmp_path):
    iphone_dir = tmp_path / "iphone"
    android_dir = tmp_path / "android"
    iphone = generate(CONFIGS / "iphone15_g0.json", iphone_dir)
    android = generate(CONFIGS / "placeholder_android_g0.json", android_dir)
    assert iphone["profile_id"] == "iPhone15"
    assert android["profile_id"] == "placeholder_android"
    assert iphone["phone"]["body_mm"] != android["phone"]["body_mm"]
    iphone_phone = next(c for c in iphone["components"] if c["id"] == "phone_reference")
    android_phone = next(c for c in android["components"] if c["id"] == "phone_reference")
    assert iphone_phone["bounds_mm"] != android_phone["bounds_mm"]
    assert (iphone_dir / "iphone_adapter.stl").exists()
    assert (android_dir / "android_adapter.stl").exists()


@pytest.mark.parametrize("config_name", ["iphone15_g0.json", "placeholder_android_g0.json"])
def test_every_exported_stl_is_watertight_with_positive_volume(tmp_path, config_name):
    output = tmp_path / Path(config_name).stem
    manifest = generate(CONFIGS / config_name, output)
    assert manifest["validation"]["passed"]
    for component in manifest["components"]:
        mesh = read_ascii_stl(output / component["stl"])
        stats = mesh.validate()
        assert stats["watertight"] is True
        assert stats["triangles"] > 0
        assert stats["volume_mm3"] > 0


def test_ballast_capture_end_stops_and_collision_checks_pass(tmp_path):
    manifest = generate(CONFIGS / "iphone15_g0.json", tmp_path / "exports")
    validation = manifest["validation"]
    assert validation["capture"]["x_ballast"]["passed"]
    assert validation["capture"]["vertical_ballast"]["passed"]
    assert validation["capture"]["x_ballast"]["end_stops"] == ["x_end_stop_rear", "x_end_stop_targetward"]
    assert validation["capture"]["vertical_ballast"]["end_stops"] == ["vertical_end_stop_lower", "vertical_end_stop_upper"]
    assert validation["forbidden_collisions"]["passed"]
    assert validation["envelope"]["passed"]


def test_manifest_lists_required_exports_and_existing_step(tmp_path):
    output = tmp_path / "exports"
    manifest = generate(CONFIGS / "iphone15_g0.json", output)
    on_disk = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk == manifest
    assert validate_export_dir(output)["passed"]
    assert manifest["exports"]["assembly_step"] == "assembly.step"
    assert (output / "assembly.step").read_text(encoding="ascii").startswith("ISO-10303-21;")
    required_roles = {"training_chassis", "grip_body", "phone_adapter", "phone_retainer", "phone_pad",
                      "x_carriage", "x_end_stop", "vertical_cassette", "vertical_end_stop", "fiducial_mount"}
    assert required_roles <= {component["role"] for component in manifest["components"]}


def test_step_export_has_no_dangling_entity_references(tmp_path):
    output = tmp_path / "exports"
    generate(CONFIGS / "iphone15_g0.json", output)
    step = (output / "assembly.step").read_text(encoding="ascii")
    entity_ids = {int(match) for match in re.findall(r"^#(\d+)=", step, flags=re.MULTILINE)}
    referenced_ids = {int(match) for match in re.findall(r"#(\d+)", step)}
    assert step.startswith("ISO-10303-21;")
    assert "POLY_LOOP" not in step
    assert referenced_ids <= entity_ids


def test_source_profile_status_does_not_claim_unmeasured_android_dimensions():
    _, profile, _ = load_sources(CONFIGS / "placeholder_android_g0.json")
    assert "NOT measured" in profile["dimension_status"]
    assert profile["camera_centres_mm"] is None
