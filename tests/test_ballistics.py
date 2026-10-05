"""Pellet-drop arithmetic behind decision D-005 (no drop term in the simulated impact)."""

import pytest

from app.scoring import ballistics as b


def test_free_fall_drop_at_160_mps():
    assert b.free_fall_drop_mm(10.0, 160.0) == pytest.approx(19.15, abs=0.01)


def test_concept_claim_of_2_mm_drop_is_not_plausible():
    # Any plausible air-pistol muzzle speed gives more than 12 mm of drop below the bore line over 10 m.
    for v in (120.0, 150.0, 175.0, 200.0):
        assert b.free_fall_drop_mm(10.0, v) > 12.0
    assert b.speed_for_drop_mps(10.0, 2.0) == pytest.approx(495.1, abs=0.1)


def test_net_drop_is_zero_at_the_zero_distance_and_negligible_within_range_tolerance():
    assert b.drop_relative_to_zeroed_sight_line_mm(10.0, 10.0, 160.0) == pytest.approx(0.0, abs=1e-12)
    for d in (9.95, 10.05):
        assert abs(b.drop_relative_to_zeroed_sight_line_mm(d, 10.0, 160.0)) < 0.1


def test_invalid_inputs():
    with pytest.raises(ValueError):
        b.time_of_flight_s(10.0, 0.0)
    with pytest.raises(ValueError):
        b.speed_for_drop_mps(10.0, 0.0)
