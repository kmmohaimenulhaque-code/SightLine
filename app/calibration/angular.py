"""Angular ground truth for rotation experiments (E-004a) and the image motion it should produce.

Everything here is DERIVED geometry. No value in this module is a measurement: the inputs (lever radius, displacement,
focal length in pixels, distances) must be measured by the operator and carry their own uncertainty.

Lever jig: a rigid arm pivots about an axis; a point at radius ``r`` from the pivot is displaced by ``d``
perpendicular to the arm. The arm, and everything rigidly fixed to it, rotates by

    theta = atan(d / r)   (= d / r to first order; the difference is < 2e-6 relative below 2 mrad)

Expected image motion of a distant fixed target for a camera rotated by ``theta`` about an axis perpendicular to its
optical axis:

    delta_px = f_px * tan(theta) * (1 + rho / L)

``rho`` is the distance by which the camera's entrance pupil sits *ahead of* the pivot axis along the line of sight
(negative if behind) and ``L`` the pupil-to-target distance: rotating about a pivot that is not at the pupil also
translates the camera, which adds parallax (first order in rho / L; an offset perpendicular to the line of sight only
contributes at second order).

``f_px`` must be a calibrated or measured focal length in pixels for the capture mode in use — never the marketing
"equivalent" focal length. ``focal_px_from_target`` measures it from the printed target itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Measured:
    """A measured quantity with its standard uncertainty (1 sigma), in the same unit."""

    value: float
    sigma: float = 0.0

    def __post_init__(self) -> None:
        if not (math.isfinite(self.value) and math.isfinite(self.sigma)) or self.sigma < 0.0:
            raise ValueError("value and sigma must be finite and sigma >= 0")

    @property
    def relative(self) -> float:
        return self.sigma / abs(self.value) if self.value else math.inf

    def as_dict(self) -> dict:
        return {"value": self.value, "sigma": self.sigma}

    @classmethod
    def of(cls, x) -> "Measured":
        """Accept a ``Measured``, a ``{"value": .., "sigma": ..}`` mapping, a ``(value, sigma)`` pair or a number."""
        if isinstance(x, Measured):
            return x
        if isinstance(x, dict):
            return cls(float(x["value"]), float(x.get("sigma", 0.0)))
        if isinstance(x, (tuple, list)):
            return cls(float(x[0]), float(x[1]))
        return cls(float(x))


def lever_angle_rad(displacement_mm, radius_mm) -> Measured:
    """Rotation of a lever from a displacement ``d`` at radius ``r``, with first-order uncertainty propagation.

    sigma_theta^2 = [ (sigma_d / r)^2 + (d * sigma_r / r^2)^2 ] / (1 + (d / r)^2)^2
    """
    d, r = Measured.of(displacement_mm), Measured.of(radius_mm)
    if r.value <= 0.0:
        raise ValueError("radius must be positive")
    ratio = d.value / r.value
    theta = math.atan(ratio)
    sigma = math.hypot(d.sigma / r.value, d.value * r.sigma / r.value**2) / (1.0 + ratio * ratio)
    return Measured(theta, sigma)


def expected_image_shift_px(theta_rad, f_px, pivot_ahead_mm=0.0, target_distance_mm=math.inf) -> Measured:
    """Image displacement (pixels) of a distant fixed target for a camera rotation ``theta`` — see module docstring.

    Uncertainty: relative terms of theta, f_px and the parallax factor added in quadrature.
    """
    th, f = Measured.of(theta_rad), Measured.of(f_px)
    if f.value <= 0.0:
        raise ValueError("f_px must be positive")
    par, sig_par = 1.0, 0.0
    infinite = isinstance(target_distance_mm, (int, float)) and math.isinf(target_distance_mm)
    if not infinite:                                         # finite target distance: pivot parallax applies
        rho, dist = Measured.of(pivot_ahead_mm), Measured.of(target_distance_mm)
        if dist.value <= 0.0:
            raise ValueError("target distance must be positive")
        par = 1.0 + rho.value / dist.value
        sig_par = math.hypot(rho.sigma / dist.value, rho.value * dist.sigma / dist.value**2)
    t = math.tan(th.value)
    value = f.value * t * par
    var = (f.value * par * th.sigma / math.cos(th.value) ** 2) ** 2 + (t * par * f.sigma) ** 2 + (f.value * t * sig_par) ** 2
    return Measured(value, math.sqrt(var))


def focal_px_from_target(size_px, size_mm, distance_mm) -> Measured:
    """Focal length in pixels measured from a feature of known size seen face-on near the image centre:

        f_px = size_px * distance / size_mm

    ``size_mm`` must be the *measured* printed size (not the nominal one) and ``distance_mm`` the measured distance from
    the camera to the target face. This is a measured intrinsic for that capture mode (pinhole, on-axis).
    """
    s_px, s_mm, dist = Measured.of(size_px), Measured.of(size_mm), Measured.of(distance_mm)
    if min(s_px.value, s_mm.value, dist.value) <= 0.0:
        raise ValueError("all inputs must be positive")
    value = s_px.value * dist.value / s_mm.value
    return Measured(value, value * math.sqrt(s_px.relative**2 + s_mm.relative**2 + dist.relative**2))


def angle_from_image_shift_rad(shift_px: float, f_px: float) -> float:
    """Apparent camera rotation implied by an image displacement (inverse of the pinhole relation, no parallax)."""
    if f_px <= 0.0:
        raise ValueError("f_px must be positive")
    return math.atan(shift_px / f_px)


def exposure_response(frequency_hz: float, exposure_s: float) -> float:
    """Amplitude response of one frame's exposure to sinusoidal image motion (boxcar average over the exposure):
    |sin(pi f T) / (pi f T)|. DERIVED. The centroid of the smear is the position at mid-exposure."""
    x = math.pi * frequency_hz * exposure_s
    return 1.0 if abs(x) < 1e-12 else abs(math.sin(x) / x)
