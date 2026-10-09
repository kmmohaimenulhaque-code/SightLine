"""Per-frame image position of the aiming mark across a frame sequence (deterministic; no learning).

Estimator hierarchy (Mission 2 experimental brief §9). Every frame gets all of them, so they can be compared:

1. ``ellipse_centre`` — centre of the direct least-squares ellipse fitted to sub-pixel edge crossings of the black.
2. ``x, y``           — flux-weighted (moments) centre of the black; the "hybrid" centre characterised in E-001.
3. ``pc_dx, pc_dy``   — phase-correlation shift of a fixed window against the first valid frame (secondary check;
                        uses all texture in the window, not the target model).
4. ``centroid``       — centroid of a plain binary threshold (baseline only).

(1) and (2) reuse ``app.vision.aiming_mark`` unchanged — the code path E-001 characterised. Feature tracking around
the target (card corners) is not implemented.

Rules: a frame that cannot be measured is recorded with ``valid=False`` and a reason. Nothing is interpolated here.
``confidence`` is a heuristic self-consistency score in [0, 1] (edge-fit inlier fraction x agreement between the
moments and ellipse centres); it is not a calibrated probability.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import cv2
import numpy as np

from app.vision.aiming_mark import DEFAULT_GAMMA, find_candidates, linearize, refine_edges, refine_moments

NAN = float("nan")
CONFIDENCE_AGREEMENT_PX = 0.5   # ASSUMED scale: centre disagreement at which confidence drops to 1/e
MAX_RADIUS_CHANGE = 0.25        # ASSUMED: frame-to-frame relative radius change treated as a tracking failure


@dataclass
class FrameRecord:
    frame_id: int
    timestamp_s: float
    valid: bool
    reason: str = ""
    x: float = NAN
    y: float = NAN
    ellipse_centre_x: float = NAN
    ellipse_centre_y: float = NAN
    centroid_x: float = NAN
    centroid_y: float = NAN
    pc_dx: float = NAN
    pc_dy: float = NAN
    pc_response: float = NAN
    radius_px: float = NAN
    semi_major_px: float = NAN
    semi_minor_px: float = NAN
    ellipse_theta_rad: float = NAN
    black_level: float = NAN
    white_level: float = NAN
    blur_sigma_px: float = NAN
    edge_rms_px: float = NAN
    n_edge_points: int = 0
    confidence: float = 0.0

    def as_row(self) -> dict:
        return asdict(self)


FRAME_FIELDS = [f.name for f in fields(FrameRecord)]


def _n_rays(radius_px: float) -> int:
    return int(np.clip(round(2.0 * math.pi * radius_px * 1.5), 32, 360))  # same rule as refine_edges


class TargetTracker:
    """Track the black aiming mark through a sequence. ``hint_px`` (x, y) selects the detection nearest to it on the
    first frame — use it when the scene contains other dark discs; otherwise the best-scoring detection is used."""

    def __init__(self, gamma: float | None = DEFAULT_GAMMA, hint_px: tuple[float, float] | None = None,
                 roi_radius_factor: float = 3.0, roi_margin_px: int = 8) -> None:
        self.gamma = gamma
        self.hint_px = hint_px
        self.roi_radius_factor = roi_radius_factor
        self.roi_margin_px = roi_margin_px
        self._last: tuple[float, float, float] | None = None   # (x, y, radius) of the last valid frame
        self._pc_ref: np.ndarray | None = None
        self._pc_box: tuple[int, int, int, int] | None = None
        self._pc_window: np.ndarray | None = None

    # ---- detection / refinement -----------------------------------------------------------------------------------
    def _detect(self, lin: np.ndarray) -> tuple[float, float, float] | None:
        cands = find_candidates(lin)
        if not cands:
            return None
        if self.hint_px is not None:
            c = min(cands, key=lambda k: math.hypot(k.cx - self.hint_px[0], k.cy - self.hint_px[1]))
        else:
            c = cands[0]
        return c.cx, c.cy, c.radius_px

    def _roi(self, shape: tuple[int, int], x: float, y: float, r: float) -> tuple[int, int, int, int]:
        half = int(math.ceil(self.roi_radius_factor * r)) + self.roi_margin_px
        h, w = shape
        x0, y0 = max(0, int(round(x)) - half), max(0, int(round(y)) - half)
        return x0, y0, min(w, int(round(x)) + half + 1), min(h, int(round(y)) + half + 1)

    def _refine(self, gray: np.ndarray, seed: tuple[float, float, float], check_radius: bool):
        """Moments refinement from a seed inside its ROI. Returns ``(mom, lin, x0, y0)`` or a failure reason."""
        x0, y0, x1, y1 = self._roi(gray.shape, *seed)
        lin = linearize(gray[y0:y1, x0:x1], self.gamma)
        try:
            mom = refine_moments(lin, seed[0] - x0, seed[1] - y0, seed[2])
        except RuntimeError as exc:
            return f"moments failed: {exc}"
        if not (math.isfinite(mom.cx) and math.isfinite(mom.cy)) or mom.white <= mom.black:
            return "degenerate measurement"
        if check_radius and abs(mom.flux_radius_px / seed[2] - 1.0) > MAX_RADIUS_CHANGE:
            return "radius jump (tracking lost)"
        return mom, lin, x0, y0

    def process(self, frame_id: int, timestamp_s: float, image: np.ndarray) -> FrameRecord:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        rec = FrameRecord(frame_id, float(timestamp_s), False)
        result = self._refine(gray, self._last, True) if self._last is not None else "no previous position"
        if isinstance(result, str):
            # Not tracking, or tracking failed (e.g. the target jumped by more than its radius): detect afresh in
            # this same frame. The frame is only declared invalid if a fresh detection also fails.
            self._last = None
            seed = self._detect(linearize(gray, self.gamma))
            if seed is None:
                rec.reason = "target not detected"
                return rec
            result = self._refine(gray, seed, False)
            if isinstance(result, str):
                rec.reason = result
                return rec
        mom, lin, x0, y0 = result
        x1, y1 = x0 + lin.shape[1], y0 + lin.shape[0]
        rec.x, rec.y = mom.cx + x0, mom.cy + y0
        rec.radius_px, rec.black_level, rec.white_level = mom.flux_radius_px, mom.black, mom.white
        rec.blur_sigma_px = mom.blur_sigma_px
        rec.semi_major_px, rec.semi_minor_px, rec.ellipse_theta_rad = mom.ellipse.a, mom.ellipse.b, mom.ellipse.theta
        edges = refine_edges(lin, mom.ellipse, mom.black, mom.white)
        if edges is not None:
            e = edges.ellipse
            rec.ellipse_centre_x, rec.ellipse_centre_y = e.cx + x0, e.cy + y0
            rec.semi_major_px, rec.semi_minor_px, rec.ellipse_theta_rad = e.a, e.b, e.theta
            rec.edge_rms_px, rec.n_edge_points = edges.rms_residual_px, edges.n_points
            inlier = min(1.0, edges.n_points / _n_rays(mom.ellipse.mean_radius))
            gap = math.hypot(e.cx - mom.cx, e.cy - mom.cy)
            rec.confidence = float(inlier * math.exp(-((gap / CONFIDENCE_AGREEMENT_PX) ** 2)))
        # Baseline: centroid of a plain mid-level threshold inside the moments window (gamma-encoded pixels).
        roi = gray[y0:y1, x0:x1].astype(np.float64)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        inside = np.hypot(xx - rec.x, yy - rec.y) <= 1.4 * mom.flux_radius_px
        dark = inside & (roi < 0.5 * (roi[inside].min() + roi[inside].max()))
        if dark.any():
            rec.centroid_x, rec.centroid_y = float(xx[dark].mean()), float(yy[dark].mean())
        self._phase_correlation(gray, rec)
        rec.valid = True
        self._last = (rec.x, rec.y, mom.flux_radius_px)
        return rec

    def _phase_correlation(self, gray: np.ndarray, rec: FrameRecord) -> None:
        """Shift of a fixed window relative to the first valid frame; positive = content moved toward +x / +y."""
        if self._pc_box is None:
            half = int(2 ** math.ceil(math.log2(max(16.0, 4.0 * rec.radius_px))))
            h, w = gray.shape
            cx, cy = int(round(rec.x)), int(round(rec.y))
            if cx - half < 0 or cy - half < 0 or cx + half > w or cy + half > h:
                return  # window does not fit: secondary estimator unavailable for this sequence
            self._pc_box = (cx - half, cy - half, cx + half, cy + half)
            self._pc_window = cv2.createHanningWindow((2 * half, 2 * half), cv2.CV_64F)
            x0, y0, x1, y1 = self._pc_box
            self._pc_ref = gray[y0:y1, x0:x1].astype(np.float64)
        x0, y0, x1, y1 = self._pc_box
        (dx, dy), response = cv2.phaseCorrelate(self._pc_ref, gray[y0:y1, x0:x1].astype(np.float64), self._pc_window)
        rec.pc_dx, rec.pc_dy, rec.pc_response = float(dx), float(dy), float(response)


def track_frames(frames: Iterable[tuple[int, float, np.ndarray]], gamma: float | None = DEFAULT_GAMMA,
                 hint_px: tuple[float, float] | None = None) -> list[FrameRecord]:
    """Track the target through ``(frame_id, timestamp_s, image)`` items."""
    tracker = TargetTracker(gamma=gamma, hint_px=hint_px)
    return [tracker.process(fid, t, img) for fid, t, img in frames]


def write_frames_csv(records: list[FrameRecord], path: str | Path, extra: dict | None = None,
                     per_frame: dict[str, list] | None = None) -> None:
    """Write one row per frame. ``extra`` adds constant columns (camera, resolution, fps); ``per_frame`` adds columns
    computed later by a harness (estimated_rotation, expected_rotation, residual)."""
    extra, per_frame = extra or {}, per_frame or {}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FRAME_FIELDS + list(extra) + list(per_frame))
        w.writeheader()
        for i, r in enumerate(records):
            row = {k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.as_row().items()}
            row.update(extra)
            row.update({k: (f"{v[i]:.6g}" if isinstance(v[i], float) else v[i]) for k, v in per_frame.items()})
            w.writerow(row)


def valid_arrays(records: list[FrameRecord], centre: str = "ellipse") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(index, t, xy)`` of valid frames for the chosen centre estimator: ``ellipse`` (falls back to the moments
    centre on frames where the edge fit failed), ``moments``, ``centroid`` or ``phase`` (shift, not position)."""
    idx, t, xy = [], [], []
    for i, r in enumerate(records):
        if not r.valid:
            continue
        if centre == "ellipse":
            p = (r.ellipse_centre_x, r.ellipse_centre_y) if math.isfinite(r.ellipse_centre_x) else (r.x, r.y)
        elif centre == "moments":
            p = (r.x, r.y)
        elif centre == "centroid":
            p = (r.centroid_x, r.centroid_y)
        elif centre == "phase":
            p = (r.pc_dx, r.pc_dy)
        else:
            raise ValueError("centre must be ellipse, moments, centroid or phase")
        if math.isfinite(p[0]) and math.isfinite(p[1]):
            idx.append(i)
            t.append(r.timestamp_s)
            xy.append(p)
    return np.asarray(idx, dtype=int), np.asarray(t, dtype=float), np.asarray(xy, dtype=float).reshape(-1, 2)
