"""Capture manifests (brief §12, §21) and the rule that simulation can never become experimental evidence (§2, §29)."""

import copy
import json

import cv2
import numpy as np
import pytest

from ml.datasets import capture as c
from ml.evaluation.status import CLAIM_STATUSES, EXPERIMENT_STATUSES, evidence_class, result_status


def _filled(test="B_step"):
    tpl = c.new_capture_template("E-004a", None, test)
    p = tpl["parameters"]
    p.update(capture_id="team-20261010-e004a-main-01", operator="KM", captured_local="2026-10-10T15:20:00+06:00",
             device="iPhone 15", os_version="UNKNOWN", camera="main_1x", zoom_readout="UNKNOWN",
             capture_app="Blackmagic Camera", resolution=[3840, 2160], fps=30, codec="hevc", file_format="mov",
             stabilisation_mode="Off", hdr="off", focus="locked 0.83", exposure=1 / 120, iso=200, white_balance="locked",
             lighting="room light", orientation="landscape_right", distance_mm={"value": 5000.0, "sigma": 5.0},
             target={"print_id": "A4-v1", "black_diameter_mm": {"value": 59.3, "sigma": 0.3}, "card_mm": [170, 170],
                     "printer": "laser", "paper": "80 gsm"},
             physical_setup="board on two rods; phone clamped over the pivot rod")
    if test in ("B_step", "C_ramp"):
        p["jig"] = {"mechanism": "paper shims", "radius_mm": {"value": 400.0, "sigma": 1.0},
                    "pivot_ahead_mm": {"value": 10.0, "sigma": 5.0},
                    "plateaus": [{"displacement_mm": {"value": 0.0, "sigma": 0.0}},
                                 {"displacement_mm": {"value": 0.1, "sigma": 0.005}}]}
    tpl["files"] = [{"path": "IMG_0001.MOV", "sha256": "a" * 64, "media_type": "video/quicktime"}]
    return tpl


def test_template_is_not_a_valid_record_until_filled():
    with pytest.raises(ValueError, match="capture_id"):
        c.finalise(c.new_capture_template("E-004a", None, "A_static"))
    rec = c.finalise(_filled())
    assert rec["sample_id"] == "team-20261010-e004a-main-01" and rec["category"] == "TEAM_COLLECTED"
    assert c.validate_capture(rec) == []


@pytest.mark.parametrize("mutate, message", [
    (lambda p: p.update(distance_mm=None), "distance_mm"),
    (lambda p: p.update(device="UNKNOWN"), "may not be UNKNOWN"),
    (lambda p: p["target"].update(black_diameter_mm={"value": 59.5, "sigma": 0.0}), "uncertainty"),
    (lambda p: p["jig"].update(radius_mm={"value": 400.0, "sigma": 0.0}), "radius_mm.sigma"),
    (lambda p: p["jig"].update(plateaus=p["jig"]["plateaus"][:1]), "plateaus"),
    (lambda p: p.update(test="E_made_up"), "test must be one of"),
])
def test_incomplete_or_implausible_manifests_are_rejected(mutate, message):
    tpl = _filled()
    mutate(tpl["parameters"])
    with pytest.raises(ValueError, match=message):
        c.finalise(tpl)


def test_oscillation_needs_an_independent_rigid_gyro_reference():
    tpl = _filled("D_oscillation")
    with pytest.raises(ValueError, match="gyro_log"):
        c.finalise(tpl)
    tpl["parameters"]["gyro_log"].update(file="Gyroscope.csv", sha256="b" * 64, rigidly_fixed_to_camera=False)
    with pytest.raises(ValueError, match="rigidly_fixed"):
        c.finalise(tpl)
    tpl["parameters"]["gyro_log"]["rigidly_fixed_to_camera"] = True
    assert c.finalise(tpl)["parameters"]["test"] == "D_oscillation"


def test_synthetic_data_cannot_be_registered_as_a_physical_capture():
    tpl = _filled()
    tpl["category"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="TEAM_COLLECTED"):
        c.finalise(tpl)


def test_template_from_video_and_checksum_check(tmp_path):
    path = str(tmp_path / "clip.avi")
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (64, 48), False)
    if not w.isOpened():
        pytest.skip("no MJPG encoder in this OpenCV build")
    for _ in range(5):
        w.write(np.zeros((48, 64), np.uint8))
    w.release()
    tpl = c.new_capture_template("E-004a", path, "B_step")
    assert tpl["parameters"]["resolution"] == [64, 48] and len(tpl["files"][0]["sha256"]) == 64
    assert tpl["parameters"]["device"] is None                      # the file cannot tell us; the operator must
    filled = _filled()
    errors, _ = c.check_against_video(c.finalise(filled), path)      # manifest lists a different checksum
    assert any("sha256" in e for e in errors)
    filled["files"] = copy.deepcopy(tpl["files"])
    errors, warnings = c.check_against_video(c.finalise(filled), path)
    assert errors == [] and any("resolution" in x for x in warnings)
    assert c.main(["new", "--experiment", "E-002", "--video", path, "--out", str(tmp_path)]) == 0
    written = json.loads((tmp_path / "TEMPLATE_E-002_clip.json").read_text())
    assert written["parameters"]["experiment"] == "E-002"
    assert c.main(["validate", str(tmp_path / "TEMPLATE_E-002_clip.json")]) == 1


def test_status_vocabulary_is_exactly_the_agreed_one():
    assert EXPERIMENT_STATUSES == ("PLANNED", "IMPLEMENTED", "PHYSICAL_DATA_REQUIRED", "RUNNING", "COMPLETE", "FAILED",
                                   "INVALID", "BLOCKED")
    assert set(CLAIM_STATUSES) == {"VERIFIED", "EXPERIMENTAL", "SIMULATED", "DERIVED", "ASSUMED", "UNVERIFIED", "REFUTED"}


def test_only_team_collected_data_can_complete_an_experiment():
    assert result_status("TEAM_COLLECTED", True) == {"experiment_status": "COMPLETE", "evidence_class": "EXPERIMENTAL"}
    bad = result_status("TEAM_COLLECTED", False, "plateau count mismatch")
    assert bad["experiment_status"] == "INVALID" and bad["evidence_class"] == "NONE"
    for category in ("SYNTHETIC", "SIMULATION_OUTPUT", "MODEL_OUTPUT", "EXTERNAL"):
        st = result_status(category, True)
        assert st["experiment_status"] == "PHYSICAL_DATA_REQUIRED"
        assert st["evidence_class"] != "EXPERIMENTAL" and "NOT experimental evidence" in st["banner"]


def test_derived_data_is_experimental_only_if_all_parents_are():
    assert evidence_class("DERIVED", ("TEAM_COLLECTED", "TEAM_COLLECTED")) == "EXPERIMENTAL"
    assert evidence_class("DERIVED", ("TEAM_COLLECTED", "SYNTHETIC")) == "SIMULATED"
    with pytest.raises(ValueError):
        evidence_class("DERIVED")
    with pytest.raises(ValueError):
        evidence_class("REAL")
