"""Pinhole camera with Brown radial distortion (k1, k2).

Conventions (docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md §1):
* Camera frame C: OpenCV convention — x right, y down, z forward; millimetres.
* Image frame I: pixel centres at integer coordinates, (0, 0) = centre of the top-left pixel; u right, v down.
* Distortion acts on normalised coordinates: x_d = x_n * (1 + k1 r^2 + k2 r^4).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class CameraModel:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float = 0.0
    k2: float = 0.0

    # ---- construction ---------------------------------------------------------------------------------------------
    @classmethod
    def from_hfov(cls, width: int, height: int, hfov_deg: float, k1: float = 0.0, k2: float = 0.0) -> "CameraModel":
        """Square pixels, principal point at the image centre, focal length from the horizontal field of view."""
        fx = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
        return cls(int(width), int(height), fx, fx, (width - 1) / 2.0, (height - 1) / 2.0, k1, k2)

    @classmethod
    def from_dict(cls, d: dict) -> "CameraModel":
        return cls(**{k: d[k] for k in ("width", "height", "fx", "fy", "cx", "cy", "k1", "k2")})

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def principal_point(self) -> np.ndarray:
        return np.array([self.cx, self.cy], dtype=float)

    def mm_per_pixel_on_axis(self, distance_mm: float) -> float:
        return distance_mm / self.fx

    # ---- distortion -----------------------------------------------------------------------------------------------
    def _radial_factor(self, xn: np.ndarray) -> np.ndarray:
        r2 = np.sum(xn * xn, axis=-1)
        return 1.0 + self.k1 * r2 + self.k2 * r2 * r2

    def distort(self, xn: np.ndarray) -> np.ndarray:
        xn = np.asarray(xn, dtype=float)
        return xn * self._radial_factor(xn)[..., None]

    def undistort(self, xd: np.ndarray, iterations: int = 20) -> np.ndarray:
        """Invert the radial model by fixed-point iteration (adequate for |k1|, |k2| typical of phone cameras)."""
        xd = np.asarray(xd, dtype=float)
        if self.k1 == 0.0 and self.k2 == 0.0:
            return xd.copy()
        xn = xd.copy()
        for _ in range(iterations):
            xn = xd / self._radial_factor(xn)[..., None]
        return xn

    # ---- projection -----------------------------------------------------------------------------------------------
    def normalized_to_pixel(self, xn: np.ndarray) -> np.ndarray:
        xd = self.distort(xn)
        return np.stack([self.fx * xd[..., 0] + self.cx, self.fy * xd[..., 1] + self.cy], axis=-1)

    def pixel_to_normalized(self, uv: np.ndarray) -> np.ndarray:
        uv = np.asarray(uv, dtype=float)
        xd = np.stack([(uv[..., 0] - self.cx) / self.fx, (uv[..., 1] - self.cy) / self.fy], axis=-1)
        return self.undistort(xd)

    def project(self, points_c: np.ndarray) -> np.ndarray:
        """Project camera-frame points (N, 3), Z > 0, to pixels (N, 2)."""
        p = np.asarray(points_c, dtype=float)
        if np.any(p[..., 2] <= 0):
            raise ValueError("points must be in front of the camera (Z > 0)")
        return self.normalized_to_pixel(p[..., :2] / p[..., 2:3])

    def pixel_rays(self, uv: np.ndarray) -> np.ndarray:
        """Unit ray directions in frame C for pixels (N, 2)."""
        xn = self.pixel_to_normalized(uv)
        rays = np.concatenate([xn, np.ones(xn.shape[:-1] + (1,))], axis=-1)
        return rays / np.linalg.norm(rays, axis=-1, keepdims=True)
