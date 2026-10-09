"""Synthetic frame sequences of the target under a prescribed camera rotation (category SYNTHETIC).

Purpose: check that the experiment harnesses recover a *known, injected* image response before any real clip is
analysed (sanity check of E-004a / E-002 code), and estimate what the harness could resolve. Output is SIMULATED and
is never experimental evidence about a phone.

A camera rotation theta about its own centre moves the simulated bore impact by L * tan(theta) on the target; the
frames are rendered on one fixed pixel window (``render(..., bounds=...)``), so the target moves in the image exactly
as for a rotating camera. ``hypothetical_stabiliser`` is a deliberately simple stand-in (first-order high-pass
compensation with a gain) used only to give the harness something to detect. It is NOT a model of any real OIS.
"""

from __future__ import annotations

import math

import numpy as np

from app.calibration.camera import CameraModel
from ml.datasets.synthetic_target import Degradation, SceneSpec, render


def hypothetical_stabiliser(theta: np.ndarray, rate_hz: float, corner_hz: float, gain: float = 1.0) -> np.ndarray:
    """Residual apparent rotation after a first-order high-pass compensator: the compensator cancels ``gain`` x the
    high-passed rotation (motion faster than ``corner_hz``) and lets slower motion through (it "re-centres").
    ``corner_hz = 0`` makes it a pure lock (cancels everything, scaled by ``gain``). HYPOTHETICAL — not a phone model."""
    theta = np.asarray(theta, float)
    if corner_hz <= 0.0:
        return theta - gain * (theta - theta[0])
    a = 1.0 / (1.0 + 2.0 * math.pi * corner_hz / rate_hz)
    hp = np.zeros_like(theta)
    for k in range(1, len(theta)):
        hp[k] = a * (hp[k - 1] + theta[k] - theta[k - 1])
    return theta - gain * hp


def render_sequence(
    camera: CameraModel,
    theta_xy_rad: np.ndarray,
    rng: np.random.Generator,
    degradation: Degradation | None = None,
    window_px: tuple[int, int] = (256, 256),
    distance_mm: float = 10000.0,
    yaw_deg: float = 2.0,
    pitch_deg: float = -1.5,
    roll_deg: float = 0.3,
) -> tuple[np.ndarray, np.ndarray]:
    """Render one frame per row of ``theta_xy_rad`` (apparent camera rotation about the image x and y directions).

    Returns ``(frames, centres)``: uint8 frames of shape (N, h, w) on a fixed window centred on the principal point,
    and the exact projected target centre in window pixels for every frame (ground truth).
    """
    theta = np.asarray(theta_xy_rad, float).reshape(-1, 2)
    deg = degradation or Degradation(jpeg_quality=None)
    w, h = window_px
    u0, v0 = int(round(camera.cx)) - w // 2, int(round(camera.cy)) - h // 2
    bounds = (u0, v0, u0 + w, v0 + h)
    frames = np.empty((len(theta), h, w), dtype=np.uint8)
    centres = np.empty((len(theta), 2))
    for k, (tx, ty) in enumerate(theta):
        spec = SceneSpec(camera, (camera.cx, camera.cy), (distance_mm * math.tan(tx), distance_mm * math.tan(ty)),
                         distance_mm, yaw_deg, pitch_deg, roll_deg, degradation=deg)
        s = render(spec, rng, bounds=bounds)
        frames[k] = s.image
        centres[k] = s.ground_truth["target_centre_px_canvas"]
    return frames, centres
