"""Gyroscope log loading and raw characterisation (CAL-EXP-6 analysis code, checked on simulated logs)."""

import math

import numpy as np
import pytest

from app.imu.gyro import allan_deviation, allan_summary, dominant_axis, load_gyro_csv, sampling_report, static_report


def _write(path, header, t, omega, extra=None):
    with open(path, "w") as f:
        f.write(",".join(header) + "\n")
        for i in range(len(t)):
            row = [repr(float(t[i]))] + [repr(float(v)) for v in omega[i]] + ([repr(float(extra[i]))] if extra is not None else [])
            f.write(",".join(row) + "\n")


def _static_log(rng, rate=100.0, seconds=120.0, density=1e-4, bias=(0.004, -0.002, 0.001)):
    n = int(rate * seconds)
    sigma = density * math.sqrt(rate / 2.0)
    return np.arange(n) / rate, rng.normal(0.0, sigma, (n, 3)) + np.asarray(bias)


def test_load_infers_columns_units_and_reports_the_mapping(tmp_path):
    rng = np.random.default_rng(0)
    t, w = _static_log(rng, seconds=5.0)
    p = tmp_path / "g.csv"
    _write(p, ["time", "seconds_elapsed", "z", "y", "x"],
           t * 1e9 + 1.7e18, np.column_stack([t, w[:, 2], w[:, 1]]), w[:, 0])
    log = load_gyro_csv(p)
    assert log.columns == {"time": "seconds_elapsed", "x": "x", "y": "y", "z": "z"}
    assert log.time_unit == "s"
    assert log.omega == pytest.approx(w)
    p2 = tmp_path / "g2.csv"
    _write(p2, ["timestamp_ns", "gyroRotationX(deg/s)", "gyroRotationY(deg/s)", "gyroRotationZ(deg/s)"],
           t * 1e9, np.degrees(w))
    log2 = load_gyro_csv(p2, rate_unit="deg/s")
    assert log2.time_unit == "ns" and log2.omega == pytest.approx(w)
    assert log2.t[-1] == pytest.approx(t[-1])


def test_load_rejects_what_it_cannot_interpret(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b,c,d\n0,1,2,3\n1,1,2,3\n2,1,2,3\n")
    with pytest.raises(ValueError, match="cannot identify"):
        load_gyro_csv(p)
    p.write_text("time,x,y,z\n0,1,2,3\n0,1,2,3\n1,1,2,3\n")
    with pytest.raises(ValueError, match="strictly increasing"):
        load_gyro_csv(p, time_unit="s")
    p.write_text("time,x,y,z\n0,1,2,3\n1,oops,2,3\n2,1,2,3\n")
    with pytest.raises(ValueError, match="non-numeric"):
        load_gyro_csv(p, time_unit="s")


def test_sampling_report_counts_gaps_and_jitter():
    t = np.arange(1000) / 100.0
    t = np.delete(t, [300, 301, 700])                       # two gaps
    rep = sampling_report(t)
    assert rep["rate_median_hz"] == pytest.approx(100.0)
    assert rep["gaps"] == 2 and rep["interval_max_s"] == pytest.approx(0.03)
    assert rep["interval_jitter_s"] > 0


def test_static_bias_noise_and_allan_random_walk(tmp_path):
    rng = np.random.default_rng(1)
    density = 1e-4                                          # rad/s/sqrt(Hz), simulated
    t, w = _static_log(rng, density=density)
    p = tmp_path / "static.csv"
    _write(p, ["seconds_elapsed", "x", "y", "z"], t, w)
    log = load_gyro_csv(p)
    rep = static_report(log)
    assert rep["bias_rad_s"] == pytest.approx([0.004, -0.002, 0.001], abs=2e-4)
    assert rep["noise_density_rad_s_sqrt_hz"] == pytest.approx([density] * 3, rel=0.05)
    taus, adev = allan_deviation(log.omega[:, 0], 100.0)
    assert taus.max() <= 12.0 + 1e-9                         # never beyond a tenth of the record
    summary = allan_summary(taus, adev)
    assert summary["angle_random_walk"] == pytest.approx(density / math.sqrt(2.0), rel=0.1)  # ADEV(1 s) for white noise
    assert summary["bias_instability"] is None               # pure white noise: no minimum inside the range


def test_allan_minimum_detects_a_bias_instability_floor():
    rng = np.random.default_rng(2)
    n, rate = 60000, 100.0
    drift = np.cumsum(rng.normal(0, 2e-6, n))               # rate random walk makes the curve turn up
    taus, adev = allan_deviation(rng.normal(0, 1e-3, n) + drift, rate)
    s = allan_summary(taus, adev)
    assert s["bias_instability"] is not None and 0.1 < s["tau_at_minimum_s"] < taus.max()


def test_dominant_axis_and_sign():
    omega = np.zeros((200, 3))
    omega[:, 1] = -0.3
    omega[:, 0] = 0.01
    assert dominant_axis(omega) == {"axis": "y", "energy_fraction": pytest.approx(0.9989, abs=1e-3), "mean_rate_sign": -1}
