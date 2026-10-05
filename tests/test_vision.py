"""Deterministic baseline on synthetic frames (SIMULATED evidence; see E-001 for the full characterisation)."""

import cv2
import numpy as np
import pytest

from app.calibration.camera import CameraModel
from app.vision.aiming_mark import linearize, measure_aiming_mark_all, measure_shot, shot_from_mark
from ml.datasets.synthetic_target import Degradation, SceneSpec, random_spec, render

PRESETS = {
    "wide_1080p": CameraModel.from_hfov(1920, 1080, 67.0),
    "wide_12mp": CameraModel.from_hfov(4032, 3024, 67.0),
    "tele3x_1080p": CameraModel.from_hfov(1920, 1080, 25.0),
    "tele3x_12mp": CameraModel.from_hfov(4032, 3024, 25.0),
}
CLEAN = Degradation(psf_sigma_px=0.7, electrons_per_unit=1e9, read_noise_e=0.0, adc_bits=16, jpeg_quality=None)


@pytest.mark.parametrize("preset", list(PRESETS))
@pytest.mark.parametrize("pose", [(0, 0, 0, (3.0, -2.0)), (8, -6, 2, (10.0, 5.0)), (25, 0, 0, (6.0, 6.0))])
def test_clean_frames_radial_error_below_0_05_mm(preset, pose):
    cam = PRESETS[preset]
    yaw, pitch, roll, impact = pose
    s = render(SceneSpec(cam, (cam.cx, cam.cy), impact, 10000.0, yaw, pitch, roll, degradation=CLEAN),
               np.random.default_rng(1))
    res = measure_aiming_mark_all(s.image)
    gt = np.array(s.ground_truth["impact_xy_mm"])
    for method in ("moments", "hybrid"):
        shot = shot_from_mark(res[method], s.bore_px_canvas, up_direction_px=s.ground_truth["up_direction_px"])
        assert abs(np.hypot(*shot.impact_xy_mm) - np.hypot(*gt)) < 0.05, method
        assert np.hypot(*(shot.impact_xy_mm - gt)) < 0.1, method
        assert shot.score.decimal_tenths == pytest.approx(s.ground_truth["impact_score"]["decimal"] * 10, abs=1)


@pytest.mark.parametrize("preset, p95_limit", [("wide_1080p", 0.35), ("tele3x_1080p", 0.15)])
def test_good_light_noise_meets_est_grade_target(preset, p95_limit):
    cam = PRESETS[preset]
    rng = np.random.default_rng(42)
    errors = []
    for _ in range(40):
        s = render(random_spec(rng, cam, Degradation()), rng)
        shot = measure_shot(s.image, s.bore_px_canvas, "hybrid",
                            up_direction_px=s.ground_truth["up_direction_px"])
        assert shot is not None
        errors.append(np.hypot(*(shot.impact_xy_mm - np.array(s.ground_truth["impact_xy_mm"]))))
    assert np.percentile(errors, 95) < p95_limit


def test_full_frame_detection_ignores_distractors():
    cam = PRESETS["wide_1080p"]
    rng = np.random.default_rng(3)
    spec = SceneSpec(cam, (cam.cx + 3.3, cam.cy - 2.1), (4.0, -9.0), 10000.0, 5.0, -4.0, 1.0)
    s = render(spec, rng, mode="full")
    img = s.image.copy()
    cv2.rectangle(img, (200, 200), (209, 209), 5, -1)        # small black square on the wall
    cv2.circle(img, (1500, 300), 5, 10, -1)                   # dark disc without a white surround
    img[700:1000, 100:500] = (img[700:1000, 100:500] * 0.2).astype(np.uint8)  # dark wall region
    res = measure_aiming_mark_all(img)
    centre = np.array(s.ground_truth["target_centre_px"])
    assert np.hypot(*(res["hybrid"].centre_px - centre)) < 0.3


def test_no_target_returns_nothing():
    rng = np.random.default_rng(0)
    noise = np.clip(rng.normal(120, 10, (480, 640)), 0, 255).astype(np.uint8)
    assert measure_aiming_mark_all(noise) == {}
    assert measure_shot(noise, (320, 240)) is None


def test_linearize_scales_integers():
    img = np.array([[0, 255]], dtype=np.uint8)
    assert linearize(img, gamma=None).tolist() == [[0.0, 1.0]]
    assert linearize(img, gamma=2.2)[0, 1] == pytest.approx(1.0)
