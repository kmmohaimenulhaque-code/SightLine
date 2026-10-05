"""Ellipse representation and direct least-squares ellipse fitting.

The fit is the numerically stable form of the ellipse-specific direct least-squares method (Fitzgibbon, Pilu & Fisher
1999; Halir & Flusser 1998), implemented here from the published mathematics (SOURCES_AND_LICENSES.md S-15).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class Ellipse:
    """Image-space ellipse. ``a >= b`` are semi-axes in pixels; ``theta`` is the major-axis angle in radians,
    measured from the +u axis toward +v (image coordinates, v down)."""

    cx: float
    cy: float
    a: float
    b: float
    theta: float

    @property
    def centre(self) -> np.ndarray:
        return np.array([self.cx, self.cy], dtype=float)

    @property
    def mean_radius(self) -> float:
        return math.sqrt(self.a * self.b)

    @property
    def axis_ratio(self) -> float:
        return self.b / self.a

    def radius_at(self, phi: np.ndarray) -> np.ndarray:
        """Distance from the centre to the ellipse along direction angle ``phi`` (image coordinates)."""
        d = np.asarray(phi, dtype=float) - self.theta
        return (self.a * self.b) / np.sqrt((self.b * np.cos(d)) ** 2 + (self.a * np.sin(d)) ** 2)

    def points(self, n: int = 72) -> np.ndarray:
        s = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        c, si = math.cos(self.theta), math.sin(self.theta)
        x = self.a * np.cos(s)
        y = self.b * np.sin(s)
        return np.stack([self.cx + c * x - si * y, self.cy + si * x + c * y], axis=1)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Ellipse":
        return cls(**{k: float(d[k]) for k in ("cx", "cy", "a", "b", "theta")})


def ellipse_from_covariance(cx: float, cy: float, cov: np.ndarray, scale: float = 2.0) -> Ellipse:
    """Ellipse whose semi-axes are ``scale * sqrt(eigenvalues)`` of a 2x2 covariance (2.0 for a uniform disc)."""
    w, v = np.linalg.eigh(np.asarray(cov, dtype=float))
    w = np.clip(w, 0.0, None)
    major = v[:, 1]
    return Ellipse(cx, cy, scale * math.sqrt(w[1]), scale * math.sqrt(w[0]), math.atan2(major[1], major[0]))


def conic_to_ellipse(coef: np.ndarray) -> Ellipse:
    """Convert A x^2 + B xy + C y^2 + D x + E y + F = 0 to geometric parameters."""
    A, B, C, D, E, F = (float(c) for c in coef)
    M = np.array([[2 * A, B], [B, 2 * C]])
    x0, y0 = np.linalg.solve(M, [-D, -E])
    F0 = A * x0 * x0 + B * x0 * y0 + C * y0 * y0 + D * x0 + E * y0 + F
    Q = np.array([[A, B / 2.0], [B / 2.0, C]])
    w, v = np.linalg.eigh(Q)
    if F0 == 0 or np.any(-F0 / w <= 0):
        raise ValueError("conic is not a real ellipse")
    axes = np.sqrt(-F0 / w)  # w ascending -> axes descending
    a, b = float(axes[0]), float(axes[1])
    major = v[:, 0]
    if b > a:
        a, b = b, a
        major = v[:, 1]
    return Ellipse(float(x0), float(y0), a, b, math.atan2(major[1], major[0]))


def fit_ellipse_direct(points: np.ndarray) -> Ellipse:
    """Ellipse-specific direct least-squares fit to (N, 2) points, N >= 6."""
    p = np.asarray(points, dtype=float)
    if p.shape[0] < 6:
        raise ValueError("need at least 6 points")
    m = p.mean(axis=0)
    s = float(np.sqrt(np.mean(np.sum((p - m) ** 2, axis=1)))) or 1.0
    x = (p[:, 0] - m[0]) / s
    y = (p[:, 1] - m[1]) / s
    D1 = np.column_stack([x * x, x * y, y * y])
    D2 = np.column_stack([x, y, np.ones_like(x)])
    S1, S2, S3 = D1.T @ D1, D1.T @ D2, D2.T @ D2
    T = -np.linalg.solve(S3, S2.T)
    M = S1 + S2 @ T
    M = np.array([M[2] / 2.0, -M[1], M[0] / 2.0])  # premultiply by inv(C1)
    w, v = np.linalg.eig(M)
    v = np.real(v)
    cond = 4.0 * v[0] * v[2] - v[1] ** 2
    idx = np.flatnonzero(cond > 0)
    if idx.size == 0:
        raise ValueError("no ellipse solution")
    a1 = v[:, idx[0]]
    coef_n = np.concatenate([a1, T @ a1])
    e = conic_to_ellipse(coef_n)
    return Ellipse(e.cx * s + m[0], e.cy * s + m[1], e.a * s, e.b * s, e.theta)


def algebraic_residuals(e: Ellipse, points: np.ndarray) -> np.ndarray:
    """Approximate geometric distance of points to the ellipse (radial difference along the centre ray)."""
    p = np.asarray(points, dtype=float) - e.centre
    phi = np.arctan2(p[:, 1], p[:, 0])
    return np.hypot(p[:, 0], p[:, 1]) - e.radius_at(phi)
