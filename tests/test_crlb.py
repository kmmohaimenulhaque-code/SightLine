"""Cramer-Rao machinery (DERIVED theory) checked against closed forms and a Monte-Carlo estimator."""

import math

import numpy as np
import pytest

from app.calibration.camera import CameraModel
from ml.datasets.synthetic_target import Degradation, SceneSpec, expected_canvas, render
from ml.evaluation.crlb import crlb_covariance, fisher_information, numerical_jacobian
from ml.evaluation.e005_localisation_limit import impact_bound


def test_gaussian_spot_location_bound_matches_the_closed_form():
    """Densely sampled Gaussian spot, amplitude A, width s, white pixel noise n: var(x0) = 2 n^2 / (pi A^2)."""
    yy, xx = np.mgrid[0:61, 0:61].astype(float)
    amp, s, noise = 100.0, 3.0, 2.0
    spot = lambda th: amp * np.exp(-((xx - th[0]) ** 2 + (yy - th[1]) ** 2) / (2 * s * s))
    jac = numerical_jacobian(spot, np.array([30.2, 29.7]), np.array([1e-3, 1e-3]))
    cov = crlb_covariance(fisher_information(jac, np.full(xx.size, noise**2)))
    assert cov[0, 0] == pytest.approx(2 * noise**2 / (math.pi * amp**2), rel=1e-3)
    assert abs(cov[0, 1]) < 1e-3 * cov[0, 0]


def test_unknown_nuisance_never_lowers_the_bound_and_least_squares_attains_it():
    rng = np.random.default_rng(0)
    x = np.linspace(-1, 1, 50)
    model = lambda th: th[0] * x + th[1]                       # slope + offset, noise sigma 0.1
    fisher = fisher_information(numerical_jacobian(model, np.array([2.0, 0.5]), np.array([1e-4, 1e-4])), np.full(50, 0.01))
    with_nuisance = crlb_covariance(fisher, [0])[0, 0]
    known = crlb_covariance(fisher, [0], nuisance_known=True)[0, 0]
    assert with_nuisance >= known * (1 - 1e-9)
    fits = [np.polyfit(x, model([2.0, 0.5]) + rng.normal(0, 0.1, 50), 1)[0] for _ in range(4000)]
    assert np.var(fits) == pytest.approx(with_nuisance, rel=0.08)


def test_expected_canvas_is_the_mean_of_rendered_frames_and_bounds_are_fixed():
    cam = CameraModel.from_hfov(1920, 1080, 25.0)
    deg = Degradation(electrons_per_unit=500.0, read_noise_e=2.0, adc_bits=16, jpeg_quality=None, gamma=1.0)
    spec = SceneSpec(cam, (cam.cx, cam.cy), (2.0, -1.0), degradation=deg)
    canvas, _, bounds = expected_canvas(spec)
    rng = np.random.default_rng(1)
    mean = np.mean([render(spec, rng, bounds=bounds).image.astype(float) for _ in range(60)], axis=0)
    expected = canvas * deg.gain_headroom * 255.0
    assert np.abs(mean - expected).mean() < 1.5              # 8-bit counts; noise of the 60-frame mean
    shifted, _, b2 = expected_canvas(SceneSpec(cam, (cam.cx, cam.cy), (12.0, -1.0), degradation=deg), bounds=bounds)
    assert b2 == bounds and shifted.shape == canvas.shape and not np.allclose(shifted, canvas)
    with pytest.raises(ValueError):
        expected_canvas(spec, bounds=(-5, 0, 10, 10))


def test_impact_bound_scales_with_light_as_shot_noise_predicts():
    cam = CameraModel.from_hfov(1920, 1080, 67.0)
    steps = np.array([0.05, 0.05, 10.0, 0.1, 0.1, 0.01, 0.01, 0.02])
    def bound(electrons):
        spec = SceneSpec(cam, (cam.cx, cam.cy), (4.0, 3.0), 10000.0, 6.0, -4.0, 1.0,
                         degradation=Degradation(electrons_per_unit=electrons, read_noise_e=0.0))
        return impact_bound(spec, steps, 57.75, 4)
    bright, dim = bound(3000.0), bound(300.0)
    assert dim["trace_mm2"] / bright["trace_mm2"] == pytest.approx(10.0, rel=0.02)   # variance ~ 1 / photons
    assert bright["trace_mm2"] >= bright["trace_known_mm2"]
    assert 0.01 < math.sqrt(bright["trace_mm2"]) < 0.3                               # sub-pixel, order 0.1 mm
