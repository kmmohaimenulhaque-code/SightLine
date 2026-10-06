"""Gyroscope log loading and raw characterisation (experiment CAL-EXP-6). No filtering, no fusion.

Measured from a log: sample rate, timestamp-interval statistics and jitter, dropped samples; from a *static* log:
bias, noise, white-noise density, Allan deviation (angle random walk, bias instability). Results describe the device
and logging app that produced the file — nothing here is a specification value.

Logging-app CSV layouts differ and were not verified against any specific app in this repository: the loader matches
column names heuristically and returns the mapping it used. Pass the columns explicitly if the mapping is wrong.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_TIME_HINTS = ("seconds_elapsed", "elapsed", "timestamp", "time")
_UNIT_SCALE = {"s": 1.0, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}


@dataclass(frozen=True)
class GyroLog:
    t: np.ndarray                 # seconds, starting at 0, strictly increasing
    omega: np.ndarray             # (N, 3) rad/s, device axes x, y, z as logged
    columns: dict                 # mapping used: {"time": name, "x": name, "y": name, "z": name}
    time_unit: str
    rate_unit: str
    temperature: np.ndarray | None = None


def _pick_axis(names: list[str], axis: str) -> str | None:
    low = {n: n.lower() for n in names}
    exact = [n for n in names if low[n] == axis]
    if exact:
        return exact[0]
    scored = []
    for n in names:
        l = low[n]
        if "gyro" in l or "rotation" in l or "angular" in l or "omega" in l:
            tokens = l.replace("(", " ").replace(")", " ").replace("_", " ").replace("-", " ").split()
            if axis in tokens or l.rstrip(" )").endswith(axis) or f"{axis}(" in l.replace(" ", ""):
                scored.append(n)
    return scored[0] if scored else None


def load_gyro_csv(path: str | Path, time_col: str | None = None, x_col: str | None = None, y_col: str | None = None,
                  z_col: str | None = None, time_unit: str | None = None, rate_unit: str = "rad/s",
                  temperature_col: str | None = None) -> GyroLog:
    """Load a gyroscope CSV. ``time_unit`` in {s, ms, us, ns}; if omitted it is inferred from the median interval
    (assuming a 20-2000 Hz sensor). ``rate_unit`` in {rad/s, deg/s}. Rows with non-numeric fields are rejected, not
    skipped silently."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        delim = max(",;\t", key=sample.count)
        rows = list(csv.reader(f, delimiter=delim))
    if len(rows) < 3:
        raise ValueError("gyro log has no data")
    names = [c.strip().strip('"') for c in rows[0]]
    if time_col is None:
        for hint in _TIME_HINTS:
            hits = [n for n in names if hint in n.lower()]
            if hits:
                time_col = hits[0]
                break
    cols = {"time": time_col, "x": x_col or _pick_axis(names, "x"), "y": y_col or _pick_axis(names, "y"),
            "z": z_col or _pick_axis(names, "z")}
    missing = [k for k, v in cols.items() if v is None or v not in names]
    if missing:
        raise ValueError(f"cannot identify column(s) {missing} in header {names}; pass them explicitly")
    ix = [names.index(cols[k]) for k in ("time", "x", "y", "z")]
    it = names.index(temperature_col) if temperature_col else None
    try:
        data = np.array([[float(r[i]) for i in ix] for r in rows[1:] if r and any(c.strip() for c in r)])
        temp = np.array([float(r[it]) for r in rows[1:] if r and any(c.strip() for c in r)]) if it is not None else None
    except (ValueError, IndexError) as exc:
        raise ValueError(f"non-numeric or short row in {path}: {exc}") from exc
    t_raw = data[:, 0]
    dt = np.diff(t_raw)
    if np.any(dt <= 0):
        raise ValueError("timestamps are not strictly increasing")
    if time_unit is None:
        med = float(np.median(dt))
        candidates = [u for u, k in _UNIT_SCALE.items() if 5e-4 <= med * k <= 5e-2]
        if len(candidates) != 1:
            raise ValueError("cannot infer the time unit; pass time_unit explicitly")
        time_unit = candidates[0]
    if rate_unit not in ("rad/s", "deg/s"):
        raise ValueError("rate_unit must be rad/s or deg/s")
    scale = math.pi / 180.0 if rate_unit == "deg/s" else 1.0
    t = (t_raw - t_raw[0]) * _UNIT_SCALE[time_unit]
    return GyroLog(t, data[:, 1:4] * scale, cols, time_unit, rate_unit, temp)


def sampling_report(t: np.ndarray) -> dict:
    """Sample rate and timestamp-interval statistics. ``gaps`` counts intervals longer than 1.5x the median."""
    dt = np.diff(np.asarray(t, float))
    med = float(np.median(dt))
    return {"n": int(len(t)), "duration_s": float(t[-1] - t[0]), "rate_median_hz": 1.0 / med,
            "rate_mean_hz": float(len(dt) / (t[-1] - t[0])), "interval_median_s": med,
            "interval_min_s": float(dt.min()), "interval_max_s": float(dt.max()),
            "interval_jitter_s": float(dt.std()), "gaps": int(np.sum(dt > 1.5 * med))}


def static_report(log: GyroLog) -> dict:
    """Bias (mean rate) and noise (standard deviation) per axis of a log recorded with the device at rest.
    ``noise_density`` assumes white noise over the full Nyquist band (sigma / sqrt(rate / 2)); a sensor's internal
    low-pass filter makes the true in-band density higher, so treat it as a lower estimate (DERIVED)."""
    rate = sampling_report(log.t)["rate_median_hz"]
    bias, sigma = log.omega.mean(axis=0), log.omega.std(axis=0, ddof=1)
    out = {"bias_rad_s": bias.tolist(), "noise_sigma_rad_s": sigma.tolist(),
           "noise_density_rad_s_sqrt_hz": (sigma / math.sqrt(rate / 2.0)).tolist(),
           "bias_deg_s": np.degrees(bias).tolist(), "noise_sigma_deg_s": np.degrees(sigma).tolist()}
    if log.temperature is not None:
        out["temperature_mean"] = float(log.temperature.mean())
        out["temperature_range"] = float(np.ptp(log.temperature))
    return out


def allan_deviation(rate_signal: np.ndarray, sample_rate_hz: float, taus_s: np.ndarray | None = None,
                    ) -> tuple[np.ndarray, np.ndarray]:
    """Overlapping Allan deviation of one axis of rate data. Returns ``(taus_s, adev)`` in the input's units.
    Averaging times longer than a tenth of the record are not evaluated (too few independent clusters)."""
    y = np.asarray(rate_signal, float)
    n, tau0 = len(y), 1.0 / sample_rate_hz
    if n < 16:
        raise ValueError("record too short")
    max_m = n // 10
    if taus_s is None:
        m = np.unique(np.round(np.logspace(0, math.log10(max(max_m, 1)), 40)).astype(int))
    else:
        m = np.unique(np.round(np.asarray(taus_s, float) / tau0).astype(int))
    m = m[(m >= 1) & (m <= max_m)]
    theta = np.concatenate([[0.0], np.cumsum(y)]) * tau0
    taus, adev = [], []
    for k in m:
        d = theta[2 * k:] - 2.0 * theta[k:-k] + theta[:-2 * k]
        if len(d) < 2:
            continue
        taus.append(k * tau0)
        adev.append(math.sqrt(float((d * d).mean()) / (2.0 * (k * tau0) ** 2)))
    return np.asarray(taus), np.asarray(adev)


def allan_summary(taus_s: np.ndarray, adev: np.ndarray) -> dict:
    """Angle random walk coefficient N (ADEV = N / sqrt(tau), i.e. the ADEV read at tau = 1 s off the -1/2 slope
    fitted to the shortest decade) and bias instability (minimum ADEV / 0.664). For ideal white noise N equals the
    one-sided noise density of ``static_report`` divided by sqrt(2) (DERIVED; checked in tests). Values are None where
    the record does not support the estimate (the minimum sits at the longest tau: record too short)."""
    taus_s, adev = np.asarray(taus_s, float), np.asarray(adev, float)
    out = {"angle_random_walk": None, "bias_instability": None, "tau_at_minimum_s": None,
           "tau_max_s": float(taus_s.max()) if len(taus_s) else None}
    short = taus_s <= 10.0 * taus_s.min() if len(taus_s) else np.zeros(0, bool)
    if short.sum() >= 3:
        out["angle_random_walk"] = float(np.exp(np.mean(np.log(adev[short]) + 0.5 * np.log(taus_s[short]))))
    if len(adev) >= 3:
        k = int(np.argmin(adev))
        if k < len(adev) - 1:
            out["bias_instability"] = float(adev[k] / 0.664)
            out["tau_at_minimum_s"] = float(taus_s[k])
    return out


def dominant_axis(omega: np.ndarray) -> dict:
    """Which device axis carries a deliberate rotation, and its sign (net rotation angle per axis over the segment).
    Used to establish the axis convention: rotate the phone about one known physical axis in a known sense."""
    omega = np.asarray(omega, float).reshape(-1, 3)
    energy = (omega**2).sum(axis=0)
    k = int(np.argmax(energy))
    return {"axis": "xyz"[k], "energy_fraction": float(energy[k] / energy.sum()) if energy.sum() > 0 else 0.0,
            "mean_rate_sign": int(np.sign(omega[:, k].mean()))}
