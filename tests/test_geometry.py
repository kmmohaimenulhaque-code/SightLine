"""Camera model, target pose, bore-axis geometry and display maths."""

import numpy as np
import pytest

from app.calibration.camera import CameraModel
from app.calibration.display import on_screen_size_mm, target_anchored_scale, unity_magnification_scale
from app.calibration.pose import bore_impact_mm, pose_from_aim


def test_focal_length_from_hfov():
    cam = CameraModel.from_hfov(1920, 1080, 67.0)
    assert cam.fx == pytest.approx(1450.40, abs=0.01)  # 960 / tan(33.5 deg)
    assert cam.mm_per_pixel_on_axis(10000.0) == pytest.approx(6.895, abs=0.001)


@pytest.mark.parametrize("k1, k2", [(0.0, 0.0), (-0.12, 0.03), (0.08, -0.01)])
def test_projection_roundtrip_with_distortion(k1, k2):
    cam = CameraModel.from_hfov(1920, 1080, 67.0, k1=k1, k2=k2)
    uu, vv = np.meshgrid(np.linspace(0, 1919, 25), np.linspace(0, 1079, 15))
    uv = np.stack([uu.ravel(), vv.ravel()], axis=1)
    back = cam.normalized_to_pixel(cam.pixel_to_normalized(uv))
    assert np.max(np.abs(back - uv)) < 1e-6
    rays = cam.pixel_rays(uv)
    assert np.allclose(np.linalg.norm(rays, axis=1), 1.0)


@pytest.mark.parametrize("yaw, pitch, roll", [(0, 0, 0), (12, -7, 3), (-20, 15, -10)])
def test_pose_from_aim_places_the_bore_ray_on_the_requested_impact(yaw, pitch, roll):
    cam = CameraModel.from_hfov(1920, 1080, 25.0, k1=-0.05)
    bore = (cam.cx + 37.3, cam.cy - 12.1)
    pose = pose_from_aim(cam, bore, (6.5, -11.25), 10012.0, yaw, pitch, roll)
    assert np.allclose(bore_impact_mm(cam, pose, bore), [6.5, -11.25], atol=1e-9)


def test_unity_magnification_and_target_anchored_scale_agree():
    f_px, eye, ppi = 1449.9, 700.0, 460.0
    s1 = unity_magnification_scale(f_px, eye, ppi)
    black_px = 59.5 / (10000.0 / f_px)  # black diameter in camera pixels at 10 m
    s2 = target_anchored_scale(black_px, eye, ppi)
    assert s1 == pytest.approx(8.74, abs=0.01)
    assert s2 == pytest.approx(s1, rel=1e-9)
    assert on_screen_size_mm(59.5, eye) == pytest.approx(4.165)
