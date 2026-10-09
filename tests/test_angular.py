"""Angular ground truth and expected image motion (E-004a geometry; DERIVED)."""

import math

import pytest

from app.calibration.angular import (
    Measured,
    angle_from_image_shift_rad,
    expected_image_shift_px,
    exposure_response,
    focal_px_from_target,
    lever_angle_rad,
)


def test_lever_angle_small_angle_and_uncertainty():
    th = lever_angle_rad(Measured(0.10, 0.005), Measured(400.0, 1.0))
    assert th.value == pytest.approx(0.25e-3, rel=1e-6)                 # 0.1 mm at 400 mm = 0.25 mrad
    assert th.sigma == pytest.approx(0.25e-3 * math.hypot(0.05, 0.0025), rel=1e-4)
    assert lever_angle_rad(2.0, 1000.0).value == pytest.approx(math.atan(0.002))
    with pytest.raises(ValueError):
        lever_angle_rad(1.0, 0.0)


def test_small_angle_approximation_error_is_negligible_in_the_test_range():
    for mrad in (0.1, 0.25, 0.5, 1.0, 2.0):
        d_over_r = mrad * 1e-3
        assert abs(math.atan(d_over_r) - d_over_r) / d_over_r < 2e-6


def test_expected_shift_matches_exact_pinhole_projection():
    f, theta = 2890.0, 1e-3
    assert expected_image_shift_px(theta, f).value == pytest.approx(f * math.tan(theta))
    assert angle_from_image_shift_rad(expected_image_shift_px(theta, f).value, f) == pytest.approx(theta)


def test_pivot_parallax_term_against_explicit_geometry():
    """Camera pupil 300 mm ahead of the pivot, target 5 m from the pupil: rotate about the pivot and project."""
    f, theta, rho, dist = 2890.0, 2e-3, 300.0, 5000.0
    cam = (rho * math.sin(theta), rho * math.cos(theta))                # pupil position after the rotation (x, z)
    target = (0.0, rho + dist)
    bearing = math.atan2(target[0] - cam[0], target[1] - cam[1]) - theta  # relative to the rotated optical axis
    exact = abs(f * math.tan(bearing))
    model = expected_image_shift_px(theta, f, pivot_ahead_mm=rho, target_distance_mm=dist).value
    assert model == pytest.approx(exact, rel=1e-4)
    assert model / (f * math.tan(theta)) == pytest.approx(1.06, abs=1e-3)   # 6 % — not negligible


def test_uncertainty_propagation_of_expected_shift():
    e = expected_image_shift_px(Measured(1e-3, 5e-5), Measured(2890.0, 29.0))
    assert e.sigma / e.value == pytest.approx(math.hypot(0.05, 0.01), rel=1e-3)


def test_focal_length_from_the_printed_target():
    f = focal_px_from_target(Measured(17.2, 0.05), Measured(59.5, 0.3), Measured(10000.0, 10.0))
    assert f.value == pytest.approx(17.2 * 10000.0 / 59.5)
    assert f.relative == pytest.approx(math.sqrt((0.05 / 17.2) ** 2 + (0.3 / 59.5) ** 2 + 1e-6), rel=1e-6)


def test_exposure_response_is_a_sinc():
    assert exposure_response(0.0, 1 / 60) == 1.0
    assert exposure_response(10.0, 1 / 60) == pytest.approx(0.9549, abs=1e-4)
    assert exposure_response(60.0, 1 / 60) == pytest.approx(0.0, abs=1e-12)


def test_measured_accepts_common_forms_and_rejects_bad_values():
    assert Measured.of({"value": 2.0, "sigma": 0.1}) == Measured(2.0, 0.1)
    assert Measured.of((3.0, 0.2)) == Measured(3.0, 0.2)
    assert Measured.of(4) == Measured(4.0, 0.0)
    with pytest.raises(ValueError):
        Measured(1.0, -0.1)
