"""Mass properties and ballast search for the SIGHTLINE G0 instrument.

This module is deliberately independent of a CAD kernel.  It is the numerical
ledger used by the editable CAD configurations, not a substitute for weighing
printed parts.  All coordinates are millimetres in the chassis frame and all
masses are grams.  The chassis frame is right handed:

    X = targetward, Y = lateral, Z = vertical

Component masses and centres carry provenance and an evidence class.  A
``manufacturer_specified`` or ``estimated`` value is never silently promoted
to a physical measurement.  The CLI writes a JSON report with the best
feasible candidate, attainable ranges, residuals and the evidence warnings.

Examples::

    python scripts/cad_mass_properties.py \
      --config cad/parametric/configurations/iphone15_mass.json
    python scripts/cad_mass_properties.py \
      --config cad/parametric/configurations/placeholder_android_mass.json \
      --out /tmp/android_mass.json

The JSON schema is intentionally small and human-editable.  An example is in
``cad/parametric/configurations/iphone15_mass.json``.  Optional inertia tensors
are component tensors about the component COM, in g mm^2.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
ZERO = (0.0, 0.0, 0.0)
Vec = tuple[float, float, float]
Mat = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if positive and result <= 0:
        raise ValueError(f"{label} must be positive")
    return result


def _vec(value: Sequence[Any], label: str) -> Vec:
    if len(value) != 3:
        raise ValueError(f"{label} must have three values")
    return tuple(_number(item, f"{label}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]


def _mat(value: Sequence[Sequence[Any]], label: str) -> Mat:
    if len(value) != 3 or any(len(row) != 3 for row in value):
        raise ValueError(f"{label} must be a 3x3 matrix")
    return tuple(tuple(_number(item, f"{label}[{i}][{j}]") for j, item in enumerate(row)) for i, row in enumerate(value))  # type: ignore[return-value]


def add(a: Vec, b: Vec) -> Vec:
    return tuple(x + y for x, y in zip(a, b))  # type: ignore[return-value]


def sub(a: Vec, b: Vec) -> Vec:
    return tuple(x - y for x, y in zip(a, b))  # type: ignore[return-value]


def scale(a: Vec, factor: float) -> Vec:
    return tuple(factor * x for x in a)  # type: ignore[return-value]


def dot(a: Vec, b: Vec) -> float:
    return sum(x * y for x, y in zip(a, b))


def mat_vec(matrix: Mat, vector: Vec) -> Vec:
    return tuple(sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def mat_mul(a: Mat, b: Mat) -> Mat:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))  # type: ignore[return-value]


def transpose(matrix: Mat) -> Mat:
    return tuple(tuple(matrix[j][i] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def mat_add(a: Mat, b: Mat) -> Mat:
    return tuple(tuple(a[i][j] + b[i][j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def mat_sub(a: Mat, b: Mat) -> Mat:
    return tuple(tuple(a[i][j] - b[i][j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def skew(vector: Vec) -> Mat:
    x, y, z = vector
    return ((0.0, -z, y), (z, 0.0, -x), (-y, x, 0.0))


def parallel_axis(mass_g: float, offset_mm: Vec) -> Mat:
    """Return m (|r|^2 I - r r^T) for an offset from COM to the origin."""
    rr = dot(offset_mm, offset_mm)
    return tuple(tuple(mass_g * (rr * (1.0 if i == j else 0.0) - offset_mm[i] * offset_mm[j]) for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _round_vec(vector: Vec) -> list[float]:
    return [round(value, 9) for value in vector]


def _round_mat(matrix: Mat) -> list[list[float]]:
    return [[round(value, 9) for value in row] for row in matrix]


@dataclass(frozen=True)
class Transform:
    rotation: Mat = IDENTITY
    translation_mm: Vec = ZERO

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "Transform":
        value = value or {}
        rotation = _mat(value.get("rotation", IDENTITY), "transform.rotation")
        translation = _vec(value.get("translation_mm", ZERO), "transform.translation_mm")
        # A rigid transform must preserve handedness and length.  A generous
        # tolerance is appropriate for hand-edited configuration matrices.
        columns = tuple(tuple(rotation[row][column] for row in range(3)) for column in range(3))
        if any(abs(dot(column, column) - 1.0) > 1e-5 for column in columns):
            raise ValueError("transform.rotation columns must be unit length")
        if abs(dot(columns[0], columns[1])) > 1e-5 or abs(dot(columns[0], columns[2])) > 1e-5 or abs(dot(columns[1], columns[2])) > 1e-5:
            raise ValueError("transform.rotation columns must be orthogonal")
        return cls(rotation, translation)

    def point(self, local_point: Vec) -> Vec:
        return add(mat_vec(self.rotation, local_point), self.translation_mm)


@dataclass(frozen=True)
class Component:
    id: str
    mass_g: float
    com_mm: Vec
    transform: Transform
    source: str
    confidence: str
    value_status: str
    inertia_tensor_g_mm2: Mat | None = None
    role: str = "component"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Component":
        identifier = str(value.get("id", ""))
        if not identifier or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for character in identifier):
            raise ValueError("component id must be a non-empty safe identifier")
        mass = _number(value.get("mass_g"), f"{identifier}.mass_g")
        if mass < 0:
            raise ValueError(f"{identifier}.mass_g must not be negative")
        inertia_value = value.get("inertia_tensor_g_mm2")
        inertia = _mat(inertia_value, f"{identifier}.inertia_tensor_g_mm2") if inertia_value is not None else None
        return cls(
            id=identifier,
            mass_g=mass,
            com_mm=_vec(value.get("com_mm", ZERO), f"{identifier}.com_mm"),
            transform=Transform.from_dict(value.get("transform")),
            source=str(value.get("source", "unspecified")),
            confidence=str(value.get("confidence", "UNVERIFIED")),
            value_status=str(value.get("value_status", "estimated")),
            inertia_tensor_g_mm2=inertia,
            role=str(value.get("role", "component")),
        )

    @property
    def chassis_com_mm(self) -> Vec:
        return self.transform.point(self.com_mm)

    @property
    def inertia_about_chassis_origin(self) -> Mat:
        local = self.inertia_tensor_g_mm2 or ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        rotated = mat_mul(mat_mul(self.transform.rotation, local), transpose(self.transform.rotation))
        return mat_add(rotated, parallel_axis(self.mass_g, self.chassis_com_mm))

    def as_report(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "mass_g": self.mass_g,
            "component_com_mm": _round_vec(self.com_mm),
            "chassis_com_mm": _round_vec(self.chassis_com_mm),
            "source": self.source,
            "confidence": self.confidence,
            "value_status": self.value_status,
            "inertia_tensor_provided": self.inertia_tensor_g_mm2 is not None,
        }


@dataclass(frozen=True)
class BallastSpec:
    id: str
    mass_g: float
    axis: str
    position_mm: Vec
    travel_min_mm: float
    travel_max_mm: float
    step_mm: float
    source: str
    confidence: str
    value_status: str
    inertia_tensor_g_mm2: Mat | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BallastSpec":
        identifier = str(value.get("id", ""))
        axis = str(value.get("axis", ""))
        if not identifier or axis not in {"X", "Y", "Z"}:
            raise ValueError("ballast id and axis (X, Y or Z) are required")
        travel = value.get("travel_mm")
        if not isinstance(travel, Sequence) or len(travel) != 2:
            raise ValueError(f"{identifier}.travel_mm must be [min, max]")
        low, high = (_number(travel[0], f"{identifier}.travel_mm[0]"), _number(travel[1], f"{identifier}.travel_mm[1]"))
        step = _number(value.get("step_mm"), f"{identifier}.step_mm", positive=True)
        if high < low:
            raise ValueError(f"{identifier}.travel_mm max must be >= min")
        inertia_value = value.get("inertia_tensor_g_mm2")
        return cls(
            id=identifier,
            mass_g=_number(value.get("mass_g"), f"{identifier}.mass_g", positive=True),
            axis=axis,
            position_mm=_vec(value.get("position_mm", ZERO), f"{identifier}.position_mm"),
            travel_min_mm=low,
            travel_max_mm=high,
            step_mm=step,
            source=str(value.get("source", "unspecified")),
            confidence=str(value.get("confidence", "UNVERIFIED")),
            value_status=str(value.get("value_status", "estimated")),
            inertia_tensor_g_mm2=_mat(inertia_value, f"{identifier}.inertia_tensor_g_mm2") if inertia_value is not None else None,
        )

    def positions(self) -> list[float]:
        count = int(math.floor((self.travel_max_mm - self.travel_min_mm) / self.step_mm + 1e-9))
        values = [self.travel_min_mm + index * self.step_mm for index in range(count + 1)]
        if not values or values[-1] < self.travel_max_mm - 1e-8:
            values.append(self.travel_max_mm)
        values[-1] = self.travel_max_mm if abs(values[-1] - self.travel_max_mm) < 1e-8 else values[-1]
        return [round(value, 9) for value in values]

    def component_at(self, position: float) -> Component:
        coordinates = list(self.position_mm)
        coordinates["XYZ".index(self.axis)] = position
        return Component(
            id=self.id,
            role="ballast",
            mass_g=self.mass_g,
            com_mm=tuple(coordinates),
            transform=Transform(),
            source=self.source,
            confidence=self.confidence,
            value_status=self.value_status,
            inertia_tensor_g_mm2=self.inertia_tensor_g_mm2,
        )


def _resolve(base: Path, reference: str) -> Path:
    candidate = Path(reference)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_model(path: Path, *, phone_mass_override: float | None = None) -> tuple[dict[str, Any], list[Component], list[BallastSpec]]:
    document = load_json(path)
    if document.get("schema_version") != 1:
        raise ValueError("mass-property configuration schema_version must be 1")
    components = [Component.from_dict(item) for item in document.get("components", [])]
    if not components:
        raise ValueError("mass-property configuration must contain components")
    ids = [component.id for component in components]
    if len(ids) != len(set(ids)):
        raise ValueError("component ids must be unique")
    if phone_mass_override is not None:
        phone_id = str(document.get("phone_component_id", "phone"))
        replacement = _number(phone_mass_override, "phone mass override", positive=True)
        components = [
            Component(**{**component.__dict__, "mass_g": replacement, "value_status": "user_measured_or_entered"})
            if component.id == phone_id else component for component in components
        ]
    ballast = [BallastSpec.from_dict(item) for item in document.get("ballast", [])]
    ballast_ids = [item.id for item in ballast]
    if len(ballast_ids) != len(set(ballast_ids)) or set(ids) & set(ballast_ids):
        raise ValueError("component and ballast ids must be unique")
    profile = document.get("phone_profile")
    if profile:
        profile_path = _resolve(path.parent, str(profile))
        if not profile_path.exists():
            raise ValueError(f"phone profile not found: {profile_path}")
        document["phone_profile_resolved"] = str(profile_path.relative_to(ROOT) if profile_path.is_relative_to(ROOT) else profile_path)
        document["phone_profile_data"] = load_json(profile_path)
    return document, components, ballast


def evaluate(components: Sequence[Component]) -> dict[str, Any]:
    total_mass = sum(component.mass_g for component in components)
    if total_mass <= 0:
        raise ValueError("total mass must be positive")
    first_moment = (0.0, 0.0, 0.0)
    inertia_origin: Mat = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    for component in components:
        first_moment = add(first_moment, scale(component.chassis_com_mm, component.mass_g))
        inertia_origin = mat_add(inertia_origin, component.inertia_about_chassis_origin)
    centre = scale(first_moment, 1.0 / total_mass)
    inertia_at_com = mat_sub(inertia_origin, parallel_axis(total_mass, centre))
    return {
        "total_mass_g": total_mass,
        "com_mm": centre,
        "inertia_tensor_about_chassis_origin_g_mm2": inertia_origin,
        "inertia_tensor_about_total_com_g_mm2": inertia_at_com,
    }


def _target_vector(target: dict[str, Any]) -> Vec | None:
    value = target.get("target_com_mm")
    return None if value is None else _vec(value, "target.target_com_mm")


def _objective(metrics: dict[str, Any], target: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    details: dict[str, Any] = {}
    score = 0.0
    target_mass = target.get("target_mass_g")
    mass_tolerance = target.get("mass_tolerance_g")
    if target_mass is not None:
        target_mass = _number(target_mass, "target.target_mass_g", positive=True)
        residual = metrics["total_mass_g"] - target_mass
        tolerance = _number(mass_tolerance, "target.mass_tolerance_g", positive=True) if mass_tolerance is not None else 1.0
        details["mass_residual_g"] = residual
        details["mass_normalized_error"] = residual / tolerance
        score += (residual / tolerance) ** 2
    target_com = _target_vector(target)
    if target_com is not None:
        com_tolerance = target.get("com_tolerance_mm")
        tolerance_vector = _vec(com_tolerance, "target.com_tolerance_mm") if isinstance(com_tolerance, Sequence) and not isinstance(com_tolerance, (str, bytes)) else None
        scalar_tolerance = _number(com_tolerance, "target.com_tolerance_mm", positive=True) if com_tolerance is not None and tolerance_vector is None else 1.0
        residual = sub(metrics["com_mm"], target_com)
        normalized = tuple(residual[i] / (tolerance_vector[i] if tolerance_vector else scalar_tolerance) for i in range(3))
        details["com_residual_mm"] = residual
        details["com_normalized_error"] = normalized
        score += sum(value * value for value in normalized)
    inertia_target = target.get("target_inertia_tensor_g_mm2")
    if inertia_target is not None:
        expected = _mat(inertia_target, "target.target_inertia_tensor_g_mm2")
        residual_matrix = mat_sub(metrics["inertia_tensor_about_total_com_g_mm2"], expected)
        tolerance = _number(target.get("inertia_tolerance"), "target.inertia_tolerance", positive=True)
        norm = math.sqrt(sum(residual_matrix[i][j] ** 2 for i in range(3) for j in range(3))) / tolerance
        details["inertia_frobenius_residual_g_mm2"] = residual_matrix
        details["inertia_normalized_error"] = norm
        score += norm * norm
    return score, details


def _within_targets(metrics: dict[str, Any], target: dict[str, Any]) -> bool:
    target_mass = target.get("target_mass_g")
    if target_mass is not None:
        tolerance = _number(target.get("mass_tolerance_g"), "target.mass_tolerance_g", positive=True)
        if abs(metrics["total_mass_g"] - _number(target_mass, "target.target_mass_g")) > tolerance + 1e-9:
            return False
    target_com = _target_vector(target)
    if target_com is not None:
        tolerance = target.get("com_tolerance_mm")
        if tolerance is None:
            return False
        limits = _vec(tolerance, "target.com_tolerance_mm") if isinstance(tolerance, Sequence) and not isinstance(tolerance, (str, bytes)) else (float(tolerance),) * 3
        if any(abs(metrics["com_mm"][i] - target_com[i]) > _number(limits[i], "target.com_tolerance_mm", positive=True) + 1e-9 for i in range(3)):
            return False
    if target.get("target_inertia_tensor_g_mm2") is not None:
        tolerance = _number(target.get("inertia_tolerance"), "target.inertia_tolerance", positive=True)
        expected = _mat(target["target_inertia_tensor_g_mm2"], "target.target_inertia_tensor_g_mm2")
        actual = metrics["inertia_tensor_about_total_com_g_mm2"]
        residual = math.sqrt(sum((actual[i][j] - expected[i][j]) ** 2 for i in range(3) for j in range(3)))
        if residual > tolerance + 1e-9:
            return False
    return True


def solve(document: dict[str, Any], components: Sequence[Component], ballast: Sequence[BallastSpec]) -> dict[str, Any]:
    target = document.get("target", {})
    if not isinstance(target, dict):
        raise ValueError("target must be an object")
    position_sets = [item.positions() for item in ballast]
    combinations = itertools.product(*position_sets) if position_sets else [()]
    best: dict[str, Any] | None = None
    best_position_key: tuple[float, ...] | None = None
    feasible: list[dict[str, Any]] = []
    ranges: list[list[float]] | None = None
    mass_range = [math.inf, -math.inf]
    confidence_classes: set[str] = {component.confidence for component in components}
    confidence_classes.update(item.confidence for item in ballast)
    search_count = 0
    for positions in combinations:
        selected = list(components) + [spec.component_at(position) for spec, position in zip(ballast, positions)]
        metrics = evaluate(selected)
        score, residuals = _objective(metrics, target)
        if ranges is None:
            ranges = [[metrics["com_mm"][i], metrics["com_mm"][i]] for i in range(3)]
        else:
            for i in range(3):
                ranges[i][0] = min(ranges[i][0], metrics["com_mm"][i])
                ranges[i][1] = max(ranges[i][1], metrics["com_mm"][i])
        mass_range[0] = min(mass_range[0], metrics["total_mass_g"])
        mass_range[1] = max(mass_range[1], metrics["total_mass_g"])
        candidate = {
            "ballast_positions_mm": {spec.id: position for spec, position in zip(ballast, positions)},
            "metrics": metrics,
            "objective": score,
            "residuals": residuals,
            "components": [component.as_report() for component in selected],
        }
        position_key = tuple(float(position) for position in positions)
        if best is None or score < best["objective"] - 1e-12 or (abs(score - best["objective"]) <= 1e-12 and (best_position_key is None or position_key < best_position_key)):
            best = candidate
            best_position_key = position_key
        if _within_targets(metrics, target):
            feasible.append(candidate)
        search_count += 1
    if best is None or ranges is None:
        raise ValueError("ballast search produced no candidates")
    unknown_targets = []
    for key in ("reference_mass_g", "target_com_mm", "target_inertia_tensor_g_mm2"):
        if target.get(key) is None:
            unknown_targets.append(key)
    warnings = [
        "CAD and manufacturer values are predictions until the printed assembly and installed hardware are weighed.",
        "A feasible mathematical target is not evidence of ergonomic equivalence or optical repeatability.",
    ]
    if unknown_targets:
        warnings.append("Unknown target fields: " + ", ".join(unknown_targets) + ".")
    if any(status not in {"measured", "user_measured_or_entered"} for status in (component.value_status for component in components)):
        warnings.append("At least one fixed component mass is not a physical measurement.")
    report_best = best
    # Convert tuples to JSON-friendly values at the report boundary.
    def normalise(value: Any) -> Any:
        if isinstance(value, tuple):
            return [normalise(item) for item in value]
        if isinstance(value, list):
            return [normalise(item) for item in value]
        if isinstance(value, dict):
            return {key: normalise(item) for key, item in value.items()}
        if isinstance(value, float):
            return round(value, 9)
        return value
    profile_data = document.get("phone_profile_data") if isinstance(document.get("phone_profile_data"), dict) else {}
    profile_summary = {
        key: profile_data.get(key)
        for key in ("id", "label", "variant", "body_mm", "case_allowance_mm", "mass_g", "mass_status", "camera_status", "adapter_id")
        if key in profile_data
    }
    return normalise({
        "report_schema_version": 1,
        "model_id": document.get("id", "unidentified"),
        "profile_id": document.get("phone_profile_data", {}).get("id") if isinstance(document.get("phone_profile_data"), dict) else document.get("profile_id"),
        "profile_summary": profile_summary,
        "status": "MODEL_OUTPUT",
        "units": {"mass": "g", "length": "mm", "inertia": "g mm^2"},
        "frame": "chassis: X targetward, Y lateral, Z vertical; origin is underside chassis centreline per cad/parametric/assembly.json",
        "target": target,
        "target_interpretation": document.get("target_interpretation", "PROVISIONAL product-design target; not an LP10 mass-property measurement"),
        "search": {"candidate_count": search_count, "feasible_count": len(feasible), "best_is_feasible": not feasible == [] and _within_targets(best["metrics"], target)},
        "best_candidate": report_best,
        "attainable_ranges": {"total_mass_g": mass_range, "com_mm": ranges},
        "unknown_targets": unknown_targets,
        "confidence_classes": sorted(confidence_classes),
        "warnings": warnings,
        "solver": {"objective": "sum of squared normalized residuals for known mass, COM and inertia targets", "enumeration": "inclusive endpoints and configured position increment"},
    })


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="mass-property JSON configuration")
    parser.add_argument("--out", type=Path, default=None, help="optional JSON report destination")
    parser.add_argument("--phone-mass", type=float, default=None, help="override the phone component mass in grams")
    args = parser.parse_args(argv)
    try:
        document, components, ballast = load_model(args.config.resolve(), phone_mass_override=args.phone_mass)
        report = solve(document, components, ballast)
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8", newline="\n")
        print(payload, end="")
        return 0
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"mass-property solve failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
