"""Tests for the Antigravity mass-properties solver."""

import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.antigravity_cad_mass_properties import (
    Component, BallastRail, MassTarget, MassPropertiesSolver, load_phone_profile
)


# ---- Arithmetic tests ----

def test_single_component_com():
    """COM of a single component is the component's own COM."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("A", 100.0, 10.0, 20.0, 30.0))
    result = solver.solve()
    assert result.feasible
    assert result.total_mass_g == 100.0
    assert abs(result.com[0] - 10.0) < 1e-9
    assert abs(result.com[1] - 20.0) < 1e-9
    assert abs(result.com[2] - 30.0) < 1e-9


def test_two_component_com():
    """COM of two equal-mass components is their midpoint."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("A", 100.0, 0.0, 0.0, 0.0))
    solver.add_component(Component("B", 100.0, 100.0, 0.0, 0.0))
    result = solver.solve()
    assert abs(result.com[0] - 50.0) < 1e-9
    assert result.total_mass_g == 200.0


def test_unequal_mass_com():
    """COM with unequal masses: m1=300g at x=0, m2=100g at x=100 → COM at x=25."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("A", 300.0, 0.0, 0.0, 0.0))
    solver.add_component(Component("B", 100.0, 100.0, 0.0, 0.0))
    result = solver.solve()
    assert abs(result.com[0] - 25.0) < 1e-9


# ---- Rail solver tests ----

def test_rail_shifts_com():
    """A ballast on a rail should shift COM."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("chassis", 400.0, 0.0, 0.0, 0.0))
    solver.add_rail(BallastRail("X", 200.0, "x", 0.0, 100.0, 0.0, 0.0, 1.0))
    solver.set_target(MassTarget(target_com_x_mm=30.0, target_com_y_mm=0.0,
                                 target_com_z_mm=0.0))
    result = solver.solve()
    assert result.feasible
    # With 400g at x=0 and 200g at x=pos: COM = 200*pos/600 = pos/3
    # To get COM=30, pos=90
    assert abs(result.rail_positions["X"] - 90.0) < 1.5  # within grid step


def test_two_rails():
    """Two independent rails (X and Z) both find optimal positions."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("chassis", 400.0, 0.0, 0.0, 0.0))
    solver.add_rail(BallastRail("X", 100.0, "x", -50.0, 50.0, 0.0, 0.0, 1.0))
    solver.add_rail(BallastRail("Z", 100.0, "z", -50.0, 50.0, 0.0, 0.0, 2.0))
    solver.set_target(MassTarget(target_com_x_mm=10.0, target_com_y_mm=0.0,
                                 target_com_z_mm=10.0))
    result = solver.solve()
    assert result.feasible
    # Check the solver found positions that move COM toward target
    assert result.com[0] > 0  # moved forward
    assert result.com[2] > 0  # moved up


def test_infeasible_mass_reported():
    """When total mass can't reach target, mass_error_g is reported honestly."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("tiny", 50.0, 0.0, 0.0, 0.0))
    solver.set_target(MassTarget(target_mass_g=2000.0))
    result = solver.solve()
    assert result.mass_error_g > 1900.0  # nowhere near


# ---- Phone profile tests ----

def test_load_iphone_profile():
    """Load the iPhone 15 profile and verify mass."""
    path = os.path.join(os.path.dirname(__file__), "..",
                        "cad/parametric/phone_profiles/antigravity_iphone15.json")
    if not os.path.exists(path):
        return  # skip if file missing in CI
    comp = load_phone_profile(path)
    assert comp.id == "iPhone_15"
    assert comp.mass_g == 171.0
    assert comp.confidence == "VERIFIED"


def test_load_android_profile():
    """Load the Android placeholder profile and verify it's marked UNVERIFIED."""
    path = os.path.join(os.path.dirname(__file__), "..",
                        "cad/parametric/phone_profiles/antigravity_android_reference.json")
    if not os.path.exists(path):
        return
    comp = load_phone_profile(path)
    assert comp.id == "Android_Reference_Placeholder"
    assert comp.mass_g == 190.0
    assert comp.confidence == "UNVERIFIED"


def test_two_phones_same_chassis():
    """Same chassis + rails with two different phones produces different COM."""
    solver1 = MassPropertiesSolver()
    solver1.add_component(Component("chassis", 400.0, 0.0, 0.0, 0.0))
    solver1.add_component(Component("phone1", 171.0, 0.0, 0.0, 70.0))
    solver1.add_rail(BallastRail("X", 200.0, "x", -50.0, 50.0, 0.0, -40.0, 1.0))

    solver2 = MassPropertiesSolver()
    solver2.add_component(Component("chassis", 400.0, 0.0, 0.0, 0.0))
    solver2.add_component(Component("phone2", 220.0, 0.0, 0.0, 80.0))
    solver2.add_rail(BallastRail("X", 200.0, "x", -50.0, 50.0, 0.0, -40.0, 1.0))

    r1 = solver1.solve()
    r2 = solver2.solve()
    # Different phones → different total mass
    assert r1.total_mass_g != r2.total_mass_g
    # But both are feasible on the same chassis
    assert r1.feasible and r2.feasible


# ---- Attainable range ----

def test_attainable_range():
    """Attainable range sweep runs and reports rail info."""
    solver = MassPropertiesSolver()
    solver.add_component(Component("chassis", 400.0, 0.0, 0.0, 0.0))
    solver.add_rail(BallastRail("X", 200.0, "x", -50.0, 50.0, 0.0, 0.0, 5.0))
    rng = solver.attainable_range()
    assert "X" in rng["rails"]
    info = rng["rails"]["X"]
    assert info["com_at_min"]["com_x"] < info["com_at_max"]["com_x"]


# ---- Coordinate transform consistency ----

def test_moment_calculation():
    """Component.moment returns mass * position."""
    c = Component("test", 250.0, 10.0, -5.0, 20.0)
    assert c.moment == (2500.0, -1250.0, 5000.0)

