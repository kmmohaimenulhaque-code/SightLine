"""E-002 / E-003 / CAL-EXP-6 harness logic, exercised on simulated input (never reported as experimental)."""

import json
import math

import numpy as np
import pytest

from app.calibration.camera import CameraModel
from app.vision.aiming_mark import linearize
from app.vision.characterise import blockiness, edge_metrics, radial_profile, temporal_noise
from ml.datasets.provenance import make_record, sha256_file
from ml.datasets.synthetic_sequence import render_sequence
from ml.datasets.synthetic_target import Degradation
from ml.evaluation import cal_exp6_gyro, e002_static_capture, e003_domain_gap

CAM = CameraModel(3840, 2160, 2890.0, 2890.0, 1919.5, 1079.5)
PARAMS = {"capture_id": "synthetic-static", "camera": "main_1x", "resolution": [3840, 2160], "device": "SYNTHETIC",
          "os_version": "n/a", "capture_app": "renderer", "codec": "none", "stabilisation_mode": "n/a", "fps": 30.0,
          "distance_mm": {"value": 10000.0, "sigma": 5.0},
          "target": {"black_diameter_mm": {"value": 59.5, "sigma": 0.2}}}


@pytest.fixture(scope="module")
def static_clip():
    frames, centres = render_sequence(CAM, np.zeros((330, 2)), np.random.default_rng(3), Degradation(jpeg_quality=None))
    return frames, centres


def test_e002_static_repeatability_in_px_mrad_and_mm(tmp_path, static_clip):
    frames, _ = static_clip
    s = e002_static_capture.analyse(PARAMS, "SYNTHETIC", ((i, i / 30.0, f) for i, f in enumerate(frames)), tmp_path)
    assert s["status"]["experiment_status"] == "PHYSICAL_DATA_REQUIRED" and s["status"]["evidence_class"] == "SIMULATED"
    r = s["result"]
    assert 0.003 < r["static"]["rms_px"] < 0.03                              # synthetic noise only
    assert r["at_target_mm"]["rms"] == pytest.approx(r["static"]["rms_px"] * r["at_target_mm"]["mm_per_px"])
    assert r["at_target_mm"]["mm_per_px"] == pytest.approx(10000.0 / 2890.0, rel=0.01)
    assert r["rms_mrad"] == pytest.approx(r["static"]["rms_px"] / s["focal_length_px"]["value"] * 1e3)
    assert set(r["rms_px_by_estimator"]) == {"ellipse", "moments", "centroid", "phase"}
    text = e002_static_capture.table([s])
    assert "PHYSICAL_DATA_REQUIRED" in text and "Precision only" in text       # no numbers shown for non-COMPLETE runs


def test_e002_rejects_clips_that_are_too_short(tmp_path, static_clip):
    frames, _ = static_clip
    s = e002_static_capture.analyse(PARAMS, "TEAM_COLLECTED", ((i, i / 30.0, f) for i, f in enumerate(frames[:90])), tmp_path)
    assert s["status"]["experiment_status"] == "INVALID" and "gap-free" in s["status"]["reason"]


def test_characterisation_recovers_the_generator_parameters(static_clip):
    frames, centres = static_clip
    stack = np.stack([linearize(f) for f in frames[:60]])
    cx, cy = centres[0]
    r, a = 29.75 / (10000.0 / 2890.0), None
    prof_r, prof_v, _ = radial_profile(stack.mean(axis=0), cx, cy, r, r, 0.0)
    m = edge_metrics(prof_r, prof_v, r)
    assert m["edge_sigma_px"] == pytest.approx(math.sqrt(0.7**2 + 1 / 12), rel=0.12)   # PSF + pixel aperture
    assert m["edge_50_radius_px"] == pytest.approx(r, abs=0.15)
    assert m["overshoot_fraction"] < 0.03                                               # no sharpening in the generator
    n = temporal_noise(stack, cx, cy, r)
    assert n["white_noise_rel"] == pytest.approx(1 / math.sqrt(0.85 * 3000.0), rel=0.25)  # shot noise at the white level
    assert abs(n["white_lag1_correlation"]) < 0.1                                       # frames are independent


def test_blockiness_detects_an_8_px_grid():
    rng = np.random.default_rng(0)
    smooth = rng.normal(100, 2, (64, 64))
    blocky = np.kron(rng.normal(100, 8, (8, 8)), np.ones((8, 8))) + rng.normal(0, 1, (64, 64))
    assert blockiness(smooth) == pytest.approx(1.0, abs=0.15)
    assert blockiness(blocky) > 3.0


def test_e003_gap_table_leaves_importance_undecided_and_stays_simulated(tmp_path, static_clip):
    frames, _ = static_clip
    s = e003_domain_gap.analyse(PARAMS, "SYNTHETIC", ((i, i / 30.0, f) for i, f in enumerate(frames[:40])), tmp_path)
    assert s["status"]["evidence_class"] == "SIMULATED"
    rows = {r["property"]: r for r in s["rows"]}
    assert len(rows) == len(e003_domain_gap.ROWS)
    assert abs(rows["Black radius (px)"]["relative_difference"]) < 0.02
    assert all("TO BE DECIDED" in r["importance"] for r in s["rows"])
    md = (tmp_path / "gap.md").read_text()
    assert "NOT experimental evidence" in md and "tone curve" in md


def _gyro_manifest(tmp_path, kind, omega, rate=100.0, category="TEAM_COLLECTED"):
    log = tmp_path / f"{kind[:4]}.csv"
    t = np.arange(len(omega)) / rate
    log.write_text("seconds_elapsed,x,y,z\n" + "\n".join(f"{a:.5f},{b:.8f},{c:.8f},{d:.8f}" for a, (b, c, d) in zip(t, omega)))
    rec = make_record("gyro-1", category, {"session": "test"},
                      [{"path": log.name, "sha256": sha256_file(log), "media_type": "text/csv"}],
                      {"experiment": "CAL-EXP-6", "capture_id": "gyro-1", "device": "phone", "os_version": "x", "app": "logger",
                       "kind": kind, "placement": "flat on a table", "requested_rate_hz": 100, "rate_unit": "rad/s"})
    return rec, log


def test_gyro_runner_static_and_axis_logs(tmp_path):
    rng = np.random.default_rng(1)
    rec, log = _gyro_manifest(tmp_path, "static", rng.normal(0, 1e-3, (6000, 3)) + [0.01, 0.0, -0.01])
    s = cal_exp6_gyro.analyse(rec, log, tmp_path / "a")
    assert s["status"]["experiment_status"] == "COMPLETE"
    assert s["sampling"]["rate_median_hz"] == pytest.approx(100.0)
    assert s["static"]["bias_rad_s"] == pytest.approx([0.01, 0.0, -0.01], abs=2e-4)
    assert any("too short" in w for w in s["warnings"]) and (tmp_path / "a" / "allan.csv").exists()
    omega = np.zeros((300, 3))
    omega[:, 0] = 0.4
    rec, log = _gyro_manifest(tmp_path, "axis:+pitch (lens end up)", omega)
    s = cal_exp6_gyro.analyse(rec, log, tmp_path / "b")
    assert s["axis"]["axis"] == "x" and s["axis"]["mean_rate_sign"] == 1


def test_gyro_runner_refuses_a_log_that_is_not_the_one_in_the_manifest(tmp_path):
    rec, log = _gyro_manifest(tmp_path, "static", np.zeros((500, 3)) + 1e-3)
    log.write_text(log.read_text() + "5.0,0,0,0\n")
    s = cal_exp6_gyro.analyse(rec, log, tmp_path / "c")
    assert s["status"]["experiment_status"] == "INVALID" and "sha256" in s["status"]["reason"]
