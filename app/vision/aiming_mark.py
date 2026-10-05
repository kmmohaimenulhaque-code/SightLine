"""Deterministic baseline: detect the ISSF black aiming mark and measure it to sub-pixel precision.

Pipeline (docs/computer-vision/BASELINE_PIPELINE.md):

1. ``linearize``      — undo the display gamma so intensities are proportional to light (flux conservation).
2. ``find_candidates`` — multi-threshold connected components; keep compact dark blobs whose surrounding annulus is
                         uniformly bright (black disc on a white card). Scale-free: no prior on target size.
3. ``refine_moments``  — iterative intensity-weighted centroid, blur-invariant "flux" radius and second moments.
4. ``refine_edges``    — sub-pixel 50 % crossings along radial rays + direct least-squares ellipse fit (robust).
5. ``measure``         — three estimators: "moments", "edges", and "hybrid" (centre from moments, shape from edges,
                         scale from flux).

The ring lines are not detected: at 10 m they are far below one pixel wide (ARCHITECTURE.md D-004).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from app.calibration.ellipse import Ellipse, algebraic_residuals, ellipse_from_covariance, fit_ellipse_direct
from app.calibration.rectify import apply_affine, ellipse_to_target_affine, local_mm_per_px
from app.scoring.issf import BLACK_RADIUS_MM, RING_RADII_MM, WHITE_LINE_RADII_MM, ShotScore, score_shot

DEFAULT_GAMMA = 2.2  # ASSUMPTION: phone output approximated by a power-law transfer (real ISPs differ — error term E11)
ASSUMED_RING_LINE_THICKNESS_MM = 0.15  # ASSUMPTION within the ISSF 0.1-0.2 mm range
METHODS = ("moments", "edges", "hybrid")

# The moments window is placed midway between the ring-6 and ring-5 lines (DERIVED): it then contains the whole black,
# its blur skirt and the complete black ring-6 line, and excludes ring 5. The expected "dark" content of that window
# is the black minus the white lines inside it (rings 8, 9, 10, inner ten) plus the ring-6 line.
_R6 = RING_RADII_MM[6]
_R5 = RING_RADII_MM[5]
MOMENTS_WINDOW_FACTOR = 0.5 * (_R6 + _R5) / BLACK_RADIUS_MM  # ~1.403 (in units of the black's radius)
_T = ASSUMED_RING_LINE_THICKNESS_MM
_area_disc = math.pi * BLACK_RADIUS_MM**2
_area_lines = 2.0 * math.pi * _T * (_R6 - sum(WHITE_LINE_RADII_MM))
DARK_AREA_FRACTION = (_area_disc + _area_lines) / _area_disc  # dark flux relative to a plain disc
_m2_disc = math.pi * BLACK_RADIUS_MM**4 / 2.0                  # integral of r^2 over the plain disc
_m2_lines = 2.0 * math.pi * _T * (_R6**3 - sum(r**3 for r in WHITE_LINE_RADII_MM))
# Ratio of the pattern's per-axis second moment to that of a plain disc (both normalised by their own flux).
SECOND_MOMENT_FACTOR = ((_m2_disc + _m2_lines) / (_area_disc + _area_lines)) / (_m2_disc / _area_disc)

# Black and white levels are estimated from a core disc and an annulus whose boundaries sit midway between printed
# lines, so every line is either fully inside or fully outside; the mean is then corrected for the known line area
# (a median is biased once the thin lines are blurred over many pixels).
_CORE_MM = 0.5 * (RING_RADII_MM[9] + RING_RADII_MM[8])            # 17.75 mm, between the ring-9 and ring-8 lines
_ANN_IN_MM = 0.5 * (_R6 + _R5)                                     # 41.75 mm, between ring 6 and ring 5
_ANN_OUT_MM = 0.5 * (RING_RADII_MM[4] + RING_RADII_MM[3])          # 57.75 mm, between ring 4 and ring 3
CORE_FACTOR = _CORE_MM / BLACK_RADIUS_MM
ANNULUS_FACTORS = (_ANN_IN_MM / BLACK_RADIUS_MM, _ANN_OUT_MM / BLACK_RADIUS_MM)
CORE_WHITE_FRACTION = sum(2.0 * r * _T for r in WHITE_LINE_RADII_MM if r < _CORE_MM) / _CORE_MM**2
ANNULUS_BLACK_FRACTION = (sum(2.0 * r * _T for r in RING_RADII_MM.values() if _ANN_IN_MM < r < _ANN_OUT_MM)
                          / (_ANN_OUT_MM**2 - _ANN_IN_MM**2))


# ----------------------------------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------------------------------
def linearize(image: np.ndarray, gamma: float | None = DEFAULT_GAMMA) -> np.ndarray:
    """Return a float32 image proportional to scene light. Integer images are scaled to [0, 1] first.
    ``gamma=None`` means the input is already linear."""
    img = np.asarray(image)
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if np.issubdtype(img.dtype, np.integer):
        img = img.astype(np.float32) / float(np.iinfo(img.dtype).max)
    else:
        img = img.astype(np.float32)
    if gamma is not None:
        img = np.power(np.clip(img, 0.0, 1.0), gamma, dtype=np.float32)
    return img


def bilinear(img: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    h, w = img.shape
    x = np.clip(x, 0.0, w - 1.000001)
    y = np.clip(y, 0.0, h - 1.000001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    dx = x - x0
    dy = y - y0
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    return (img[y0, x0] * (1 - dx) * (1 - dy) + img[y0, x1] * dx * (1 - dy)
            + img[y1, x0] * (1 - dx) * dy + img[y1, x1] * dx * dy)


def _window(img: np.ndarray, cx: float, cy: float, half: int):
    h, w = img.shape
    x0, x1 = max(0, int(math.floor(cx)) - half), min(w, int(math.floor(cx)) + half + 2)
    y0, y1 = max(0, int(math.floor(cy)) - half), min(h, int(math.floor(cy)) + half + 2)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    return img[y0:y1, x0:x1], xx.astype(np.float64), yy.astype(np.float64)


# ----------------------------------------------------------------------------------------------------------------------
# 1. Candidate detection
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Candidate:
    cx: float
    cy: float
    radius_px: float
    contrast: float
    bright_fraction: float
    score: float


def find_candidates(
    lin: np.ndarray,
    min_radius_px: float = 1.5,
    max_radius_px: float | None = None,
    levels: tuple[float, ...] = (0.30, 0.45, 0.60),
    max_candidates: int = 5,
) -> list[Candidate]:
    h, w = lin.shape
    if max_radius_px is None:
        max_radius_px = min(h, w) / 4.0
    smooth = cv2.GaussianBlur(lin, (0, 0), 0.8)
    lo, hi = np.percentile(smooth, [1.0, 99.5])
    span = float(hi - lo)
    if span < 1e-4:
        return []
    # Robust per-pixel noise estimate from horizontal neighbour differences (edges are sparse, so the MAD ignores them).
    diffs = np.diff(lin, axis=1).ravel()
    noise_sigma = 1.4826 * float(np.median(np.abs(diffs - np.median(diffs)))) / math.sqrt(2.0)
    found: list[Candidate] = []
    for f in levels:
        mask = (smooth < lo + f * span).astype(np.uint8)
        n, _, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, n):
            x, y, bw, bh, area = (int(v) for v in stats[i])
            if area < math.pi * min_radius_px**2 or area > math.pi * max_radius_px**2:
                continue
            if x == 0 or y == 0 or x + bw >= w or y + bh >= h:
                continue  # touches the border: incomplete
            if max(bw, bh) / max(1, min(bw, bh)) > 3.0:
                continue
            fill = area / (math.pi * bw * bh / 4.0)
            if not 0.70 <= fill <= 1.30:
                continue
            r = math.sqrt(area / math.pi)
            cx, cy = float(cents[i][0]), float(cents[i][1])
            sub, xx, yy = _window(lin, cx, cy, int(math.ceil(2.3 * r)) + 2)
            d = np.hypot(xx - cx, yy - cy)
            core = sub[d <= max(0.5 * r, 0.8)]
            ann = sub[(d >= 1.5 * r) & (d <= 2.2 * r)]
            if core.size == 0 or ann.size < 8:
                continue
            core_level, ann_level = float(np.median(core)), float(np.median(ann))
            contrast = ann_level - core_level
            # A printed black on a white card: contrast is a large fraction of the white level (true ratio > 10:1)
            # and far above the pixel noise. Noise blobs fail both tests.
            if contrast < 0.25 * span or contrast < 0.5 * ann_level or contrast < 8.0 * noise_sigma:
                continue
            bright = float(np.mean(ann > core_level + 0.5 * contrast))
            if bright < 0.85:
                continue
            score = contrast * bright * (1.0 - min(1.0, abs(1.0 - fill)))
            found.append(Candidate(cx, cy, r, contrast, bright, score))
    found.sort(key=lambda c: c.score, reverse=True)
    merged: list[Candidate] = []
    for c in found:
        if all(math.hypot(c.cx - m.cx, c.cy - m.cy) > 0.5 * max(c.radius_px, m.radius_px) for m in merged):
            merged.append(c)
        if len(merged) >= max_candidates:
            break
    return merged


# ----------------------------------------------------------------------------------------------------------------------
# 2. Moments (centroid, flux radius, second moments)
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class MomentsResult:
    cx: float
    cy: float
    cov: np.ndarray
    flux_radius_px: float
    black: float
    white: float
    ellipse: Ellipse
    blur_sigma_px: float


def _shape_from_moments(cov: np.ndarray, r: float):
    """Semi-axes, angle and blur from the weighted covariance and the flux radius (a * b = r^2).
    For the ISSF pattern the per-axis variance along a semi-axis s is SECOND_MOMENT_FACTOR * s^2 / 4 (plain disc:
    s^2 / 4); blur adds sigma^2 to both axes, so it cancels in the difference of the eigenvalues."""
    lam, vec = np.linalg.eigh(cov)
    k = SECOND_MOMENT_FACTOR / 4.0
    diff = max(lam[1] - lam[0], 0.0) / k  # a^2 - b^2
    prod = r * r
    a2 = 0.5 * (diff + math.sqrt(diff * diff + 4.0 * prod * prod))
    b2 = max(a2 - diff, 1e-12)
    sigma2 = max(lam[1] - k * a2, 0.0)
    major = vec[:, 1]
    return math.sqrt(a2), math.sqrt(b2), math.atan2(major[1], major[0]), math.sqrt(sigma2)


def refine_moments(lin: np.ndarray, cx: float, cy: float, r: float, iterations: int = 6) -> MomentsResult:
    """Iterative moments. Windows are defined in the *normalised* distance of the current ellipse estimate, so the
    core, the moments window and the annulus follow the projected ring geometry at any tilt."""
    a = b = r
    theta = 0.0
    black = white = float("nan")
    cov = np.eye(2)
    level_matrix = np.array([[1.0 - CORE_WHITE_FRACTION, CORE_WHITE_FRACTION],
                             [ANNULUS_BLACK_FRACTION, 1.0 - ANNULUS_BLACK_FRACTION]])
    for _ in range(iterations):
        sub, xx, yy = _window(lin, cx, cy, int(math.ceil(ANNULUS_FACTORS[1] * a)) + 3)
        dx0, dy0 = xx - cx, yy - cy
        c, s = math.cos(theta), math.sin(theta)
        dn = np.hypot((dx0 * c + dy0 * s) * (r / a), (-dx0 * s + dy0 * c) * (r / b))  # equivalent-circle distance
        core = sub[dn <= CORE_FACTOR * r]
        ann = sub[(dn >= ANNULUS_FACTORS[0] * r) & (dn <= ANNULUS_FACTORS[1] * r)]
        if ann.size < 8 or core.size < 1:
            raise RuntimeError("window too small for moments refinement")
        black, white = (float(v) for v in np.linalg.solve(level_matrix, [core.mean(), ann.mean()]))
        contrast = white - black
        if contrast <= 0:
            raise RuntimeError("no contrast")
        win = dn <= MOMENTS_WINDOW_FACTOR * r
        wts = np.minimum((white - sub[win]) / contrast, 1.5).astype(np.float64)  # negatives kept: unbiased noise
        total = wts.sum()
        if total <= 0:
            raise RuntimeError("no dark flux")
        mx = float((wts * xx[win]).sum() / total)
        my = float((wts * yy[win]).sum() / total)
        dx, dy = xx[win] - mx, yy[win] - my
        cov = np.array([[np.sum(wts * dx * dx), np.sum(wts * dx * dy)],
                        [np.sum(wts * dx * dy), np.sum(wts * dy * dy)]]) / total
        cx, cy = mx, my
        r = math.sqrt(total / math.pi / DARK_AREA_FRACTION)
        a, b, theta, sigma = _shape_from_moments(cov, r)
    ellipse = Ellipse(cx, cy, a, b, theta)
    return MomentsResult(cx, cy, cov, r, black, white, ellipse, sigma)


# ----------------------------------------------------------------------------------------------------------------------
# 3. Radial edges + direct ellipse fit
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class EdgeResult:
    ellipse: Ellipse
    rms_residual_px: float
    n_points: int


def refine_edges(lin: np.ndarray, guess: Ellipse, black: float, white: float, step_px: float = 0.1) -> EdgeResult | None:
    r = guess.mean_radius
    n_rays = int(np.clip(round(2.0 * math.pi * r * 1.5), 32, 360))
    phi = np.linspace(0.0, 2.0 * math.pi, n_rays, endpoint=False)
    rho_pred = guess.radius_at(phi)
    half = 0.35 * r + 2.0
    offsets = np.arange(-half, half + step_px / 2, step_px)
    rho = np.clip(rho_pred[:, None] + offsets[None, :], 0.2, None)
    xs = guess.cx + rho * np.cos(phi)[:, None]
    ys = guess.cy + rho * np.sin(phi)[:, None]
    prof = bilinear(lin, xs, ys)
    level = 0.5 * (black + white)
    below = prof[:, :-1] < level
    above = prof[:, 1:] >= level
    pts = []
    for k in range(n_rays):
        idx = np.flatnonzero(below[k] & above[k])
        if idx.size == 0:
            continue
        i = idx[np.argmin(np.abs(rho[k, idx] - rho_pred[k]))]
        s0, s1 = prof[k, i], prof[k, i + 1]
        frac = (level - s0) / (s1 - s0) if s1 != s0 else 0.5
        rr = rho[k, i] + frac * (rho[k, i + 1] - rho[k, i])
        pts.append((guess.cx + rr * math.cos(phi[k]), guess.cy + rr * math.sin(phi[k])))
    if len(pts) < 12:
        return None
    pts = np.asarray(pts)
    try:
        e = fit_ellipse_direct(pts)
        for _ in range(2):
            res = algebraic_residuals(e, pts)
            mad = 1.4826 * np.median(np.abs(res - np.median(res)))
            keep = np.abs(res - np.median(res)) <= max(3.0 * mad, 0.05)
            if keep.sum() < 12 or keep.all():
                break
            pts = pts[keep]
            e = fit_ellipse_direct(pts)
    except (ValueError, np.linalg.LinAlgError):
        return None
    res = algebraic_residuals(e, pts)
    return EdgeResult(e, float(np.sqrt(np.mean(res * res))), int(len(pts)))


# ----------------------------------------------------------------------------------------------------------------------
# 4. Public measurement API
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class AimingMarkMeasurement:
    method: str
    ellipse: Ellipse
    flux_radius_px: float
    black_level: float
    white_level: float
    blur_sigma_px: float
    edge_rms_px: float | None
    n_edge_points: int
    detection_score: float

    @property
    def centre_px(self) -> np.ndarray:
        return self.ellipse.centre


def measure_aiming_mark_all(image: np.ndarray, gamma: float | None = DEFAULT_GAMMA) -> dict[str, AimingMarkMeasurement]:
    """Run detection once and return every estimator's measurement (empty dict when no target is found)."""
    lin = linearize(image, gamma)
    candidates = find_candidates(lin)
    if not candidates:
        return {}
    cand = candidates[0]
    try:
        mom = refine_moments(lin, cand.cx, cand.cy, cand.radius_px)
    except RuntimeError:
        return {}
    edges = refine_edges(lin, mom.ellipse, mom.black, mom.white)
    common = dict(flux_radius_px=mom.flux_radius_px, black_level=mom.black, white_level=mom.white,
                  blur_sigma_px=mom.blur_sigma_px, detection_score=cand.score)
    out = {"moments": AimingMarkMeasurement("moments", mom.ellipse, edge_rms_px=None, n_edge_points=0, **common)}
    if edges is not None:
        e = edges.ellipse
        ratio = math.sqrt(e.a / e.b)
        hybrid = Ellipse(mom.cx, mom.cy, mom.flux_radius_px * ratio, mom.flux_radius_px / ratio, e.theta)
        out["edges"] = AimingMarkMeasurement("edges", e, edge_rms_px=edges.rms_residual_px,
                                             n_edge_points=edges.n_points, **common)
        out["hybrid"] = AimingMarkMeasurement("hybrid", hybrid, edge_rms_px=edges.rms_residual_px,
                                              n_edge_points=edges.n_points, **common)
    return out


def measure_aiming_mark(image: np.ndarray, method: str = "hybrid", gamma: float | None = DEFAULT_GAMMA):
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    return measure_aiming_mark_all(image, gamma).get(method)


@dataclass(frozen=True)
class ShotMeasurement:
    mark: AimingMarkMeasurement
    impact_xy_mm: np.ndarray
    score: ShotScore
    mm_per_px: float


def shot_from_mark(mark: AimingMarkMeasurement, bore_px, roll_deg: float = 0.0,
                   up_direction_px=None) -> ShotMeasurement:
    affine = ellipse_to_target_affine(mark.ellipse, BLACK_RADIUS_MM, roll_deg, up_direction_px)
    xy = apply_affine(affine, np.asarray(bore_px, dtype=float))[0]
    return ShotMeasurement(mark, xy, score_shot(float(xy[0]), float(xy[1])), local_mm_per_px(mark.ellipse))


def measure_shot(image: np.ndarray, bore_px, method: str = "hybrid", gamma: float | None = DEFAULT_GAMMA,
                 roll_deg: float = 0.0, up_direction_px=None) -> ShotMeasurement | None:
    """Full single-frame shot measurement: detect the black, rectify, map the bore pixel to target mm, score."""
    mark = measure_aiming_mark(image, method, gamma)
    if mark is None:
        return None
    return shot_from_mark(mark, bore_px, roll_deg, up_direction_px)
