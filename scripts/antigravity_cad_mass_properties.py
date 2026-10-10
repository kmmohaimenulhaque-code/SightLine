"""SIGHTLINE — Antigravity Mass Properties Solver

Computes total mass, centre of mass (COM), and optionally the inertia tensor
for the assembled grip instrument given:
  - A phone profile (JSON)
  - Chassis, adapter, and accessory component definitions
  - One or more ballast rails with configurable slider positions
  - Target mass/COM from a reference configuration (e.g. Steyr LP10)

The solver searches the ballast parameter space to minimise a weighted error
objective and reports feasible vs infeasible configurations honestly.

Coordinate system (SIGHTLINE grip datum):
  X — longitudinal, toward the target (positive forward)
  Y — lateral (positive left)
  Z — vertical (positive up)
  Origin: intersection of the adapter mating plane with the grip centreline

All masses in grams.  All distances in millimetres.
"""

from __future__ import annotations

import json
import math
import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Component:
    """A rigid body with known mass and COM in the chassis frame."""
    id: str
    mass_g: float
    com_x: float
    com_y: float
    com_z: float
    source: str = "CAD estimate"
    confidence: str = "ESTIMATED"  # MEASURED | SPECIFIED | ESTIMATED

    @property
    def moment(self) -> tuple[float, float, float]:
        return (self.mass_g * self.com_x,
                self.mass_g * self.com_y,
                self.mass_g * self.com_z)


@dataclass
class BallastRail:
    """A captive slider that can translate a ballast mass along one axis."""
    id: str
    ballast_mass_g: float
    axis: str = "x"            # "x", "y", or "z"
    min_pos: float = 0.0       # mm along that axis
    max_pos: float = 100.0
    fixed_other_1: float = 0.0  # position on the other two axes
    fixed_other_2: float = 0.0
    step_mm: float = 1.0       # search grid resolution

    def positions(self) -> list[float]:
        n = int(round((self.max_pos - self.min_pos) / self.step_mm)) + 1
        return [self.min_pos + i * self.step_mm for i in range(n)]

    def com_at(self, pos: float) -> tuple[float, float, float]:
        if self.axis == "x":
            return (pos, self.fixed_other_1, self.fixed_other_2)
        elif self.axis == "y":
            return (self.fixed_other_1, pos, self.fixed_other_2)
        else:
            return (self.fixed_other_1, self.fixed_other_2, pos)


@dataclass
class MassTarget:
    """Target mass properties to match.  TBD values are None."""
    reference_id: str = "Steyr_LP10"
    reference_mass_g: float = 1060.0
    target_mass_g: Optional[float] = 1060.0
    target_com_x_mm: Optional[float] = None  # TBD — no physical data
    target_com_y_mm: Optional[float] = 0.0
    target_com_z_mm: Optional[float] = None  # TBD
    mass_tolerance_g: float = 50.0            # ± band
    com_tolerance_mm: float = 5.0             # per axis
    # Inertia targets — TBD
    target_inertia_tensor: Optional[list] = None
    inertia_tolerance: Optional[float] = None


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------
@dataclass
class SolverResult:
    feasible: bool
    total_mass_g: float
    com: tuple[float, float, float]
    rail_positions: dict[str, float]
    target_error_mm: float
    mass_error_g: float
    com_error_per_axis: tuple[float, float, float]
    notes: str = ""


class MassPropertiesSolver:
    """Grid-search solver for ballast placement."""

    def __init__(self):
        self.components: list[Component] = []
        self.rails: list[BallastRail] = []
        self.target = MassTarget()

    def add_component(self, c: Component):
        self.components.append(c)

    def add_rail(self, r: BallastRail):
        self.rails.append(r)

    def set_target(self, t: MassTarget):
        self.target = t

    def _base_mass_moment(self):
        m = sum(c.mass_g for c in self.components)
        mx = sum(c.moment[0] for c in self.components)
        my = sum(c.moment[1] for c in self.components)
        mz = sum(c.moment[2] for c in self.components)
        return m, mx, my, mz

    def _com_error(self, com: tuple[float, float, float]) -> float:
        """Euclidean distance to target COM (only axes where target is known)."""
        err_sq = 0.0
        t = self.target
        if t.target_com_x_mm is not None:
            err_sq += (com[0] - t.target_com_x_mm) ** 2
        if t.target_com_y_mm is not None:
            err_sq += (com[1] - t.target_com_y_mm) ** 2
        if t.target_com_z_mm is not None:
            err_sq += (com[2] - t.target_com_z_mm) ** 2
        return math.sqrt(err_sq)

    def solve(self) -> SolverResult:
        base_m, base_mx, base_my, base_mz = self._base_mass_moment()

        if not self.rails:
            total = base_m
            if total <= 0:
                return SolverResult(False, 0, (0, 0, 0), {}, float("inf"),
                                    float("inf"), (0, 0, 0), "zero mass")
            com = (base_mx / total, base_my / total, base_mz / total)
            return SolverResult(
                feasible=True, total_mass_g=total, com=com, rail_positions={},
                target_error_mm=self._com_error(com),
                mass_error_g=abs(total - (self.target.target_mass_g or 0)),
                com_error_per_axis=self._per_axis_error(com))

        # Grid search over all rail position combinations
        position_lists = [r.positions() for r in self.rails]
        best_error = float("inf")
        best_result: Optional[SolverResult] = None

        for combo in itertools.product(*position_lists):
            rail_mass = sum(r.ballast_mass_g for r in self.rails)
            rail_mx = sum(r.ballast_mass_g * r.com_at(p)[0]
                          for r, p in zip(self.rails, combo))
            rail_my = sum(r.ballast_mass_g * r.com_at(p)[1]
                          for r, p in zip(self.rails, combo))
            rail_mz = sum(r.ballast_mass_g * r.com_at(p)[2]
                          for r, p in zip(self.rails, combo))

            total = base_m + rail_mass
            if total <= 0:
                continue
            com = ((base_mx + rail_mx) / total,
                   (base_my + rail_my) / total,
                   (base_mz + rail_mz) / total)

            # Weighted objective: COM error + mass error contribution
            com_err = self._com_error(com)
            mass_err = abs(total - (self.target.target_mass_g or 0))
            # Normalise mass error to mm-equivalent (1g ~ 0.1mm weight)
            obj = com_err + 0.1 * mass_err

            if obj < best_error:
                best_error = obj
                positions = {r.id: p for r, p in zip(self.rails, combo)}
                best_result = SolverResult(
                    feasible=True, total_mass_g=total, com=com,
                    rail_positions=positions,
                    target_error_mm=com_err, mass_error_g=mass_err,
                    com_error_per_axis=self._per_axis_error(com))

        if best_result is None:
            return SolverResult(False, 0, (0, 0, 0), {}, float("inf"),
                                float("inf"), (0, 0, 0),
                                "no feasible configuration found")
        return best_result

    def _per_axis_error(self, com):
        t = self.target
        ex = abs(com[0] - t.target_com_x_mm) if t.target_com_x_mm is not None else float("nan")
        ey = abs(com[1] - t.target_com_y_mm) if t.target_com_y_mm is not None else float("nan")
        ez = abs(com[2] - t.target_com_z_mm) if t.target_com_z_mm is not None else float("nan")
        return (ex, ey, ez)

    def attainable_range(self) -> dict:
        """Sweep each rail independently and report the achievable COM envelope."""
        base_m, base_mx, base_my, base_mz = self._base_mass_moment()
        rail_mass = sum(r.ballast_mass_g for r in self.rails)
        total = base_m + rail_mass
        if total <= 0:
            return {"error": "zero total mass"}

        results = {"total_mass_g": total, "rails": {}}
        for rail in self.rails:
            sweep = []
            other_rails_mx = sum(
                r.ballast_mass_g * r.com_at(r.min_pos)[0]
                for r in self.rails if r.id != rail.id)
            other_rails_my = sum(
                r.ballast_mass_g * r.com_at(r.min_pos)[1]
                for r in self.rails if r.id != rail.id)
            other_rails_mz = sum(
                r.ballast_mass_g * r.com_at(r.min_pos)[2]
                for r in self.rails if r.id != rail.id)

            for pos in rail.positions():
                rc = rail.com_at(pos)
                mx = base_mx + other_rails_mx + rail.ballast_mass_g * rc[0]
                my = base_my + other_rails_my + rail.ballast_mass_g * rc[1]
                mz = base_mz + other_rails_mz + rail.ballast_mass_g * rc[2]
                sweep.append({
                    "position_mm": pos,
                    "com_x": mx / total, "com_y": my / total,
                    "com_z": mz / total
                })
            results["rails"][rail.id] = {
                "axis": rail.axis,
                "min_pos": rail.min_pos,
                "max_pos": rail.max_pos,
                "ballast_mass_g": rail.ballast_mass_g,
                "com_at_min": sweep[0],
                "com_at_max": sweep[-1],
                "com_x_range": (sweep[0]["com_x"], sweep[-1]["com_x"]),
                "com_z_range": (sweep[0]["com_z"], sweep[-1]["com_z"]),
            }
        return results


# ---------------------------------------------------------------------------
# Phone profile loader
# ---------------------------------------------------------------------------
def load_phone_profile(path: str | Path) -> Component:
    """Load a phone profile JSON and return it as a Component in chassis coords."""
    with open(path) as f:
        p = json.load(f)
    tx = p.get("adapter_to_chassis_transform", {})
    off_x = tx.get("translation_mm", [0, 0, 0])[0]
    off_y = tx.get("translation_mm", [0, 0, 0])[1]
    off_z = tx.get("translation_mm", [0, 0, 0])[2]
    # Phone COM in body frame + adapter offset
    com_x = p.get("com_body_x", 0.0) + off_x
    com_y = p.get("com_body_y", 0.0) + off_y
    com_z = p.get("com_body_z", p["body_dims_mm"][0] / 2.0) + off_z
    return Component(
        id=p["id"], mass_g=p["mass_g"],
        com_x=com_x, com_y=com_y, com_z=com_z,
        source=p.get("mass_source", "profile"),
        confidence=p.get("mass_confidence", "ESTIMATED"))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="SIGHTLINE mass properties solver")
    parser.add_argument("--phone", default=None, help="Path to phone profile JSON")
    parser.add_argument("--target-mass", type=float, default=1060.0)
    parser.add_argument("--target-com-x", type=float, default=None)
    parser.add_argument("--target-com-z", type=float, default=None)
    args = parser.parse_args()

    solver = MassPropertiesSolver()

    # Default assembly components (G0 estimates)
    solver.add_component(Component("chassis_body", 280.0, 20.0, 0.0, -30.0,
                                   "CAD volume × PETG density", "ESTIMATED"))
    solver.add_component(Component("grip_handle", 120.0, -10.0, 0.0, -80.0,
                                   "CAD volume × PETG density", "ESTIMATED"))
    solver.add_component(Component("adapter_plate", 45.0, 0.0, 0.0, 5.0,
                                   "CAD volume × PETG density", "ESTIMATED"))
    solver.add_component(Component("fasteners_inserts", 25.0, 0.0, 0.0, -10.0,
                                   "M3 × 8 estimate", "ESTIMATED"))

    # Phone
    if args.phone:
        phone = load_phone_profile(args.phone)
    else:
        phone = Component("iPhone_15", 171.0, 0.0, 0.0, 73.8,
                          "Apple spec", "VERIFIED")
    solver.add_component(phone)

    # Ballast rails
    solver.add_rail(BallastRail(
        id="X_longitudinal", ballast_mass_g=200.0, axis="x",
        min_pos=-50.0, max_pos=70.0,
        fixed_other_1=0.0, fixed_other_2=-45.0, step_mm=1.0))
    solver.add_rail(BallastRail(
        id="Z_vertical", ballast_mass_g=100.0, axis="z",
        min_pos=-90.0, max_pos=-30.0,
        fixed_other_1=10.0, fixed_other_2=0.0, step_mm=2.0))

    # Target
    target = MassTarget(
        target_mass_g=args.target_mass,
        target_com_x_mm=args.target_com_x,
        target_com_z_mm=args.target_com_z)
    solver.set_target(target)

    # Solve
    result = solver.solve()
    print("=" * 70)
    print("SIGHTLINE Antigravity Mass Properties Solver — Result")
    print("=" * 70)
    print(f"  Phone:        {phone.id} ({phone.mass_g} g)")
    print(f"  Total mass:   {result.total_mass_g:.1f} g")
    print(f"  Achieved COM: X={result.com[0]:.2f}  Y={result.com[1]:.2f}  "
          f"Z={result.com[2]:.2f} mm")
    if target.target_com_x_mm is not None or target.target_com_z_mm is not None:
        print(f"  COM error:    {result.target_error_mm:.2f} mm "
              f"(per-axis: X={result.com_error_per_axis[0]:.2f}, "
              f"Y={result.com_error_per_axis[1]:.2f}, "
              f"Z={result.com_error_per_axis[2]:.2f})")
    print(f"  Mass error:   {result.mass_error_g:.1f} g from target "
          f"({target.target_mass_g} g)")
    print(f"  Rail settings: {result.rail_positions}")
    print()

    # Attainable range
    rng = solver.attainable_range()
    print("Attainable COM ranges (sweeping each rail independently):")
    for rid, info in rng.get("rails", {}).items():
        print(f"  {rid} ({info['axis']}-axis, {info['ballast_mass_g']}g): "
              f"COM_X {info['com_x_range'][0]:.1f}..{info['com_x_range'][1]:.1f}  "
              f"COM_Z {info['com_z_range'][0]:.1f}..{info['com_z_range'][1]:.1f}")
    print()

    # JSON output
    out = {
        "phone": phone.id,
        "total_mass_g": result.total_mass_g,
        "com_mm": list(result.com),
        "rail_positions": result.rail_positions,
        "target_error_mm": result.target_error_mm,
        "mass_error_g": result.mass_error_g,
        "feasible": result.feasible,
        "attainable_range": rng,
    }
    out_path = Path("cad/parametric/configurations") / f"antigravity_mass_report_{phone.id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Report written to {out_path}")


if __name__ == "__main__":
    main()

