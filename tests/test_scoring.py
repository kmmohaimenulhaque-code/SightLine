"""ISSF geometry constants and scoring rules (FUN-01)."""

import math

import pytest

from app.scoring import issf


def test_ring_diameters_match_issf_gtr_6_3_4_6():
    assert issf.RING_DIAMETERS_MM == {
        10: 11.5, 9: 27.5, 8: 43.5, 7: 59.5, 6: 75.5, 5: 91.5, 4: 107.5, 3: 123.5, 2: 139.5, 1: 155.5}
    assert issf.INNER_TEN_DIAMETER_MM == 5.0
    assert issf.BLACK_AIMING_MARK_DIAMETER_MM == issf.RING_DIAMETERS_MM[7] == 59.5
    assert issf.PELLET_DIAMETER_MM == 4.5


def test_ring_pitch_is_exactly_8_mm_everywhere():
    radii = issf.RING_RADII_MM
    for n in range(10, 1, -1):
        assert radii[n - 1] - radii[n] == pytest.approx(8.0, abs=1e-12)
    assert issf.RING_PITCH_MM == pytest.approx(8.0)
    assert issf.DECIMAL_STEP_MM == pytest.approx(0.8)
    assert issf.EST_ACCURACY_REQUIREMENT_MM == pytest.approx(0.4)


def test_scoring_zone_radii():
    assert issf.SCORING_ZONE_RADII_MM[10] == pytest.approx(8.0)
    assert issf.SCORING_ZONE_RADII_MM[9] == pytest.approx(16.0)
    assert issf.SCORING_ZONE_RADII_MM[1] == pytest.approx(80.0)
    assert issf.INNER_TEN_ZONE_RADIUS_MM == pytest.approx(4.75)


@pytest.mark.parametrize(
    "d, tenths",
    [
        (0.0, 109), (0.8, 109), (0.8 + 1e-6, 108), (4.0, 105), (7.2, 101), (7.2 + 1e-6, 100),
        (8.0, 100), (8.0 + 1e-6, 99), (16.0, 90), (16.0 + 1e-6, 89), (79.2, 11), (79.2 + 1e-6, 10),
        (80.0, 10), (80.0 + 1e-6, 0), (500.0, 0),
    ],
)
def test_decimal_score_boundaries_touching_scores_higher(d, tenths):
    assert issf.decimal_score_tenths(d) == tenths


def test_integer_score_agrees_with_ring_radii_away_from_boundaries():
    d = 0.0005
    while d < 90.0:
        assert issf.integer_score(d) == issf.integer_score_from_rings(d), d
        d += 0.0731  # irrational-ish stride, never exactly on a boundary


def test_inner_ten():
    assert issf.is_inner_ten(4.75)
    assert not issf.is_inner_ten(4.75 + 1e-6)


def test_score_shot():
    s = issf.score_shot(3.0, 4.0)
    assert s.distance_mm == pytest.approx(5.0)
    assert s.decimal == pytest.approx(10.3)
    assert s.integer == 10
    assert not s.inner_ten
    centre = issf.score_shot(0.0, 0.0)
    assert centre.decimal == pytest.approx(10.9) and centre.inner_ten


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_invalid_distance_rejected(bad):
    with pytest.raises(ValueError):
        issf.decimal_score_tenths(bad)


def test_angular_sizes_and_the_0891_degree_claim():
    # The concept document attributed 0.891 deg to the black; it is the 1-ring (VALIDATION.md C-012).
    assert issf.angular_size_deg(59.5) == pytest.approx(0.3409, abs=1e-4)
    assert issf.angular_size_deg(155.5) == pytest.approx(0.8909, abs=1e-4)
    assert math.isclose(issf.angular_size_rad(11.5), 1.15e-3, rel_tol=1e-6)
