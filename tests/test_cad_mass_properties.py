"""Arithmetic and feasibility tests for the G0 mass-property solver."""

from pathlib import Path
import json

import pytest

from scripts.cad_mass_properties import (
    Component,
    Transform,
    evaluate,
    load_model,
    solve,
)


ROOT = Path(__file__).resolve().parents[1]
MASS_CONFIGS = ROOT / "cad/parametric/configurations"


def test_weighted_centroid_and_total_mass():
    components = [
        Component.from_dict({"id": "a", "mass_g": 2, "com_mm": [0, 0, 0]}),
        Component.from_dict({"id": "b", "mass_g": 6, "com_mm": [8, 4, -2]}),
    ]
    result = evaluate(components)
    assert result["total_mass_g"] == pytest.approx(8)
    assert result["com_mm"] == pytest.approx((6, 3, -1.5))


def test_rigid_transform_moves_component_com_into_chassis_frame():
    transform = Transform.from_dict({
        "rotation": [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
        "translation_mm": [10, 20, 30],
    })
    component = Component.from_dict({
        "id": "rotated",
        "mass_g": 1,
        "com_mm": [2, 0, 4],
        "transform": {"rotation": [list(row) for row in transform.rotation], "translation_mm": list(transform.translation_mm)},
    })
    assert component.chassis_com_mm == pytest.approx((10, 22, 34))


def test_parallel_axis_inertia_is_reported_about_both_origins():
    component = Component.from_dict({
        "id": "point_mass",
        "mass_g": 10,
        "com_mm": [10, 0, 0],
        "inertia_tensor_g_mm2": [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
    })
    result = evaluate([component])
    assert result["inertia_tensor_about_chassis_origin_g_mm2"][1][1] == pytest.approx(1002)
    assert result["inertia_tensor_about_total_com_g_mm2"][0] == pytest.approx((1, 0, 0))
    assert result["inertia_tensor_about_total_com_g_mm2"][1] == pytest.approx((0, 2, 0))
    assert result["inertia_tensor_about_total_com_g_mm2"][2] == pytest.approx((0, 0, 3))


def test_infeasible_mass_target_is_flagged_instead_of_fabricated():
    document = {
        "schema_version": 1,
        "id": "infeasible",
        "target": {"target_mass_g": 100, "mass_tolerance_g": 0.1, "target_com_mm": None},
    }
    components = [Component.from_dict({"id": "base", "mass_g": 10, "com_mm": [0, 0, 0]})]
    ballast = [{
        "id": "small_ballast", "mass_g": 5, "axis": "X", "position_mm": [0, 0, 0],
        "travel_mm": [0, 10], "step_mm": 10,
    }]
    from scripts.cad_mass_properties import BallastSpec
    report = solve(document, components, [BallastSpec.from_dict(ballast[0])])
    assert report["search"]["feasible_count"] == 0
    assert report["search"]["best_is_feasible"] is False
    assert report["attainable_ranges"]["total_mass_g"] == [15, 15]


@pytest.mark.parametrize(
    ("config_name", "profile_id"),
    [("iphone15_mass.json", "iPhone15"), ("placeholder_android_mass.json", "placeholder_android")],
)
def test_both_phone_configurations_produce_explicit_model_reports(config_name, profile_id):
    path = MASS_CONFIGS / config_name
    document, components, ballast = load_model(path)
    report = solve(document, components, ballast)
    assert report["profile_id"] == profile_id
    assert report["status"] == "MODEL_OUTPUT"
    assert report["search"]["candidate_count"] > 1
    assert report["attainable_ranges"]["total_mass_g"][0] == report["attainable_ranges"]["total_mass_g"][1]
    assert report["attainable_ranges"]["com_mm"][0][0] < report["attainable_ranges"]["com_mm"][0][1]
    assert report["warnings"]


def test_phone_mass_override_is_visible_as_entered_value():
    document, components, ballast = load_model(MASS_CONFIGS / "iphone15_mass.json", phone_mass_override=180)
    phone = next(item for item in components if item.id == "phone")
    assert phone.mass_g == 180
    assert phone.value_status == "user_measured_or_entered"
