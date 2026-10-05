"""Target-anchored rectification: image pixels -> target-plane millimetres, from the imaged black aiming mark.

Basis (DERIVED, docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md §6): the whole target subtends < 1 degree at
10 m, so perspective and lens distortion are locally affine around it. The affine map that turns the imaged black
(an ellipse) back into a circle of the ISSF black radius is then the image -> target map near the target. No camera
intrinsics are needed (ARCHITECTURE.md D-003).
"""

from __future__ import annotations

import math

import numpy as np

from app.scoring.issf import BLACK_RADIUS_MM

from .ellipse import Ellipse

_FLIP_V = np.diag([1.0, -1.0])  # image v (down) -> target y (up)


def _rot2(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, -s], [s, c]], dtype=float)


def ellipse_to_target_affine(
    ellipse: Ellipse,
    radius_mm: float = BLACK_RADIUS_MM,
    roll_deg: float = 0.0,
    up_direction_px=None,
) -> np.ndarray:
    """2x3 affine map from image pixels to target millimetres.

    A circle has no orientation, so the ellipse fixes distances but not the rotation of the result. Two ways to fix it:

    * ``up_direction_px`` — image-space direction of the target's "up" (+y) at the target. In the app this comes from
      the phone's gravity vector, assuming the target hangs plumb (D-015). It removes the residual in-plane rotation
      of compound tilts exactly (under weak perspective).
    * ``roll_deg`` — otherwise, the apparent in-image rotation of the target.

    Neither changes the distance from the centre, so neither changes the score.
    """
    if ellipse.a <= 0 or ellipse.b <= 0:
        raise ValueError("degenerate ellipse")
    r = _rot2(ellipse.theta)
    unstretch = r @ np.diag([radius_mm / ellipse.a, radius_mm / ellipse.b]) @ r.T  # symmetric, px -> mm
    if up_direction_px is not None:
        w = _FLIP_V @ unstretch @ np.asarray(up_direction_px, dtype=float)
        if not np.all(np.isfinite(w)) or np.hypot(*w) == 0:
            raise ValueError("invalid up direction")
        A = _rot2(math.pi / 2.0 - math.atan2(w[1], w[0])) @ _FLIP_V @ unstretch
    else:
        A = _FLIP_V @ _rot2(-math.radians(roll_deg)) @ unstretch
    b = -A @ ellipse.centre
    return np.hstack([A, b[:, None]])


def apply_affine(affine: np.ndarray, uv: np.ndarray) -> np.ndarray:
    uv = np.atleast_2d(np.asarray(uv, dtype=float))
    return uv @ affine[:, :2].T + affine[:, 2]


def image_to_target_mm(ellipse: Ellipse, uv, radius_mm: float = BLACK_RADIUS_MM, roll_deg: float = 0.0,
                       up_direction_px=None) -> np.ndarray:
    """Convenience: map one or more pixels to target millimetres."""
    out = apply_affine(ellipse_to_target_affine(ellipse, radius_mm, roll_deg, up_direction_px), uv)
    return out[0] if np.ndim(uv) == 1 else out


def local_mm_per_px(ellipse: Ellipse, radius_mm: float = BLACK_RADIUS_MM) -> float:
    """Isotropic-equivalent scale at the target (mm per pixel)."""
    return radius_mm / ellipse.mean_radius
