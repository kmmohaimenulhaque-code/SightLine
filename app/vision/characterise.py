"""Image characterisation of the target as it appears in a frame — the quantities compared between synthetic and
real data in E-003 (edge blur, sharpening halo, levels, temporal noise, compression blocking).

All functions take *linear-light* images unless stated. They describe an image; they do not judge it. Whether a
synthetic/real difference matters is decided against the measurement objective, not here.

Limits: the ring lines sit 8 mm either side of the black's edge (about 2.3 px at 3.45 mm/px), so at low resolution
their blurred dips overlap the edge profile; halo and plateau figures are then indicative only.
"""

from __future__ import annotations

import math

import numpy as np

GAUSS_10_90 = 2.0 * 1.2815515655446004   # 10-90 % width of a Gaussian-blurred edge, in units of sigma


def radial_profile(lin: np.ndarray, cx: float, cy: float, a: float, b: float, theta: float,
                   r_max_factor: float = 1.9, bin_px: float = 0.2) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mean level against equivalent-circle radius (pixels), over-sampled: every pixel contributes at its own
    sub-pixel radius. Returns ``(radius_px, mean_level, pixel_count)`` for non-empty bins."""
    r = math.sqrt(a * b)
    h, w = lin.shape
    half = int(math.ceil(r_max_factor * a)) + 2
    x0, x1, y0, y1 = max(0, int(cx) - half), min(w, int(cx) + half + 1), max(0, int(cy) - half), min(h, int(cy) + half + 1)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    dx, dy = xx - cx, yy - cy
    c, s = math.cos(theta), math.sin(theta)
    dn = np.hypot((dx * c + dy * s) * (r / a), (-dx * s + dy * c) * (r / b))
    keep = dn <= r_max_factor * r
    idx = np.floor(dn[keep] / bin_px).astype(int)
    vals = lin[y0:y1, x0:x1][keep]
    count = np.bincount(idx)
    total = np.bincount(idx, weights=vals)
    ok = count > 0
    return (np.arange(len(count))[ok] + 0.5) * bin_px, total[ok] / count[ok], count[ok]


def edge_metrics(radius: np.ndarray, level: np.ndarray, r_px: float) -> dict:
    """Plateau levels, 10-90 % edge width (and the equivalent Gaussian sigma), halo over/undershoot as a fraction of
    the black-white contrast, from a radial profile of the black aiming mark of flux radius ``r_px``."""
    radius, level = np.asarray(radius, float), np.asarray(level, float)
    black = float(np.median(level[(radius > 0.2 * r_px) & (radius < 0.6 * r_px)]))
    white = float(np.median(level[(radius > 1.45 * r_px) & (radius < 1.85 * r_px)]))
    contrast = white - black
    if contrast <= 0:
        raise ValueError("no contrast in the profile")
    norm = (level - black) / contrast
    band = (radius > 0.6 * r_px) & (radius < 1.4 * r_px)
    rb, nb = radius[band], norm[band]

    def crossing(q: float) -> float:
        k = np.flatnonzero((nb[:-1] < q) & (nb[1:] >= q))
        if k.size == 0:
            return float("nan")
        i = k[np.argmin(np.abs(rb[k] - r_px))]
        return float(rb[i] + (q - nb[i]) / (nb[i + 1] - nb[i]) * (rb[i + 1] - rb[i]))

    width = crossing(0.9) - crossing(0.1)
    outer = norm[(radius > r_px) & (radius < 1.25 * r_px)]
    inner = norm[(radius > 0.75 * r_px) & (radius < r_px)]
    return {"black_level": black, "white_level": white, "contrast_ratio": white / max(black, 1e-9),
            "edge_10_90_px": width, "edge_sigma_px": width / GAUSS_10_90,
            "edge_50_radius_px": crossing(0.5),
            "overshoot_fraction": float(max(outer.max() - 1.0, 0.0)) if outer.size else float("nan"),
            "undershoot_fraction": float(max(-inner.min(), 0.0)) if inner.size else float("nan")}


def temporal_noise(stack: np.ndarray, cx: float, cy: float, r_px: float) -> dict:
    """Per-pixel temporal noise of a static stack (N, h, w), averaged over the white surround and the black core,
    relative to the white level; and the lag-1 temporal correlation of the white-region noise (near 0 for an
    untouched sensor; positive when a temporal denoiser or an inter-frame codec carries content between frames)."""
    stack = np.asarray(stack, float)
    if stack.shape[0] < 8:
        raise ValueError("need at least 8 frames")
    yy, xx = np.mgrid[0:stack.shape[1], 0:stack.shape[2]].astype(float)
    d = np.hypot(xx - cx, yy - cy)
    white, black = (d > 1.4 * r_px) & (d < 1.85 * r_px), d < 0.6 * r_px
    resid = stack - stack.mean(axis=0)
    std = resid.std(axis=0, ddof=1)
    w = resid[:, white]
    num, den = (w[1:] * w[:-1]).sum(axis=0), (w * w).sum(axis=0)
    level = float(stack.mean(axis=0)[white].mean())
    return {"white_level": level, "white_noise_rel": float(std[white].mean() / level),
            "black_noise_rel": float(std[black].mean() / level),
            "white_lag1_correlation": float(np.mean(num[den > 0] / den[den > 0])), "n_frames": int(stack.shape[0])}


def blockiness(gray: np.ndarray, block: int = 8) -> float:
    """Ratio of the mean absolute pixel difference across ``block``-aligned boundaries to that elsewhere (rows and
    columns averaged). About 1.0 without block artefacts. A coarse indicator only: modern codecs use variable block
    sizes and in-loop deblocking."""
    g = np.asarray(gray, float)
    dh, dv = np.abs(np.diff(g, axis=1)), np.abs(np.diff(g, axis=0))
    ch, cv = (np.arange(dh.shape[1]) + 1) % block == 0, (np.arange(dv.shape[0]) + 1) % block == 0
    ratios = []
    for d, sel, axis in ((dh, ch, 0), (dv, cv, 1)):
        m = d.mean(axis=axis)
        if m[~sel].mean() > 0:
            ratios.append(m[sel].mean() / m[~sel].mean())
    return float(np.mean(ratios)) if ratios else float("nan")
