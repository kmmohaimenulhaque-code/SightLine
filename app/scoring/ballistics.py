"""Pellet-drop arithmetic used to evaluate the concept document's ballistic claim.

Status: DERIVED. Point mass, flat fire, **no drag**. Drag only lengthens the time of flight, so the free-fall values
are lower bounds on the drop below the bore line. This module exists to document why SIGHTLINE's simulated impact has
no drop term (ARCHITECTURE.md D-005); it is not used by the scoring pipeline.
"""

from __future__ import annotations

import math

STANDARD_GRAVITY_MPS2 = 9.80665


def time_of_flight_s(distance_m: float, speed_mps: float) -> float:
    if distance_m < 0 or speed_mps <= 0:
        raise ValueError("distance must be >= 0 and speed > 0")
    return distance_m / speed_mps


def free_fall_drop_mm(distance_m: float, speed_mps: float, g: float = STANDARD_GRAVITY_MPS2) -> float:
    """Drop below the bore line after ``distance_m`` (no drag; lower bound)."""
    t = time_of_flight_s(distance_m, speed_mps)
    return 0.5 * g * t * t * 1000.0


def speed_for_drop_mps(distance_m: float, drop_mm: float, g: float = STANDARD_GRAVITY_MPS2) -> float:
    """Muzzle speed at which the no-drag drop over ``distance_m`` equals ``drop_mm``."""
    if drop_mm <= 0:
        raise ValueError("drop must be > 0")
    return distance_m / math.sqrt(2.0 * (drop_mm / 1000.0) / g)


def drop_relative_to_zeroed_sight_line_mm(
    distance_m: float, zero_distance_m: float, speed_mps: float, g: float = STANDARD_GRAVITY_MPS2
) -> float:
    """Vertical offset of the trajectory from a sight line zeroed at ``zero_distance_m`` (positive = low).

    Small-angle, no drag: offset(d) = drop(d) - (d / Z) * drop(Z) = 0.5 * g * d * (d - Z) / v^2.
    Zero at d == Z by construction.
    """
    if zero_distance_m <= 0:
        raise ValueError("zero distance must be > 0")
    return 0.5 * g * distance_m * (distance_m - zero_distance_m) / (speed_mps * speed_mps) * 1000.0
