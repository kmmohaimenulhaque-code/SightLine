"""Time-series analysis used by the camera experiments (static stats, plateaus, gyro-referenced gain)."""

import math

import numpy as np
import pytest

from app.analytics.timeseries import (
    amplitude_spectrum,
    find_plateaus,
    gyro_referenced_gain,
    integrate_rate,
    longest_contiguous,
    static_stats,
    step_table,
)


def test_static_stats_on_known_noise_and_drift():
    rng = np.random.default_rng(1)
    t = np.arange(600) / 30.0
    xy = np.column_stack([100.0 + 0.01 * t + rng.normal(0, 0.03, 600), 50.0 + rng.normal(0, 0.04, 600)])
    s = static_stats(t, xy)
    assert s["std_y_px"] == pytest.approx(0.04, rel=0.1)
    assert s["drift_x_px_per_s"] == pytest.approx(0.01, abs=0.002)
    assert s["end_shift_x_px"] == pytest.approx(0.01 * 19.0, abs=0.03)
    assert s["detrended_rms_px"] == pytest.approx(0.05, rel=0.1)       # sqrt(0.03^2 + 0.04^2)
    assert s["rms_px"] >= s["detrended_rms_px"] and s["max_px"] >= s["p95_px"]


def test_amplitude_spectrum_reads_a_sinusoid_amplitude():
    rate, n = 60.0, 600
    t = np.arange(n) / rate
    f, a = amplitude_spectrum(0.2 * np.sin(2 * np.pi * 6.0 * t) + 0.5, rate)
    k = int(np.argmax(a))
    assert f[k] == pytest.approx(6.0, abs=rate / n)
    assert a[k] == pytest.approx(0.2, rel=0.02)


def test_longest_contiguous_run_skips_gaps():
    assert longest_contiguous(np.array([0, 1, 2, 5, 6, 7, 8, 9, 12])) == slice(3, 8)
    assert longest_contiguous(np.array([], dtype=int)) == slice(0, 0)


def _step_sequence(levels_px, rng, rate=30.0, hold_s=3.0, move_s=1.0, noise=0.02, creep=0.0):
    xs = [np.full(int(hold_s * rate), float(levels_px[0]))]
    for prev, lev in zip(levels_px[:-1], levels_px[1:]):
        n_move = int(move_s * rate)
        xs.append(np.linspace(prev, lev, n_move) + rng.normal(0, 0.6, n_move))           # disturbed transition
        hold = np.full(int(hold_s * rate), float(lev))
        if creep:
            hold = lev - creep * (lev - prev) * np.exp(-np.arange(len(hold)) / (0.8 * rate))  # creeps to the level
        xs.append(hold)
    x = np.concatenate(xs)
    t = np.arange(len(x)) / rate
    xy = np.column_stack([0.3 * x, x]) + rng.normal(0, noise, (len(x), 2))                # motion along a tilted axis
    return t, xy


def test_plateaus_and_response_ratio_recover_known_steps():
    rng = np.random.default_rng(2)
    true_gain = 0.8                                                                        # image shows 80 % of expected
    expected = [0.0, 0.72, 1.44, 2.89, 5.78]
    t, xy = _step_sequence([true_gain * e / math.hypot(1.0, 0.3) for e in expected], rng)
    plateaus = find_plateaus(t, xy)
    assert len(plateaus) == 5
    table = step_table(t, xy, plateaus, expected, [0.04 * e for e in expected])
    for row in table["rows"][1:]:
        assert row["response_ratio"] == pytest.approx(true_gain, abs=0.03)
        assert abs(row["off_axis_px"]) < 0.03
        assert row["response_ratio_sigma"] >= 0.04 * true_gain * 0.99                      # carries the expectation's sigma
    assert abs(table["rows"][0]["observed_px"]) < 1e-12


def test_creep_inside_a_plateau_is_reported():
    rng = np.random.default_rng(3)
    t, xy = _step_sequence([0.0, 3.0], rng, creep=0.6)
    table = step_table(t, xy, find_plateaus(t, xy, threshold_px=0.5), [0.0, 3.0 * math.hypot(1.0, 0.3)])
    assert table["rows"][1]["creep_px"] > 0.5                                              # moved toward the level


def test_step_table_refuses_a_plateau_count_mismatch():
    rng = np.random.default_rng(4)
    t, xy = _step_sequence([0.0, 1.0, 2.0], rng)
    with pytest.raises(ValueError, match="plateaus"):
        step_table(t, xy, find_plateaus(t, xy), [0.0, 1.0])


def _gyro_scenario(gain_by_band, rng, fps=60.0, gyro_rate=200.0, duration=30.0, offset=3.217, exposure=1 / 120):
    """Rigid rotation about a fixed axis made of tones in several bands; the image shows each tone scaled by a gain."""
    tg = np.arange(int(duration * gyro_rate)) / gyro_rate
    tones = [(0.9, 0.8e-3), (1.4, 0.5e-3), (3.1, 0.4e-3), (4.2, 0.3e-3), (6.3, 0.25e-3), (8.7, 0.2e-3)]
    axis = np.array([0.2, 0.95, 0.1])
    axis /= np.linalg.norm(axis)
    start = 0.5 * (1 + np.tanh((tg - 2.0) / 0.3))                                         # quiet start, then motion
    theta = sum(a * np.sin(2 * np.pi * f * tg + i) for i, (f, a) in enumerate(tones)) * start
    omega = np.gradient(theta, tg)[:, None] * axis[None, :] + rng.normal(0, 2e-4, (len(tg), 3)) + [0.01, -0.02, 0.005]
    ti = np.arange(int((duration - 6.0) * fps)) / fps                                     # video starts later
    def band_gain(f):
        return next(g for (lo, hi), g in gain_by_band.items() if lo <= f < hi)
    sinc = lambda f: np.sinc(f * exposure)
    env = 0.5 * (1 + np.tanh((ti + offset - 2.0) / 0.3))
    img = sum(band_gain(f) * sinc(f) * a * np.sin(2 * np.pi * f * (ti + offset) + i) for i, (f, a) in enumerate(tones))
    direction = np.array([0.1, 1.0]) / math.hypot(0.1, 1.0)
    angle_img = (img * env)[:, None] * direction[None, :] + rng.normal(0, 1e-5, (len(ti), 2))
    return ti, angle_img, tg, omega, offset


@pytest.mark.parametrize("gains", [
    {(0.5, 2.0): 1.0, (2.0, 5.0): 1.0, (5.0, 10.0): 1.0},                                 # no stabiliser
    {(0.5, 2.0): 0.9, (2.0, 5.0): 0.4, (5.0, 10.0): 0.1},                                 # high-frequency suppression
])
def test_gyro_referenced_gain_recovers_band_gains_and_clock_offset(gains):
    rng = np.random.default_rng(5)
    ti, angle_img, tg, omega, offset = _gyro_scenario(gains, rng)
    res = gyro_referenced_gain(ti, angle_img, tg, omega, bands=tuple(gains), exposure_s=1 / 120)
    assert res["clock_offset_s"] == pytest.approx(offset, abs=0.02)
    for row, (band, g) in zip(res["bands"], gains.items()):
        assert row["usable"]
        assert row["gain"] == pytest.approx(g, abs=0.05), band
        assert row["principal_axis_energy"] > 0.9


def test_gyro_gain_flags_bands_it_cannot_measure():
    rng = np.random.default_rng(6)
    ti, angle_img, tg, omega, _ = _gyro_scenario({(0.5, 2.0): 1.0, (2.0, 5.0): 1.0, (5.0, 10.0): 1.0}, rng)
    res = gyro_referenced_gain(ti, angle_img, tg, omega, bands=((0.5, 2.0), (10.0, 14.0), (14.0, 30.0)))
    assert res["bands"][0]["usable"]
    assert not res["bands"][1]["usable"] and res["bands"][1]["reason"] == "insufficient excitation"
    assert not res["bands"][2]["usable"] and "frame rate" in res["bands"][2]["reason"]


def test_integrate_rate_removes_bias():
    t = np.arange(1000) / 100.0
    omega = np.column_stack([0.05 + 0.1 * np.cos(2 * np.pi * t), np.full(1000, 0.02), np.zeros(1000)])
    ang = integrate_rate(t, omega)
    assert ang[:, 0] == pytest.approx(0.1 / (2 * np.pi) * np.sin(2 * np.pi * t), abs=2e-4)
    assert np.abs(ang[:, 1]).max() < 1e-12
