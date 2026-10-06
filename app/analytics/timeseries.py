"""Deterministic time-series analysis of a tracked image position (and of gyroscope logs).

Used by the camera experiments (E-002 static repeatability, E-004a response to known rotation) and reusable later for
hold analytics. Pure NumPy. Positions are in pixels unless stated; times in seconds.

Contents
* ``static_stats``     — mean, standard deviation, RMS, p95 / maximum displacement, drift.
* ``amplitude_spectrum`` — one-sided amplitude spectrum of a uniformly sampled series.
* ``find_plateaus`` / ``step_table`` — segment a step sequence into still intervals and compare each step with the
  expected displacement (response ratio with uncertainty, in-plateau creep = re-centring indicator).
* ``gyro_referenced_gain`` — |H(f)| of image motion against an independent gyroscope, per frequency band.
"""

from __future__ import annotations

import math

import numpy as np


# ----------------------------------------------------------------------------------------------------------------------
# Static statistics
# ----------------------------------------------------------------------------------------------------------------------
def static_stats(t: np.ndarray, xy: np.ndarray, edge_s: float = 1.0) -> dict:
    """Statistics of a nominally still target. Displacements are radial distances from the mean position.

    ``drift``: least-squares slope per axis (px/s) and the displacement between the mean of the first and the last
    ``edge_s`` seconds. ``rms_px`` is the RMS radial displacement (sqrt of the summed per-axis variances).
    """
    t, xy = np.asarray(t, float), np.asarray(xy, float).reshape(-1, 2)
    if len(t) < 3:
        raise ValueError("need at least 3 samples")
    mean = xy.mean(axis=0)
    dev = xy - mean
    radial = np.hypot(dev[:, 0], dev[:, 1])
    tc = t - t.mean()
    slope = (tc[:, None] * dev).sum(axis=0) / float((tc * tc).sum())
    first, last = t <= t[0] + edge_s, t >= t[-1] - edge_s
    end_shift = xy[last].mean(axis=0) - xy[first].mean(axis=0)
    detr = dev - tc[:, None] * slope
    step = np.hypot(*np.diff(xy, axis=0).T)
    return {
        # Share of frame-to-frame position changes below 0.001 px. Sensor noise never repeats that closely; a large
        # share means the encoder is repeating picture content (inter-frame "skip"), so the scatter is understated.
        "frozen_step_fraction": float(np.mean(step < 1e-3)),
        "n": int(len(t)), "duration_s": float(t[-1] - t[0]),
        "mean_x_px": float(mean[0]), "mean_y_px": float(mean[1]),
        "std_x_px": float(dev[:, 0].std(ddof=1)), "std_y_px": float(dev[:, 1].std(ddof=1)),
        "rms_px": float(math.sqrt((radial**2).mean())),
        "p95_px": float(np.percentile(radial, 95)), "max_px": float(radial.max()),
        "drift_x_px_per_s": float(slope[0]), "drift_y_px_per_s": float(slope[1]),
        "end_shift_x_px": float(end_shift[0]), "end_shift_y_px": float(end_shift[1]),
        "detrended_rms_px": float(math.sqrt((detr**2).sum(axis=1).mean())),
    }


def sampling_rate(t: np.ndarray) -> tuple[float, float]:
    """``(rate_hz, interval_jitter_s)`` from timestamps: 1 / median interval, and the standard deviation of intervals."""
    dt = np.diff(np.asarray(t, float))
    if len(dt) < 2 or np.median(dt) <= 0:
        raise ValueError("timestamps must be increasing with at least 3 samples")
    return 1.0 / float(np.median(dt)), float(dt.std())


def longest_contiguous(idx: np.ndarray) -> slice:
    """Slice (into the valid-frame arrays) of the longest run of consecutive frame indices — used so that spectral
    analysis never spans a gap left by invalid frames."""
    idx = np.asarray(idx)
    if len(idx) == 0:
        return slice(0, 0)
    breaks = np.flatnonzero(np.diff(idx) != 1)
    starts = np.concatenate([[0], breaks + 1])
    ends = np.concatenate([breaks + 1, [len(idx)]])
    k = int(np.argmax(ends - starts))
    return slice(int(starts[k]), int(ends[k]))


def amplitude_spectrum(x: np.ndarray, rate_hz: float) -> tuple[np.ndarray, np.ndarray]:
    """One-sided amplitude spectrum of a uniformly sampled, linearly detrended series (Hann window, amplitude-
    corrected: a sinusoid of amplitude A at a bin centre reads A)."""
    x = np.asarray(x, float)
    n = len(x)
    if n < 8:
        raise ValueError("need at least 8 samples")
    k = np.arange(n)
    x = x - np.polyval(np.polyfit(k, x, 1), k)
    w = np.hanning(n)
    spec = np.abs(np.fft.rfft(x * w)) * 2.0 / w.sum()
    return np.fft.rfftfreq(n, 1.0 / rate_hz), spec


# ----------------------------------------------------------------------------------------------------------------------
# Step sequences
# ----------------------------------------------------------------------------------------------------------------------
def find_plateaus(t: np.ndarray, xy: np.ndarray, min_duration_s: float = 1.0, window_s: float = 0.3,
                  threshold_px: float | None = None, floor_px: float = 0.02) -> list[tuple[int, int]]:
    """Index ranges ``[i0, i1)`` during which the position is still.

    Stillness = rolling standard deviation (radial, window ``window_s``) below ``threshold_px``. By default the
    threshold is 4x the 10th percentile of the rolling values (the quietest tenth of the record sets the noise floor),
    but never below ``floor_px``. Callers that know the smallest step they expect should raise ``floor_px`` to a
    fraction of it, so that sub-step glitches (e.g. a codec refresh) do not split a plateau. A slow creep inside a
    plateau does not break it; it is reported by ``step_table``.
    """
    t, xy = np.asarray(t, float), np.asarray(xy, float).reshape(-1, 2)
    n = len(t)
    rate, _ = sampling_rate(t)
    w = max(3, int(round(window_s * rate)))
    if n < 2 * w:
        return []
    c1 = np.cumsum(np.vstack([np.zeros((1, 2)), xy]), axis=0)
    c2 = np.cumsum(np.vstack([np.zeros((1, 2)), xy * xy]), axis=0)
    m = (c1[w:] - c1[:-w]) / w
    var = np.clip((c2[w:] - c2[:-w]) / w - m * m, 0.0, None).sum(axis=1)
    roll = np.sqrt(var)                                   # value for the window starting at each index
    thr = threshold_px if threshold_px is not None else max(4.0 * float(np.percentile(roll, 10)), floor_px)
    still = np.zeros(n, dtype=bool)
    for i in np.flatnonzero(roll < thr):
        still[i:i + w] = True
    out, i = [], 0
    while i < n:
        if still[i]:
            j = i
            while j < n and still[j]:
                j += 1
            if t[j - 1] - t[i] >= min_duration_s:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out


def _block_sem(v: np.ndarray, blocks: int = 5) -> np.ndarray:
    """Standard error of the mean from block means (frames are correlated, so sigma / sqrt(n) would be optimistic)."""
    b = min(blocks, len(v) // 2)
    if b < 2:
        return np.full(v.shape[1], float("nan"))
    means = np.array([part.mean(axis=0) for part in np.array_split(v, b)])
    return means.std(axis=0, ddof=1) / math.sqrt(b)


def step_table(t: np.ndarray, xy: np.ndarray, plateaus: list[tuple[int, int]], expected_px: list[float],
               expected_sigma_px: list[float] | None = None, edge_s: float = 0.5) -> dict:
    """Compare each plateau's displacement from the first plateau with the expected displacement.

    ``expected_px[k]`` is the expected image displacement of plateau k relative to plateau 0 (so ``expected_px[0]``
    is 0). The motion axis is the unit vector toward the plateau with the largest |expected| displacement, signed so
    that this plateau's observed displacement has the sign of its expectation. The direction therefore carries no
    information, only magnitudes do. ``creep_px`` is the along-axis change between the first and last ``edge_s`` seconds of
    a plateau — a stabiliser that re-centres shows up as creep toward the expected position.
    """
    t, xy = np.asarray(t, float), np.asarray(xy, float).reshape(-1, 2)
    if len(plateaus) != len(expected_px):
        raise ValueError(f"found {len(plateaus)} plateaus but {len(expected_px)} were expected")
    if len(plateaus) < 2:
        raise ValueError("need a baseline plateau and at least one step")
    sig = list(expected_sigma_px) if expected_sigma_px is not None else [0.0] * len(expected_px)
    means = np.array([xy[i0:i1].mean(axis=0) for i0, i1 in plateaus])
    sems = np.array([_block_sem(xy[i0:i1]) for i0, i1 in plateaus])
    k_ref = int(np.argmax(np.abs(expected_px)))
    v = means[k_ref] - means[0]
    norm = float(np.hypot(*v))
    if norm == 0.0 or expected_px[k_ref] == 0.0:
        raise ValueError("no displacement between plateaus")
    axis = v / norm * math.copysign(1.0, expected_px[k_ref])
    perp = np.array([-axis[1], axis[0]])
    rows = []
    for k, (i0, i1) in enumerate(plateaus):
        d = means[k] - means[0]
        obs, off = float(d @ axis), float(d @ perp)
        along = np.nan_to_num(sems) @ np.abs(axis)            # conservative along-axis standard error per plateau
        obs_sigma = float(math.hypot(along[k], along[0])) if k else 0.0
        seg_t, seg = t[i0:i1], xy[i0:i1] @ axis
        head, tail = seg[seg_t <= seg_t[0] + edge_s], seg[seg_t >= seg_t[-1] - edge_s]
        row = {"plateau": k, "t_start_s": float(seg_t[0]), "t_end_s": float(seg_t[-1]), "n": int(i1 - i0),
               "expected_px": float(expected_px[k]), "expected_sigma_px": float(sig[k]),
               "observed_px": obs, "observed_sigma_px": obs_sigma, "off_axis_px": off,
               "scatter_px": float(np.hypot(*xy[i0:i1].std(axis=0, ddof=1))),
               "creep_px": float(tail.mean() - head.mean())}
        if expected_px[k] != 0.0:
            ratio = obs / expected_px[k]
            row["response_ratio"] = ratio
            row["response_ratio_sigma"] = abs(ratio) * math.hypot(obs_sigma / abs(obs) if obs else math.inf,
                                                                 sig[k] / abs(expected_px[k]))
        rows.append(row)
    return {"axis_unit": [float(axis[0]), float(axis[1])], "rows": rows}


# ----------------------------------------------------------------------------------------------------------------------
# Gyro-referenced gain
# ----------------------------------------------------------------------------------------------------------------------
def _bandpass(x: np.ndarray, rate_hz: float, lo: float, hi: float) -> np.ndarray:
    """Zero-phase FFT band-pass along axis 0 (linear detrend, 10 % cosine taper)."""
    x = np.asarray(x, float)
    n = x.shape[0]
    k = np.arange(n)
    flat = x.reshape(n, -1)
    A = np.column_stack([k, np.ones(n)])
    flat = flat - A @ np.linalg.lstsq(A, flat, rcond=None)[0]
    m = max(1, n // 10)
    taper = np.ones(n)
    ramp = 0.5 * (1 - np.cos(np.pi * (np.arange(m) + 0.5) / m))
    taper[:m], taper[-m:] = ramp, ramp[::-1]
    spec = np.fft.rfft(flat * taper[:, None], axis=0)
    f = np.fft.rfftfreq(n, 1.0 / rate_hz)
    spec[(f < lo) | (f > hi)] = 0.0
    return np.fft.irfft(spec, n=n, axis=0).reshape(x.shape)


def _hilbert(x: np.ndarray) -> np.ndarray:
    """Quadrature (90 degree shifted) copy of a real series."""
    n = len(x)
    spec = np.fft.fft(x)
    h = np.zeros(n)
    h[0] = 1.0
    if n % 2 == 0:
        h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[1:(n + 1) // 2] = 2.0
    return np.imag(np.fft.ifft(spec * h))


def integrate_rate(t: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """Trapezoidal integral of angular rate (rad/s) to angle (rad), per axis, after removing the mean rate (bias).
    Small-angle treatment: axes are integrated independently (valid for the few-mrad motions studied here)."""
    t, omega = np.asarray(t, float), np.asarray(omega, float)
    w = omega - omega.mean(axis=0)
    dt = np.diff(t)[:, None]
    return np.vstack([np.zeros((1, omega.shape[1])), np.cumsum(0.5 * (w[1:] + w[:-1]) * dt, axis=0)])


def _exposure_average(t: np.ndarray, angle: np.ndarray, exposure_s: float) -> np.ndarray:
    """Boxcar average of ``angle`` over a centred window of ``exposure_s`` (models the camera's exposure)."""
    if exposure_s <= 0.0:
        return angle
    cum = np.vstack([np.zeros((1, angle.shape[1])),
                     np.cumsum(0.5 * (angle[1:] + angle[:-1]) * np.diff(t)[:, None], axis=0)])
    lo, hi = t - exposure_s / 2.0, t + exposure_s / 2.0
    out = np.empty_like(angle)
    for a in range(angle.shape[1]):
        out[:, a] = (np.interp(hi, t, cum[:, a]) - np.interp(lo, t, cum[:, a])) / exposure_s
    return out


def gyro_referenced_gain(
    t_img: np.ndarray, angle_img: np.ndarray, t_gyro: np.ndarray, omega: np.ndarray,
    bands: tuple[tuple[float, float], ...] = ((0.5, 2.0), (2.0, 5.0), (5.0, 10.0), (10.0, 14.0)),
    exposure_s: float = 0.0, min_excitation_rad: float = 5e-5,
) -> dict:
    """Magnitude of the image-motion response to rotation measured by an independent gyroscope.

    ``angle_img`` (N, 2): image position converted to angle, (x - mean) / f_px, at frame times ``t_img``.
    ``omega`` (M, 3): angular rate in rad/s at ``t_gyro``, from a gyroscope rigidly fixed to the camera (any
    orientation: a rigid body has one angular velocity). The two clocks may have an arbitrary offset; it is estimated by
    cross-correlation, so both records must contain the same motion (e.g. start with a few sharp taps).

    Per band: the gyro angle is exposure-averaged, sampled at the frame times and band-passed; its principal axis gives
    a scalar reference s(t). Both image components are regressed on s and on its quadrature copy, so the gain does not
    depend on residual delay: gain = sqrt(|a|^2 + |b|^2). A gain of 1 means the image follows the rotation; a gain
    well below 1 means something (a stabiliser) is cancelling it. Rotation about the optical axis produces no image
    translation — always run the same excitation on a non-stabilised control camera to confirm a gain near 1.

    Bands whose reference RMS is below ``min_excitation_rad`` or that extend beyond 0.45 x frame rate are returned
    with ``usable=False`` (no gain is claimed for them).
    """
    t_img, angle_img = np.asarray(t_img, float), np.asarray(angle_img, float).reshape(-1, 2)
    t_gyro, omega = np.asarray(t_gyro, float), np.asarray(omega, float).reshape(-1, 3)
    rate, jitter = sampling_rate(t_img)
    gyro_rate, _ = sampling_rate(t_gyro)
    theta = _exposure_average(t_gyro, integrate_rate(t_gyro, omega), exposure_s)
    n = len(t_img)
    tu = t_img[0] + np.arange(n) / rate                       # uniform frame grid
    img_u = np.column_stack([np.interp(tu, t_img, angle_img[:, a]) for a in range(2)])
    lo_all, hi_all = min(b[0] for b in bands), min(max(b[1] for b in bands), 0.45 * rate)

    # --- clock offset: coarse (cross-correlation on a common grid), then fine (1 ms steps, best broadband fit) -----
    ng = int(math.floor((t_gyro[-1] - t_gyro[0]) * rate)) + 1
    tg = t_gyro[0] + np.arange(ng) / rate
    th_u = np.column_stack([np.interp(tg, t_gyro, theta[:, a]) for a in range(3)])
    th_bp, img_bp = _bandpass(th_u, rate, lo_all, hi_all), _bandpass(img_u, rate, lo_all, hi_all)
    s = th_bp @ np.linalg.svd(th_bp, full_matrices=False)[2][0]
    y = img_bp @ np.linalg.svd(img_bp, full_matrices=False)[2][0]
    nfft = 1 << int(math.ceil(math.log2(len(s) + len(y))))
    xc = np.fft.irfft(np.fft.rfft(s, nfft) * np.conj(np.fft.rfft(y, nfft)), nfft)
    lag = int(np.argmax(np.abs(xc)))
    lag = lag - nfft if lag > nfft // 2 else lag               # s(t + lag) ~ y(t)
    coarse = (tg[0] - tu[0]) + lag / rate                      # t_gyro = t_img + offset

    def fit(offset: float, lo: float, hi: float) -> dict | None:
        ts = tu + offset
        keep = (ts >= t_gyro[0]) & (ts <= t_gyro[-1])
        if keep.sum() < max(16, int(2 * rate / lo)):           # at least two periods of the lowest frequency
            return None
        ref = np.column_stack([np.interp(ts[keep], t_gyro, theta[:, a]) for a in range(3)])
        ref_bp, im_bp = _bandpass(ref, rate, lo, hi), _bandpass(img_u[keep], rate, lo, hi)
        cut = max(1, keep.sum() // 20)                         # drop the tapered ends
        ref_bp, im_bp = ref_bp[cut:-cut], im_bp[cut:-cut]
        u, sv, vt = np.linalg.svd(ref_bp, full_matrices=False)
        sref = ref_bp @ vt[0]
        X = np.column_stack([sref, _hilbert(sref)])
        coef, *_ = np.linalg.lstsq(X, im_bp, rcond=None)
        resid = im_bp - X @ coef
        sst = float((im_bp**2).sum())
        direction = coef[0] / (np.linalg.norm(coef[0]) or 1.0)   # image response direction (in-phase part)
        return {"_series": (np.flatnonzero(keep)[cut:-cut], im_bp @ direction, sref),
                "gain": float(np.sqrt((coef**2).sum())), "r2": 1.0 - float((resid**2).sum()) / sst if sst > 0 else 0.0,
                "excitation_rms_rad": float(sref.std()), "image_rms_rad": float(np.sqrt((im_bp**2).sum(axis=1).mean())),
                "residual_rms_rad": float(np.sqrt((resid**2).sum(axis=1).mean())),
                "principal_axis_energy": float(sv[0] ** 2 / (sv**2).sum()), "n": int(len(sref))}

    best, best_off = None, coarse
    for d in np.arange(-1.5 / rate, 1.5 / rate + 1e-9, 1e-3):
        r = fit(coarse + d, lo_all, hi_all)
        if r is not None and (best is None or r["r2"] > best["r2"]):
            best, best_off = r, coarse + d
    series = best.pop("_series") if best is not None else None
    out = {"frame_rate_hz": rate, "frame_interval_jitter_s": jitter, "gyro_rate_hz": gyro_rate,
           "clock_offset_s": float(best_off), "broadband": best, "bands": [],
           # (frame positions, band-limited image angle along its response direction, band-limited reference angle)
           "series": series}
    for lo, hi in bands:
        row = {"f_lo_hz": lo, "f_hi_hz": hi, "usable": False}
        if hi <= 0.45 * rate:
            r = fit(best_off, lo, hi)
            if r is not None:
                r.pop("_series")
                row.update(r)
                row["usable"] = bool(r["excitation_rms_rad"] >= min_excitation_rad)
                if not row["usable"]:
                    row["reason"] = "insufficient excitation"
            else:
                row["reason"] = "record too short for this band"
        else:
            row["reason"] = "band exceeds 0.45 x frame rate"
        out["bands"].append(row)
    return out
