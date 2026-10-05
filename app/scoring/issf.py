"""ISSF 10 m Air Pistol target geometry and scoring.

Evidence status of every constant (see VALIDATION.md):

* Ring diameters and tolerances, inner ten, black aiming mark, ring-line thickness, minimum card size:
  VERIFIED — ISSF Rule Book 2026 (Second Print 07/2026), General Technical Rules 6.3.4.6.
* Calibre 4.5 mm: VERIFIED — ISSF Pistol Rules 2026, 8.4.3.5 and 8.4.4.
* Range 10 m +/- 0.05 m: VERIFIED — GTR 6.4.5.2.
* Decimal scoring ("the scoring area for one full ring" divided "into ten equal scoring rings"): VERIFIED — GTR 6.3.3.1.
* EST accuracy requirement of half a decimal ring: rule VERIFIED (GTR 6.3.2.2); the 0.4 mm value is DERIVED.
* Shot-centre scoring zones (ring radius + pellet radius): DERIVED. Relies on the paper-target convention that a hit
  touching a ring line scores the higher value (annex not retrieved this session; VALIDATION.md C-010).

All distances are in millimetres in the target frame T (origin at the centre of the 10 ring, x right, y up).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

RING_DIAMETERS_MM: dict[int, float] = {
    10: 11.5, 9: 27.5, 8: 43.5, 7: 59.5, 6: 75.5,
    5: 91.5, 4: 107.5, 3: 123.5, 2: 139.5, 1: 155.5,
}
RING_TOLERANCES_MM: dict[int, float] = {
    10: 0.1, 9: 0.1, 8: 0.2, 7: 0.5, 6: 0.5,
    5: 0.5, 4: 0.5, 3: 0.5, 2: 0.5, 1: 0.5,
}
INNER_TEN_DIAMETER_MM = 5.0
BLACK_AIMING_MARK_DIAMETER_MM = 59.5          # "Black from 7 to 10 rings"
BLACK_RINGS = (7, 8, 9, 10)
RING_LINE_THICKNESS_RANGE_MM = (0.1, 0.2)
MIN_CARD_SIZE_MM = (170.0, 170.0)
PELLET_DIAMETER_MM = 4.5
RANGE_DISTANCE_M = 10.0
RANGE_DISTANCE_TOLERANCE_M = 0.05

# ---- Derived quantities -------------------------------------------------------------------------------------------
PELLET_RADIUS_MM = PELLET_DIAMETER_MM / 2.0
BLACK_RADIUS_MM = BLACK_AIMING_MARK_DIAMETER_MM / 2.0
RING_RADII_MM: dict[int, float] = {n: d / 2.0 for n, d in RING_DIAMETERS_MM.items()}
RING_PITCH_MM = RING_RADII_MM[9] - RING_RADII_MM[10]                       # 8.0
SCORING_ZONE_RADII_MM: dict[int, float] = {n: r + PELLET_RADIUS_MM for n, r in RING_RADII_MM.items()}  # 10 -> 8.0
INNER_TEN_ZONE_RADIUS_MM = INNER_TEN_DIAMETER_MM / 2.0 + PELLET_RADIUS_MM  # 4.75
DECIMAL_STEP_MM = RING_PITCH_MM / 10.0                                     # 0.8
EST_ACCURACY_REQUIREMENT_MM = DECIMAL_STEP_MM / 2.0                        # 0.4
MAX_SCORING_DISTANCE_MM = SCORING_ZONE_RADII_MM[1]                         # 80.0

# Lines printed inside the black are white (rings 8, 9, 10 and the inner ten); lines outside it are black (rings 1-6).
# The ring-7 boundary is the edge of the black itself.
WHITE_LINE_RADII_MM: tuple[float, ...] = (RING_RADII_MM[8], RING_RADII_MM[9], RING_RADII_MM[10], INNER_TEN_DIAMETER_MM / 2.0)
BLACK_LINE_RADII_MM: tuple[float, ...] = tuple(RING_RADII_MM[n] for n in (6, 5, 4, 3, 2, 1))

# Boundary tolerance: a pellet centre exactly on a zone boundary scores the higher value. The epsilon only absorbs
# floating-point representation error (it is ~1e-9 mm, far below any physical tolerance).
_BOUNDARY_EPS = 1e-9


def _validate_distance(distance_mm: float) -> float:
    d = float(distance_mm)
    if not math.isfinite(d) or d < 0.0:
        raise ValueError(f"distance_mm must be a finite, non-negative number, got {distance_mm!r}")
    return d


def decimal_score_tenths(distance_mm: float) -> int:
    """Decimal score in integer tenths of a ring (109 == 10.9, 100 == 10.0, 10 == 1.0, 0 == miss).

    ``distance_mm`` is the distance of the *pellet centre* from the target centre.
    """
    d = _validate_distance(distance_mm)
    if d > MAX_SCORING_DISTANCE_MM + _BOUNDARY_EPS:
        return 0
    k = math.ceil(d / DECIMAL_STEP_MM - _BOUNDARY_EPS)  # index of the 0.8 mm decimal zone, 1 = innermost
    k = max(k, 1)
    return 110 - k


def decimal_score(distance_mm: float) -> float:
    """Decimal score as a float rounded to one decimal (10.9 maximum, 0.0 for a miss)."""
    return decimal_score_tenths(distance_mm) / 10.0


def integer_score(distance_mm: float) -> int:
    """Full-ring score (10 … 1, 0 = miss). Defined as floor(decimal) so both scores always agree."""
    return decimal_score_tenths(distance_mm) // 10


def integer_score_from_rings(distance_mm: float) -> int:
    """Independent full-ring score computed directly from ring radii (used to cross-check ``integer_score``)."""
    d = _validate_distance(distance_mm)
    for ring in range(10, 0, -1):
        if d <= SCORING_ZONE_RADII_MM[ring] + _BOUNDARY_EPS:
            return ring
    return 0


def is_inner_ten(distance_mm: float) -> bool:
    return _validate_distance(distance_mm) <= INNER_TEN_ZONE_RADIUS_MM + _BOUNDARY_EPS


@dataclass(frozen=True)
class ShotScore:
    x_mm: float
    y_mm: float
    distance_mm: float
    decimal_tenths: int
    integer: int
    inner_ten: bool

    @property
    def decimal(self) -> float:
        return self.decimal_tenths / 10.0

    def as_dict(self) -> dict:
        return {
            "x_mm": self.x_mm, "y_mm": self.y_mm, "distance_mm": self.distance_mm,
            "decimal": self.decimal, "integer": self.integer, "inner_ten": self.inner_ten,
        }


def score_shot(x_mm: float, y_mm: float) -> ShotScore:
    """Score a simulated pellet centre at (x_mm, y_mm) in the target frame."""
    d = math.hypot(float(x_mm), float(y_mm))
    tenths = decimal_score_tenths(d)
    return ShotScore(float(x_mm), float(y_mm), d, tenths, tenths // 10, is_inner_ten(d))


def angular_size_rad(size_mm: float, distance_m: float = RANGE_DISTANCE_M) -> float:
    """Full angle subtended by a feature of ``size_mm`` centred on the line of sight at ``distance_m`` (DERIVED)."""
    return 2.0 * math.atan((size_mm / 2.0) / (distance_m * 1000.0))


def angular_size_deg(size_mm: float, distance_m: float = RANGE_DISTANCE_M) -> float:
    return math.degrees(angular_size_rad(size_mm, distance_m))
