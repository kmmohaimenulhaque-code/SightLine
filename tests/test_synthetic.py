"""Synthetic generator: determinism and ground-truth consistency (DAT-02)."""

import hashlib

import numpy as np
import pytest

from app.calibration.camera import CameraModel
from app.scoring.issf import BLACK_RADIUS_MM, score_shot
from ml.datasets.synthetic_target import Degradation, SceneSpec, random_spec, render

CAM = CameraModel.from_hfov(1920, 1080, 25.0, k1=-0.05)


def _digest(img):
    return hashlib.sha256(img.tobytes()).hexdigest()


def test_same_seed_same_image_different_seed_different_noise():
    spec = SceneSpec(CAM, (CAM.cx, CAM.cy), (2.0, 3.0))
    a = render(spec, np.random.default_rng(11)).image
    b = render(spec, np.random.default_rng(11)).image
    c = render(spec, np.random.default_rng(12)).image
    assert _digest(a) == _digest(b)
    assert _digest(a) != _digest(c)


def test_ground_truth_is_self_consistent():
    rng = np.random.default_rng(5)
    for _ in range(5):
        s = render(random_spec(rng, CAM, Degradation()), rng)
        gt = s.ground_truth
        x, y = gt["impact_xy_mm"]
        assert gt["impact_score"] == score_shot(x, y).as_dict()
        u0, v0 = gt["canvas_origin_px"]
        assert gt["target_centre_px_canvas"] == pytest.approx([gt["target_centre_px"][0] - u0,
                                                               gt["target_centre_px"][1] - v0])
        black = gt["ring_ellipses_px"]["black_edge"]
        assert np.sqrt(black["a"] * black["b"]) == pytest.approx(BLACK_RADIUS_MM / gt["local_mm_per_px"], rel=5e-3)
        assert s.image.shape == tuple(reversed(gt["canvas_size_px"]))
        assert np.hypot(*gt["up_direction_px"]) == pytest.approx(1.0)


def test_full_mode_renders_the_whole_sensor():
    s = render(SceneSpec(CAM, (CAM.cx, CAM.cy), (0.0, 0.0)), np.random.default_rng(0), mode="full")
    assert s.image.shape == (CAM.height, CAM.width)
    assert s.origin_px == (0, 0)


def test_parameters_record_generator_identity():
    s = render(SceneSpec(CAM, (CAM.cx, CAM.cy), (0.0, 0.0)), np.random.default_rng(0))
    assert s.parameters["generator"]["name"] == "sightline.synthetic_target"
    assert s.parameters["camera"]["fx"] == pytest.approx(CAM.fx)
