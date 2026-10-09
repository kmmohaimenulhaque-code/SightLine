"""Shared steps for analysing a recorded clip of the target: track, convert pixels to angle, write per-frame rows.

Used by E-002 (static repeatability) and E-004a (response to known rotation). The functions take the capture
``parameters`` and the provenance ``category`` explicitly so that the same code path runs on team-collected clips
and on synthetic sanity sequences — and so that the category decides the evidence class (``ml/evaluation/status.py``).
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import numpy as np

from app.analytics.timeseries import amplitude_spectrum, longest_contiguous, sampling_rate, static_stats
from app.calibration.angular import Measured, focal_px_from_target
from app.vision.motion import FrameRecord, track_frames, valid_arrays

MAX_INVALID_FRACTION = 0.05   # ASSUMED acceptance limit: more unusable frames than this invalidates a run


def track(frames: Iterable[tuple[int, float, np.ndarray]], gamma: float | None = 2.2,
          hint_px: tuple[float, float] | None = None) -> tuple[list[FrameRecord], dict]:
    records = track_frames(frames, gamma=gamma, hint_px=hint_px)
    bad = [r for r in records if not r.valid]
    info = {"n_frames": len(records), "n_invalid": len(bad),
            "invalid_fraction": len(bad) / len(records) if records else 1.0,
            "invalid_reasons": dict(Counter(r.reason for r in bad))}
    return records, info


def focal_length_px(records: list[FrameRecord], params: dict) -> dict:
    """Focal length in pixels for this capture mode.

    Preference: (1) ``params["intrinsics"]["f_px"]`` = {value, sigma, method} when the operator supplies a calibrated
    or platform-reported value; (2) measured from the target: major axis of the imaged black (unforeshortened
    diameter) x measured distance / measured black diameter. The marketing "equivalent" focal length is never used.
    """
    intr = params.get("intrinsics") or {}
    if isinstance(intr.get("f_px"), dict) and intr["f_px"].get("value"):
        m = Measured.of(intr["f_px"])
        return {"value": m.value, "sigma": m.sigma, "method": intr["f_px"].get("method", "supplied")}
    major = np.array([2.0 * r.radius_px * math.sqrt(r.semi_major_px / r.semi_minor_px)
                      for r in records if r.valid and r.semi_minor_px > 0 and math.isfinite(r.semi_major_px)])
    if len(major) < 3:
        raise ValueError("too few valid frames to measure the target size")
    med = float(np.median(major))
    sem = 1.4826 * float(np.median(np.abs(major - med))) / math.sqrt(len(major))
    f = focal_px_from_target(Measured(med, sem), Measured.of(params["target"]["black_diameter_mm"]),
                             Measured.of(params["distance_mm"]))
    return {"value": f.value, "sigma": f.sigma, "method": "target-anchored (measured black diameter and distance)",
            "black_major_axis_px": med, "mm_per_px_at_target": params["target"]["black_diameter_mm"]["value"] / med,
            "sigma_includes": ["frame scatter", "black diameter", "distance"],
            "sigma_excludes": ["estimator / ISP scale bias (UNVERIFIED on real video)"]}


def scope(params: dict) -> dict:
    """What a result applies to. Conclusions must never be stated more generally than this."""
    keys = ("device", "os_version", "camera", "zoom_readout", "capture_app", "resolution", "fps", "codec",
            "stabilisation_mode", "hdr", "focus", "exposure", "iso", "white_balance")
    return {k: params.get(k) for k in keys}


def frame_columns(params: dict) -> dict:
    res = params.get("resolution") or [None, None]
    return {"camera": params.get("camera"), "resolution": f"{res[0]}x{res[1]}", "fps": params.get("fps")}


def positions(records: list[FrameRecord], centre: str = "ellipse"):
    return valid_arrays(records, centre)


def static_analysis(records: list[FrameRecord], f_px: float, out_dir: str | Path, centre: str = "ellipse",
                    mm_per_px: float | None = None) -> tuple[dict, np.ndarray]:
    """Static repeatability of the target centre (E-002; E-004a test A): mean, standard deviation, RMS, p95, maximum,
    drift and spectrum, on the longest gap-free run of valid frames. Writes ``spectrum.csv``. Returns the result block
    and the mean position. Angles use ``f_px``; millimetres at the target use ``mm_per_px`` when given."""
    idx, t, xy = valid_arrays(records, centre)
    run = longest_contiguous(idx)
    stats = static_stats(t[run], xy[run])
    rate, jitter = sampling_rate(t[run])
    freqs, ax = amplitude_spectrum(xy[run][:, 0], rate)
    _, ay = amplitude_spectrum(xy[run][:, 1], rate)
    with open(Path(out_dir) / "spectrum.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["frequency_hz", "amplitude_x_px", "amplitude_y_px"])
        w.writerows([f"{a:.6g}", f"{b:.6g}", f"{c:.6g}"] for a, b, c in zip(freqs, ax, ay))
    k = int(np.argmax(np.hypot(ax, ay)[1:])) + 1
    cross = {}
    for c in ("ellipse", "moments", "centroid", "phase"):
        ci, ct, cxy = valid_arrays(records, c)
        if len(ct) >= 3:
            cross[c] = static_stats(ct, cxy)["rms_px"]
    result = {"static": stats, "frame_rate_hz": rate, "frame_interval_jitter_s": jitter,
              "rms_mrad": stats["rms_px"] / f_px * 1e3, "p95_mrad": stats["p95_px"] / f_px * 1e3,
              "max_mrad": stats["max_px"] / f_px * 1e3,
              "spectrum_peak": {"frequency_hz": float(freqs[k]), "amplitude_px": float(np.hypot(ax[k], ay[k]))},
              "rms_px_by_estimator": cross, "frames_used": int(run.stop - run.start)}
    if mm_per_px:
        result["at_target_mm"] = {k2: stats[k1] * mm_per_px for k1, k2 in
                                  (("std_x_px", "std_x"), ("std_y_px", "std_y"), ("rms_px", "rms"), ("p95_px", "p95"),
                                   ("max_px", "max"), ("detrended_rms_px", "detrended_rms"))}
        result["at_target_mm"]["mm_per_px"] = mm_per_px
    return result, np.array([stats["mean_x_px"], stats["mean_y_px"]])
