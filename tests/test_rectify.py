"""Target-anchored rectification (D-003): error of the local-affine model, independent of image noise.

The imaged black edge is computed exactly (projection of the 29.75 mm circle) and fitted with the direct ellipse fit;
the bore pixel is then mapped to target millimetres and compared with the exact ray-plane intersection.
"""

import numpy as np
import pytest

from app.calibration.camera import CameraModel
from app.calibration.ellipse import Ellipse, fit_ellipse_direct
from app.calibration.pose import bore_impact_mm, pose_from_aim
from app.calibration.rectify import ellipse_to_target_affine, image_to_target_mm
from app.scoring.issf import BLACK_RADIUS_MM

_S = np.linspace(0.0, 2.0 * np.pi, 180, endpoint=False)
_CIRCLE = np.stack([BLACK_RADIUS_MM * np.cos(_S), BLACK_RADIUS_MM * np.sin(_S)], axis=1)


def _up(cam, pose):
    p = pose.project(cam, np.array([[0.0, -0.5], [0.0, 0.5]]))
    d = p[1] - p[0]
    return d / np.hypot(*d)


def test_ellipse_fit_recovers_known_ellipse():
    e = Ellipse(400.25, 300.75, 21.3, 17.9, 0.61)
    f = fit_ellipse_direct(e.points(64))
    assert (f.cx, f.cy, f.a, f.b) == pytest.approx((e.cx, e.cy, e.a, e.b), abs=1e-6)
    assert f.theta % np.pi == pytest.approx(e.theta % np.pi, abs=1e-6)


def test_local_affine_model_error_is_negligible_for_scoring_offsets():
    """Bore near the image centre (as when aiming), offsets up to 40 mm (rings 10-6), tilt up to 20 deg,
    k1 = -0.1 distortion: radial error < 0.05 mm (8x below the 0.4 mm EST-grade target)."""
    rng = np.random.default_rng(7)
    cam = CameraModel.from_hfov(1920, 1080, 67.0, k1=-0.10, k2=0.02)
    worst_radial = worst_vector = 0.0
    for _ in range(600):
        bore = (cam.cx + rng.uniform(-100, 100), cam.cy + rng.uniform(-100, 100))
        rad, ang = rng.uniform(0, 40), rng.uniform(0, 2 * np.pi)
        imp = (rad * np.cos(ang), rad * np.sin(ang))
        yaw, pitch = rng.uniform(-20, 20, 2)
        pose = pose_from_aim(cam, bore, imp, rng.uniform(9950, 10050), yaw, pitch, rng.uniform(-10, 10))
        e = fit_ellipse_direct(pose.project(cam, _CIRCLE))
        gt = bore_impact_mm(cam, pose, bore)
        est = image_to_target_mm(e, np.array(bore), up_direction_px=_up(cam, pose))
        worst_radial = max(worst_radial, abs(np.hypot(*est) - np.hypot(*gt)))
        worst_vector = max(worst_vector, np.hypot(*(est - gt)))
    assert worst_radial < 0.05
    assert worst_vector < 0.07


def test_perspective_bias_of_the_ellipse_centre_is_tiny_at_10_m():
    cam = CameraModel.from_hfov(1920, 1080, 67.0)
    pose = pose_from_aim(cam, (cam.cx, cam.cy), (0.0, 0.0), 10000.0, 20.0, -20.0, 0.0)
    e = fit_ellipse_direct(pose.project(cam, _CIRCLE))
    centre = pose.project(cam, np.zeros((1, 2)))[0]
    assert np.hypot(*(e.centre - centre)) < 0.01  # pixels


def test_roll_changes_direction_not_distance():
    e = Ellipse(100.0, 80.0, 10.0, 9.5, 0.3)
    p = np.array([104.0, 77.0])
    a = image_to_target_mm(e, p, roll_deg=0.0)
    b = image_to_target_mm(e, p, roll_deg=25.0)
    assert np.hypot(*a) == pytest.approx(np.hypot(*b), rel=1e-12)
    assert not np.allclose(a, b)


def test_affine_flips_image_down_to_target_up():
    e = Ellipse(50.0, 50.0, 10.0, 10.0, 0.0)
    A = ellipse_to_target_affine(e)
    up_in_image = np.array([50.0, 40.0, 1.0])  # 10 px above the centre (v decreases)
    assert A @ up_in_image == pytest.approx([0.0, BLACK_RADIUS_MM])
