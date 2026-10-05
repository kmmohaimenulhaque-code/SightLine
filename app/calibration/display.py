"""Display geometry: unity magnification ("Fit to FOV"), derived in
docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md §5 (DERIVED).

Unity magnification: an object subtending angle theta at the eye should subtend the same angle on the screen.
"""

from __future__ import annotations

MM_PER_INCH = 25.4


def unity_magnification_scale(f_px: float, eye_to_screen_mm: float, screen_ppi: float) -> float:
    """Screen pixels per camera pixel for unity magnification: s = D_eye * ppi / (25.4 * f_px)."""
    if f_px <= 0 or eye_to_screen_mm <= 0 or screen_ppi <= 0:
        raise ValueError("all inputs must be positive")
    return eye_to_screen_mm * screen_ppi / (MM_PER_INCH * f_px)


def target_anchored_scale(
    black_diameter_px: float,
    eye_to_screen_mm: float,
    screen_ppi: float,
    target_distance_mm: float = 10000.0,
    black_diameter_mm: float = 59.5,
) -> float:
    """Screen pixels per camera pixel that draw the black at its true visual angle, using the black itself as the
    ruler (needs no focal length): on-screen size = black_diameter_mm * D_eye / L_target."""
    if black_diameter_px <= 0:
        raise ValueError("black_diameter_px must be positive")
    on_screen_mm = black_diameter_mm * eye_to_screen_mm / target_distance_mm
    return on_screen_mm / MM_PER_INCH * screen_ppi / black_diameter_px


def on_screen_size_mm(feature_mm: float, eye_to_screen_mm: float, target_distance_mm: float = 10000.0) -> float:
    """Physical on-screen size that matches the real feature's visual angle."""
    return feature_mm * eye_to_screen_mm / target_distance_mm
