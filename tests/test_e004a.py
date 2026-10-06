"""E-004a harness logic on small synthetic sequences (SIMULATED): the checks that protect the experiment's integrity."""

import json
import math

import numpy as np
import pytest

from app.calibration.camera import CameraModel
from ml.datasets.synthetic_sequence import render_sequence
from ml.evaluation import e004a_ois_transfer as e

CFG = json.load(open("ml/configs/e004a.json"))
CAM = CameraModel(3840, 2160, 2890.0, 2890.0, 1919.5, 1079.5)
BASE = {"capture_id": "synthetic-test", "camera": "main_1x", "resolution": [3840, 2160], "device": "SYNTHETIC",
        "os_version": "n/a", "capture_app": "renderer", "codec": "none", "stabilisation_mode": "n/a", "fps": 30.0,
        "distance_mm": {"value": 10000.0, "sigma": 5.0}, "target": {"black_diameter_mm": {"value": 59.5, "sigma": 0.2}}}


def _steps(levels_mrad, gain=1.0, frames_per_level=24, seed=0):
    theta = np.repeat(np.asarray(levels_mrad) * 1e-3 * gain, frames_per_level)
    frames, _ = render_sequence(CAM, np.column_stack([np.zeros_like(theta), theta]), np.random.default_rng(seed))
    n = frames_per_level / 30.0
    jig = {"radius_mm": {"value": 400.0, "sigma": 1.0}, "pivot_ahead_mm": {"value": 0.0, "sigma": 0.0},
           "plateaus": [{"displacement_mm": {"value": 400.0 * math.tan(a * 1e-3), "sigma": 0.004},
                         "window_s": [k * n + 0.05, (k + 1) * n - 0.05]} for k, a in enumerate(levels_mrad)]}
    return [(i, i / 30.0, f) for i, f in enumerate(frames)], jig


@pytest.mark.parametrize("gain", [1.0, 0.4])
def test_step_analysis_recovers_the_injected_response_and_stays_non_experimental(tmp_path, gain):
    items, jig = _steps([0.0, 0.5, 1.0], gain)
    s = e.analyse(dict(BASE, test="B_step", jig=jig), "SYNTHETIC", items, tmp_path)
    assert s["status"]["experiment_status"] == "PHYSICAL_DATA_REQUIRED"        # never COMPLETE from simulation
    assert s["status"]["evidence_class"] == "SIMULATED"
    assert s["focal_length_px"]["value"] == pytest.approx(2890.0, rel=0.01)    # measured from the target, not assumed
    rows = s["result"]["steps"]["rows"]
    assert [r["response_ratio"] for r in rows[1:]] == pytest.approx([gain, gain], abs=0.04)
    assert rows[1]["response_ratio_sigma"] >= 0.02 * gain                       # 0.004 mm on a 0.2 mm step is 2 %
    header = (tmp_path / "frames.csv").read_text().splitlines()[0]
    for col in ("frame_id", "timestamp_s", "camera", "resolution", "fps", "x", "y", "ellipse_centre_x",
                "ellipse_centre_y", "confidence", "estimated_rotation_mrad", "expected_rotation_mrad", "residual_mrad"):
        assert col in header.split(",")


def test_plateau_count_mismatch_makes_the_run_invalid_instead_of_guessing(tmp_path):
    items, jig = _steps([0.0, 1.0], frames_per_level=40)
    for p in jig["plateaus"]:
        p.pop("window_s")                                   # automatic segmentation finds 2 plateaus
    jig["plateaus"].append({"displacement_mm": {"value": 0.8, "sigma": 0.004}})   # ... but the manifest claims 3
    s = e.analyse(dict(BASE, test="B_step", jig=jig), "TEAM_COLLECTED", items, tmp_path)
    assert s["status"]["experiment_status"] == "INVALID"
    assert "plateaus" in s["status"]["reason"] and s["result"] == {}


def test_too_many_unusable_frames_invalidate_a_run(tmp_path):
    items, _ = _steps([0.0], frames_per_level=30)
    for k in range(5, 12):
        items[k] = (k, items[k][1], np.full_like(items[k][2], 128))
    s = e.analyse(dict(BASE, test="A_static"), "TEAM_COLLECTED", items, tmp_path)
    assert s["status"]["experiment_status"] == "INVALID" and "unusable" in s["status"]["reason"]
    assert s["tracking"]["n_invalid"] == 7


def _summary(camera, ratio, sigma=0.03, status="COMPLETE"):
    row = {"theta_mrad": 1.0, "theta_sigma_mrad": 0.02, "observed_px": ratio * 2.89, "response_ratio": ratio,
           "response_ratio_sigma": sigma}
    return {"capture_id": f"c-{camera}", "test": "B_step", "focal_length_px": {"value": 2890.0},
            "status": {"experiment_status": status}, "result": {"steps": {"rows": [{}, row]}},
            "scope": {"camera": camera, "device": "iPhone 15", "os_version": "iOS X", "capture_app": "app",
                      "resolution": [3840, 2160], "fps": 30, "codec": "hevc", "stabilisation_mode": "Off"}}


@pytest.mark.parametrize("main, uw, phrase", [
    (0.2, 1.0, "strong evidence that stabilisation"),
    (1.0, 1.01, "No suppression"),
    (0.3, 0.3, "both cameras showed less motion"),
    (0.3, 0.85, "INVALID comparison"),
])
def test_comparison_reading_follows_the_stated_rules_and_is_scoped(main, uw, phrase):
    text = e.compare([_summary("main_1x", main), _summary("ultra_wide", uw)], CFG["thresholds"])
    assert phrase in text
    assert "not a statement about iPhones in general" in text
    assert "iPhone 15" in text and "Off" in text


def test_comparison_refuses_runs_that_are_not_complete():
    text = e.compare([_summary("main_1x", 0.2, status="PHYSICAL_DATA_REQUIRED"), _summary("ultra_wide", 1.0)],
                     CFG["thresholds"])
    assert "No comparison possible" in text and "Excluded" in text


def test_classification_uses_uncertainty():
    th = CFG["thresholds"]
    assert e.classify(0.95, 0.02, th) == "TRACKS"
    assert e.classify(0.5, 0.05, th) == "SUPPRESSED"
    assert e.classify(0.6, 0.3, th) == "INCONCLUSIVE"       # low, but not distinguishable from 1 at 2 sigma
    assert e.classify(0.85, 0.02, th) == "INCONCLUSIVE"


def test_expected_table_is_labelled_derived_and_uses_no_marketing_focal_length():
    text = e.expected_table(CFG)
    assert "DERIVED, not measured" in text and "prior estimates" in text
    assert "2.89 px" in text                                # 1 mrad at the 2890 px prior
    assert "0.100 mm" in text                               # 0.25 mrad at a 400 mm lever
