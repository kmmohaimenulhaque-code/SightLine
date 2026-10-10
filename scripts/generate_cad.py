"""Dependency-free G0 solid generator. Source of truth: cad/parametric/assembly.json.

Generate: python scripts/generate_cad.py --config cad/parametric/configurations/iphone15_g0.json
Validate without writing: append --validate-only. Verify existing exports: --check-exports DIR.
All lengths are millimetres. Geometric volumes are NOT measured mass or fit evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "cad/parametric/configurations/iphone15_g0.json"
EPS = 1e-7
Vec = tuple[float, float, float]
Box = tuple[Vec, Vec]


def box(x0, x1, y0, y1, z0, z1) -> Box:
    result = ((float(x0), float(y0), float(z0)), (float(x1), float(y1), float(z1)))
    if not all(math.isfinite(v) for p in result for v in p):
        raise ValueError("non-finite box coordinate")
    if any(b - a <= EPS for a, b in zip(*result)):
        raise ValueError(f"degenerate box: {result}")
    return result


def intersects(a: Box, b: Box) -> bool:
    """Strict positive-volume intersection; surface contact is permitted."""
    return all(min(a[1][i], b[1][i]) - max(a[0][i], b[0][i]) > EPS for i in range(3))


def contains(b: Box, p: Vec) -> bool:
    return all(b[0][i] < p[i] < b[1][i] for i in range(3))


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def sub(a: Vec, b: Vec) -> Vec:
    return tuple(x-y for x, y in zip(a, b))


@dataclass
class Mesh:
    vertices: list[Vec]
    triangles: list[tuple[int, int, int]]

    @property
    def bounds(self) -> Box:
        return tuple(tuple(fn(p[i] for p in self.vertices) for i in range(3)) for fn in (min, max))

    @property
    def volume(self) -> float:
        # Translation reduces cancellation for parts far from the origin.
        origin = self.vertices[0]
        return sum(sum(a*b for a, b in zip(sub(self.vertices[i], origin),
                   cross(sub(self.vertices[j], origin), sub(self.vertices[k], origin))))
                   for i, j, k in self.triangles) / 6

    def validate(self) -> dict:
        edges = Counter()
        directed = Counter()
        adjacency = defaultdict(set)
        links = defaultdict(lambda: defaultdict(set))
        for i, j, k in self.triangles:
            n = cross(sub(self.vertices[j], self.vertices[i]), sub(self.vertices[k], self.vertices[i]))
            if sum(v*v for v in n) <= EPS*EPS:
                raise ValueError("degenerate triangle")
            for a, b, c in ((i, j, k), (j, k, i), (k, i, j)):
                edges[tuple(sorted((a, b)))] += 1
                directed[a, b] += 1
                adjacency[a].add(b)
                adjacency[b].add(a)
                links[a][b].add(c)
                links[a][c].add(b)
        if any(n != 2 for n in edges.values()):
            raise ValueError("mesh is not watertight: every edge must have two incident faces")
        if any(directed[a, b] != 1 or directed[b, a] != 1 for a, b in edges):
            raise ValueError("inconsistent outward winding")
        def connected(graph):
            seen, todo = set(), [next(iter(graph))]
            while todo:
                v = todo.pop()
                if v not in seen:
                    seen.add(v)
                    todo.extend(graph[v] - seen)
            return len(seen) == len(graph)
        if not connected(adjacency):
            raise ValueError("component has disconnected shells")
        if self.volume <= EPS:
            raise ValueError("non-positive solid volume")
        return {"vertices": len(self.vertices), "triangles": len(self.triangles),
                "edges": len(edges), "watertight": True, "connected_shells": 1,
                "volume_mm3": round(self.volume, 6)}


def solid_mesh(add: list[Box], remove: list[Box]) -> tuple[Mesh, list[Box]]:
    """Exact orthogonal CSG on a conforming coordinate grid (not voxel approximation).

    Every box boundary becomes a grid plane; internal faces are removed. Surface
    squares share indexed vertices and use the same subdivision at every join.
    Subtractive boxes model open pockets and unthreaded placeholder fastener bores.
    """
    axes = [sorted({round(b[e][i], 6) for b in add + remove for e in (0, 1)}) for i in range(3)]
    if math.prod(len(a)-1 for a in axes) > 500_000:
        raise ValueError("solid grid exceeds G0 complexity limit")
    occupied = set()
    cells = []
    for index in itertools.product(*(range(len(a)-1) for a in axes)):
        lo = tuple(axes[i][index[i]] for i in range(3))
        hi = tuple(axes[i][index[i]+1] for i in range(3))
        mid = tuple((a+b)/2 for a, b in zip(lo, hi))
        if any(contains(b, mid) for b in add) and not any(contains(b, mid) for b in remove):
            occupied.add(index)
            cells.append((lo, hi))
    if not occupied:
        raise ValueError("empty solid")
    vertices, triangles, vertex_ids = [], [], {}
    # Cyclic basis gives outward +axis normals; reverse for -axis faces.
    for index in sorted(occupied):
        for axis in range(3):
            u, v = (axis+1) % 3, (axis+2) % 3
            for sign in (-1, 1):
                neighbour = list(index)
                neighbour[axis] += sign
                if tuple(neighbour) in occupied:
                    continue
                quad = []
                for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    corner = list(index)
                    corner[axis] += int(sign > 0)
                    corner[u] += du
                    corner[v] += dv
                    point = tuple(axes[i][corner[i]] for i in range(3))
                    if point not in vertex_ids:
                        vertex_ids[point] = len(vertices)
                        vertices.append(point)
                    quad.append(vertex_ids[point])
                if sign < 0:
                    quad.reverse()
                triangles.extend(((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])))
    return Mesh(vertices, triangles), cells


@dataclass
class Part:
    id: str
    role: str
    mesh: Mesh
    cells: list[Box]
    color: str
    note: str
    reference_only: bool = False


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"unsupported schema in {path.name}")
    return value


def finite(value, label: str, positive=False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if positive and value <= 0:
        raise ValueError(f"{label} must be positive")
    return float(value)


def load_sources(config_path: Path, profile_path: Path | None = None) -> tuple[dict, dict, dict]:
    config = load_json(config_path)
    assembly = load_json(config_path.parent / config["assembly"])
    profile = load_json(profile_path or config_path.parent / config["phone_profile"])
    for source in (config, assembly, profile):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", source["id"]):
            raise ValueError("source ids must be safe ASCII identifiers")
    if assembly["units"] != "mm":
        raise ValueError("only millimetre source definitions are supported")
    for key in ("include_imu_mount", "include_ble_mount"):
        if not isinstance(config[key], bool):
            raise ValueError(f"{key} must be boolean")
    return assembly, profile, config


def parameters(assembly, profile, config):
    d = dict(assembly["dimensions"])
    overrides = config.get("dimension_overrides", {})
    if set(overrides) - set(d):
        raise ValueError("unknown dimension override")
    d.update(overrides)
    d = {k: finite(v, k) for k, v in d.items()}
    for k in ("pad_thickness", "adapter_wall", "slide_clearance", "scale_pitch", "stop_thickness",
              "grip_length", "grip_width", "grip_height", "chassis_thickness"):
        finite(d[k], k, positive=True)
    if d["scale_pitch"] < 1:
        raise ValueError("scale_pitch must be at least 1 mm")
    for name in ("height", "width", "thickness"):
        finite(profile["body_mm"][name], f"phone {name}", positive=True)
    case = finite(profile.get("case_allowance_mm", 0), "case_allowance_mm")
    if not 0 <= case <= 10:
        raise ValueError("case allowance must be between 0 and 10 mm per face")
    d.update(phone_height=profile["body_mm"]["height"]+2*case,
             phone_width=profile["body_mm"]["width"]+2*case,
             phone_thickness=profile["body_mm"]["thickness"]+2*case,
             carriage_x=finite(config["x_carriage_position_mm"], "carriage X"),
             cassette_z=finite(config["vertical_cassette_position_mm"], "cassette Z"))
    return d


def cylinder_mesh(center: Vec, radius: float, height: float, axis: str = "z", segments: int = 16) -> Mesh:
    if radius <= 0 or height <= 0 or segments < 8:
        raise ValueError("invalid cylinder")
    axes = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
    direction = axes[axis]
    # Pick a stable perpendicular basis. v = direction x u makes u x v = direction.
    u = (0, 1, 0) if axis == "x" else (1, 0, 0)
    v = cross(direction, u)
    lo = tuple(center[i] - direction[i]*height/2 for i in range(3))
    hi = tuple(center[i] + direction[i]*height/2 for i in range(3))
    vertices = []
    for end in (lo, hi):
        vertices.extend(tuple(end[i] + radius*(u[i]*math.cos(2*math.pi*j/segments) +
                         v[i]*math.sin(2*math.pi*j/segments)) for i in range(3))
                        for j in range(segments))
    triangles = []
    for j in range(segments):
        n = (j+1) % segments
        triangles.extend(((j, n, segments+n), (j, segments+n, segments+j)))
    lo_center, hi_center = len(vertices), len(vertices)+1
    vertices.extend((lo, hi))
    for j in range(segments):
        n = (j+1) % segments
        triangles.extend(((lo_center, n, j), (hi_center, segments+j, segments+n)))
    return Mesh(vertices, triangles)


def rounded_prism_mesh(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float,
                       radius: float, corner_segments: int = 4) -> Mesh:
    """Make a closed rounded-rectangle prism with polygonal corner arcs.

    This keeps the G0 grip printable without a CAD kernel while avoiding a
    sharp rectangular user-facing outline.  It is a faceted design surface,
    not a claim about ergonomic radii or surface finish.
    """
    if x1 <= x0 or y1 <= y0 or z1 <= z0 or radius <= 0 or radius >= min(x1 - x0, y1 - y0) / 2:
        raise ValueError("invalid rounded prism dimensions")
    if corner_segments < 2:
        raise ValueError("corner_segments must be at least 2")
    points: list[Vec] = []
    corners = ((x1 - radius, y0 + radius, -math.pi / 2, 0.0),
               (x1 - radius, y1 - radius, 0.0, math.pi / 2),
               (x0 + radius, y1 - radius, math.pi / 2, math.pi),
               (x0 + radius, y0 + radius, math.pi, 3 * math.pi / 2))
    for cx, cy, start, end in corners:
        for index in range(corner_segments + 1):
            angle = start + (end - start) * index / corner_segments
            point = (cx + radius * math.cos(angle), cy + radius * math.sin(angle), 0.0)
            if not points or point[:2] != points[-1][:2]:
                points.append(point)
    vertices = [(x, y, z0) for x, y, _ in points] + [(x, y, z1) for x, y, _ in points]
    n = len(points)
    bottom_center = len(vertices)
    top_center = bottom_center + 1
    vertices.extend(((sum(point[0] for point in points) / n, sum(point[1] for point in points) / n, z0),
                     (sum(point[0] for point in points) / n, sum(point[1] for point in points) / n, z1)))
    triangles: list[tuple[int, int, int]] = []
    for index in range(n):
        next_index = (index + 1) % n
        triangles.extend(((bottom_center, next_index, index),
                          (top_center, n + index, n + next_index),
                          (index, next_index, n + next_index),
                          (index, n + next_index, n + index)))
    return Mesh(vertices, triangles)


def add_box_part(parts, part_id, role, bounds, color, note, reference_only=False):
    mesh, cells = solid_mesh([bounds], [])
    parts.append(Part(part_id, role, mesh, cells, color, note, reference_only))


def add_cylinder_part(parts, part_id, role, center, radius, height, axis, color, note):
    mesh = cylinder_mesh(center, radius, height, axis)
    parts.append(Part(part_id, role, mesh, [mesh.bounds], color, note))


def add_rounded_prism_part(parts, part_id, role, bounds, radius, color, note):
    (x0, y0, z0), (x1, y1, z1) = bounds
    mesh = rounded_prism_mesh(x0, x1, y0, y1, z0, z1, radius)
    parts.append(Part(part_id, role, mesh, [mesh.bounds], color, note))


def build_parts(assembly: dict, profile: dict, config: dict) -> list[Part]:
    d = parameters(assembly, profile, config)
    parts: list[Part] = []
    orange, cyan, grey, black, lime = "#FF7A00", "#00B8D9", "#667085", "#111827", "#B6F000"
    x0, x1 = d["chassis_x_min"], d["chassis_x_max"]
    y0, y1 = -d["chassis_half_width"], d["chassis_half_width"]
    add_box_part(parts, "common_training_chassis", "training_chassis",
                 box(x0, x1, y0, y1, 0, d["chassis_thickness"]), orange,
                 "Broad bright chassis slab; no barrel, muzzle, pressure system or launching mechanism")
    add_rounded_prism_part(parts, "grip_body", "grip_body",
                           box(-34, 6, -d["grip_width"]/2, d["grip_width"]/2, -d["grip_height"], 1), 6, orange,
                           "Short broad rounded training grip; exact ergonomics and angle remain open")
    add_rounded_prism_part(parts, "grip_backstrap", "ergonomic_panel",
                           box(-33, -28, -d["grip_width"]/2 + 2, d["grip_width"]/2 - 2,
                               -d["grip_height"] + 7, -8), 2, lime,
                           "Replaceable ergonomic backstrap/panel placeholder; fit and comfort unverified")

    phone_x = d["phone_x"]
    phone_z0 = d["phone_bottom_z"]
    phone_z1 = phone_z0 + d["phone_height"]
    phone_x0 = phone_x - d["phone_thickness"]/2
    phone_x1 = phone_x + d["phone_thickness"]/2
    phone_y0, phone_y1 = -d["phone_width"]/2, d["phone_width"]/2
    adapter_y0 = phone_y0 - 8
    adapter_y1 = phone_y1 + 8
    add_box_part(parts, "adapter_interface", "adapter_interface",
                 box(phone_x-22, phone_x+22, adapter_y0, adapter_y1, 5, phone_z0+3), cyan,
                 "Replaceable interface plate; datum geometry only")
    plate_x0 = phone_x0 - d["adapter_wall"] - 0.6
    plate_x1 = phone_x0 - 0.6
    rail_x0 = phone_x1 + 0.6
    rail_x1 = rail_x0 + d["adapter_wall"]
    rail_t = d["adapter_wall"]
    add_box_part(parts, "iphone_adapter" if profile["id"] == "iPhone15" else "android_adapter",
                 "phone_adapter", box(plate_x0, plate_x1, adapter_y0, adapter_y1,
                 phone_z0-6, phone_z1+6), cyan,
                 "Replaceable phone back plate and open-edge frame; rear camera region intentionally not located")
    add_box_part(parts, "phone_reference", "phone_reference",
                 box(phone_x0, phone_x1, phone_y0, phone_y1, phone_z0, phone_z1), black,
                 f"Reference-only envelope from {profile['dimension_status']}; not a measured case or phone solid", True)
    add_box_part(parts, "retainer_left", "phone_retainer",
                 box(rail_x0, rail_x1, phone_y1+d["slide_clearance"], phone_y1+d["slide_clearance"]+rail_t*2,
                     phone_z0+5, phone_z1-5), cyan, "Captive lateral retainer; fit is adjustable")
    add_box_part(parts, "retainer_right", "phone_retainer",
                 box(rail_x0, rail_x1, phone_y0-d["slide_clearance"]-rail_t*2, phone_y0-d["slide_clearance"],
                     phone_z0+5, phone_z1-5), cyan, "Captive lateral retainer; fit is adjustable")
    add_box_part(parts, "pad_left", "phone_pad",
                 box(rail_x1+0.3, rail_x1+d["pad_thickness"]+0.3, phone_y1-d["pad_thickness"], phone_y1,
                     phone_z0+10, phone_z1-10), lime, "Replaceable compliant pad placeholder; material and compression unverified")
    add_box_part(parts, "pad_right", "phone_pad",
                 box(rail_x1+0.3, rail_x1+d["pad_thickness"]+0.3, phone_y0, phone_y0+d["pad_thickness"],
                     phone_z0+10, phone_z1-10), lime, "Replaceable compliant pad placeholder; material and compression unverified")

    # A short top/bottom bridge is deliberately not a tube: it leaves the upper rear phone area open.
    add_box_part(parts, "phone_top_retainer", "phone_retainer",
                 box(rail_x0, rail_x1, phone_y0-rail_t*2, phone_y1+rail_t*2, phone_z1+d["slide_clearance"],
                     phone_z1+d["slide_clearance"]+rail_t), cyan, "Upper anti-lift retainer")
    add_box_part(parts, "phone_bottom_retainer", "phone_retainer",
                 box(rail_x0, rail_x1, phone_y0-rail_t*2, phone_y1+rail_t*2, phone_z0-rail_t-d["slide_clearance"],
                     phone_z0-d["slide_clearance"]), cyan, "Lower anti-lift retainer")

    # X-axis captive ballast: floor, carriage, two hard stops, graduated scale and lock.
    tx0, tx1 = d["x_track_min"], d["x_track_max"]
    add_box_part(parts, "x_ballast_rail", "x_track",
                 box(tx0, tx1, -d["x_track_half_width"], d["x_track_half_width"], d["x_track_floor_z"], d["x_track_top_z"]), grey,
                 "Captive X ballast guide; targetward is +X")
    cx = d["carriage_x"]
    add_box_part(parts, "x_ballast_carriage", "x_carriage",
                 box(cx-d["x_flange_half_length"], cx+d["x_flange_half_length"], -d["x_flange_half_width"], d["x_flange_half_width"],
                     d["x_track_floor_z"]+d["slide_clearance"], d["x_lip_bottom_z"]), grey,
                 "Captive carriage at configured nominal X position")
    add_box_part(parts, "x_ballast", "x_ballast",
                 box(cx-d["x_neck_half_width"], cx+d["x_neck_half_width"], -d["x_neck_half_width"], d["x_neck_half_width"],
                     d["x_lip_bottom_z"]+0.5, d["x_track_top_z"]+5), grey,
                 "Removable ballast placeholder; mass is intentionally unspecified")
    add_box_part(parts, "x_end_stop_rear", "x_end_stop",
                 box(tx0, tx0+d["stop_thickness"], -d["x_track_half_width"], d["x_track_half_width"], d["x_track_floor_z"], d["x_track_top_z"]+2), orange,
                 "Hard rear travel end stop")
    add_box_part(parts, "x_end_stop_targetward", "x_end_stop",
                 box(tx1-d["stop_thickness"], tx1, -d["x_track_half_width"], d["x_track_half_width"], d["x_track_floor_z"], d["x_track_top_z"]+2), orange,
                 "Hard targetward travel end stop")
    add_box_part(parts, "x_scale", "x_scale",
                 box(tx0+4, tx1-4, -d["x_track_half_width"]-3, -d["x_track_half_width"]-1, d["x_track_top_z"]+0.2, d["x_track_top_z"]+1.5), orange,
                 f"Scale reference bar; nominal pitch {d['scale_pitch']:g} mm; print scale must be checked")
    add_cylinder_part(parts, "x_lock", "x_lock", (cx, -d["x_track_half_width"]-4, d["x_track_top_z"]+3), 4, 4, "y", black,
                      "Captive lock placeholder; thread and force are unverified")

    # Vertical cassette and two passive side rails. The cassette is a separate enclosed solid.
    vz0, vz1 = d["vertical_min_z"], d["vertical_max_z"]
    add_box_part(parts, "vertical_ballast_track", "vertical_track",
                 box(d["vertical_back_x"], d["vertical_outer_x"], d["vertical_y_min"], d["vertical_y_max"], vz0, vz1), grey,
                 "Captive vertical ballast track; +Z is vertical")
    vz = d["cassette_z"]
    add_box_part(parts, "vertical_ballast_cassette", "vertical_cassette",
                 box(d["vertical_back_x"]+d["slide_clearance"], d["vertical_lip_x"]-d["slide_clearance"],
                     d["vertical_channel_y_min"]+1, d["vertical_channel_y_max"]-1, vz-d["vertical_flange_half_height"], vz+d["vertical_flange_half_height"]), grey,
                 "Removable vertical ballast cassette at configured nominal Z")
    add_box_part(parts, "vertical_ballast", "vertical_ballast",
                 box(d["vertical_back_x"]+2, d["vertical_lip_x"]-2, d["vertical_mouth_y_min"], d["vertical_mouth_y_max"],
                     vz-8, vz+8), grey, "Removable ballast placeholder; mass is intentionally unspecified")
    add_box_part(parts, "vertical_retainer", "vertical_retainer",
                 box(d["vertical_lip_x"], d["vertical_outer_x"], d["vertical_y_min"], d["vertical_y_min"]+3, vz0+4, vz1-4), orange,
                 "Vertical capture lip")
    add_box_part(parts, "vertical_end_stop_lower", "vertical_end_stop",
                 box(d["vertical_back_x"], d["vertical_outer_x"], d["vertical_y_min"], d["vertical_y_max"], vz0, vz0+d["stop_thickness"]), orange,
                 "Hard lower vertical end stop")
    add_box_part(parts, "vertical_end_stop_upper", "vertical_end_stop",
                 box(d["vertical_back_x"], d["vertical_outer_x"], d["vertical_y_min"], d["vertical_y_max"], vz1-d["stop_thickness"], vz1), orange,
                 "Hard upper vertical end stop")
    add_cylinder_part(parts, "vertical_lock", "vertical_lock", (d["vertical_outer_x"]+3, (d["vertical_y_min"]+d["vertical_y_max"])/2, vz), 4, 4, "x", black,
                      "Vertical cassette lock placeholder; thread and force are unverified")

    # Fiducial is a passive plate outside the phone envelope; no camera coordinate is invented.
    add_box_part(parts, "passive_fiducial_mount", "fiducial_mount",
                 box(phone_x1+8, phone_x1+13, -d["phone_width"]/2-16, -d["phone_width"]/2-8, phone_z0+8, phone_z0+28), lime,
                 "Passive calibration/fiducial plate; size and camera relation require measurement")
    if config["include_imu_mount"]:
        add_box_part(parts, "imu_mount", "imu_mount", box(26, 42, -51, -33, 8, 15), cyan,
                     "Optional rigid IMU mount placeholder; axis convention unverified")
    if config["include_ble_mount"]:
        add_box_part(parts, "ble_mount", "ble_mount", box(26, 42, 33, 51, 8, 15), cyan,
                     "Optional passive BLE/trigger switch mount placeholder")
    add_cylinder_part(parts, "fastener_placeholders", "fastener_placeholder", (x0+12, y0+12, -2), 2.0, 4.0, "z", black,
                      "One M4-scale placeholder shown; repeat count, inserts and threads are unverified")
    return parts


def fmt(value: float) -> str:
    if abs(value) < 0.0000005:
        value = 0.0
    return f"{value:.6f}"


def write_ascii_stl(mesh: Mesh, path: Path, name: str) -> dict:
    stats = mesh.validate()
    lines = [f"solid {name}"]
    for i, j, k in mesh.triangles:
        normal = cross(sub(mesh.vertices[j], mesh.vertices[i]), sub(mesh.vertices[k], mesh.vertices[i]))
        length = math.sqrt(sum(v*v for v in normal))
        normal = tuple(v/length for v in normal)
        lines.append(f"  facet normal {' '.join(fmt(v) for v in normal)}")
        lines.append("    outer loop")
        for index in (i, j, k):
            lines.append(f"      vertex {' '.join(fmt(v) for v in mesh.vertices[index])}")
        lines.extend(("    endloop", "  endfacet"))
    lines.extend((f"endsolid {name}", ""))
    path.write_text("\n".join(lines), encoding="ascii", newline="\n")
    return stats


def read_ascii_stl(path: Path) -> Mesh:
    vertices: list[Vec] = []
    vertex_ids: dict[Vec, int] = {}
    triangles: list[tuple[int, int, int]] = []
    current: list[int] = []
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.strip().split()
        if len(fields) == 4 and fields[0].lower() == "vertex":
            point = tuple(round(float(v), 6) for v in fields[1:])
            if point not in vertex_ids:
                vertex_ids[point] = len(vertices)
                vertices.append(point)
            current.append(vertex_ids[point])
            if len(current) == 3:
                triangles.append(tuple(current))
                current = []
    if current or not triangles:
        raise ValueError(f"invalid ASCII STL: {path}")
    return Mesh(vertices, triangles)


def step_direction(normal: Vec) -> Vec:
    candidates = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    return min(candidates, key=lambda candidate: abs(sum(a*b for a, b in zip(candidate, normal))))


def write_step(meshes: dict[str, Mesh], path: Path, title: str) -> None:
    """Write a deterministic AP203-style faceted BREP.

    This deliberately uses planar triangle faces and explicit edge curves. It
    does not claim NURBS, machining tolerances or material properties. The
    result is intended to be reopened by a STEP reader; the repository still
    requires a native CAD-kernel reopen check before manufacturing release.
    """
    entities: list[str] = []

    def entity(text: str) -> int:
        entities.append(text)
        return len(entities)

    app = entity("APPLICATION_CONTEXT('configuration controlled 3d designs of mechanical parts and assemblies')")
    product_context = entity(f"PRODUCT_CONTEXT('',#{app},'mechanical')")
    product = entity(f"PRODUCT('{title}','{title}','',(#{product_context}))")
    formation = entity(f"PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('1','G0 faceted BREP',#{product},.MADE.)")
    pd_context = entity(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{app},'design')")
    product_definition = entity(f"PRODUCT_DEFINITION('design','',#{formation},#{pd_context})")
    shape_definition = entity(f"PRODUCT_DEFINITION_SHAPE('','',#{product_definition})")
    length_unit = entity("(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.))")
    angle_unit = entity("(NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.))")
    solid_angle_unit = entity("(NAMED_UNIT(*) SOLID_ANGLE_UNIT() SI_UNIT($,.STERADIAN.))")
    uncertainty = entity(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.01),#{length_unit},'distance_accuracy_value','G0 export')")
    context = entity(
        "(GEOMETRIC_REPRESENTATION_CONTEXT(3) "
        "GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{0})) "
        "GLOBAL_UNIT_ASSIGNED_CONTEXT((#{1},#{2},#{3})) "
        "REPRESENTATION_CONTEXT('3D','MODEL SPACE'))".format(
            uncertainty, length_unit, angle_unit, solid_angle_unit
        )
    )

    brep_refs = []
    for mesh_name in sorted(meshes):
        mesh = meshes[mesh_name]
        mesh.validate()
        point_ids: dict[Vec, int] = {}
        cartesian_ids: dict[Vec, int] = {}
        for raw_point in mesh.vertices:
            point = tuple(round(v, 6) for v in raw_point)
            if point not in point_ids:
                cart = entity(f"CARTESIAN_POINT('',({','.join(fmt(v) for v in point)}))")
                cartesian_ids[point] = cart
                point_ids[point] = entity(f"VERTEX_POINT('',#{cart})")
        face_refs = []
        for i, j, k in mesh.triangles:
            points = [tuple(round(v, 6) for v in mesh.vertices[index]) for index in (i, j, k)]
            a, b, c = points
            normal_raw = cross(sub(b, a), sub(c, a))
            norm = math.sqrt(sum(v * v for v in normal_raw))
            normal = tuple(v / norm for v in normal_raw)
            ref = step_direction(normal)
            origin = entity(f"CARTESIAN_POINT('',({','.join(fmt(v) for v in a)}))")
            normal_dir = entity(f"DIRECTION('',({','.join(fmt(v) for v in normal)}))")
            ref_dir = entity(f"DIRECTION('',({','.join(fmt(v) for v in ref)}))")
            placement = entity(f"AXIS2_PLACEMENT_3D('',#{origin},#{normal_dir},#{ref_dir})")
            plane = entity(f"PLANE('',#{placement})")
            oriented_edges = []
            for start, end in ((a, b), (b, c), (c, a)):
                delta = sub(end, start)
                length = math.sqrt(sum(value * value for value in delta))
                direction = tuple(value / length for value in delta)
                edge_direction = entity(f"DIRECTION('',({','.join(fmt(v) for v in direction)}))")
                vector = entity(f"VECTOR('',#{edge_direction},{fmt(length)})")
                line = entity(f"LINE('',#{cartesian_ids[start]},#{vector})")
                edge_curve = entity(f"EDGE_CURVE('',#{point_ids[start]},#{point_ids[end]},#{line},.T.)")
                oriented_edges.append(entity(f"ORIENTED_EDGE('',*,*,#{edge_curve},.T.)"))
            loop = entity(f"EDGE_LOOP('',({','.join('#' + str(ref) for ref in oriented_edges)}))")
            bound = entity(f"FACE_OUTER_BOUND('',#{loop},.T.)")
            face_refs.append(entity(f"ADVANCED_FACE('',(#{bound}),#{plane},.T.)"))
        shell = entity(f"CLOSED_SHELL('',({','.join('#' + str(ref) for ref in face_refs)}))")
        brep_refs.append(entity(f"FACETED_BREP('{mesh_name}',#{shell})"))
    representation = entity(f"SHAPE_REPRESENTATION('{title}',({','.join('#' + str(ref) for ref in brep_refs)}),#{context})")
    entity(f"SHAPE_DEFINITION_REPRESENTATION(#{shape_definition},#{representation})")

    lines = [
        "ISO-10303-21;", "HEADER;",
        "FILE_DESCRIPTION(('SIGHTLINE deterministic faceted BREP'),'2;1');",
        "FILE_NAME('sightline_g0.step','2000-01-01T00:00:00',('SIGHTLINE'),('SIGHTLINE'),'','SIGHTLINE','');",
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN_CC2'));", "ENDSEC;", "DATA;",
    ]
    lines.extend(f"#{index}={value};" for index, value in enumerate(entities, 1))
    lines.extend(("ENDSEC;", "END-ISO-10303-21;", ""))
    path.write_text("\n".join(lines), encoding="ascii", newline="\n")


def bounds_to_json(bounds: Box) -> dict:
    return {"min": [round(v, 6) for v in bounds[0]], "max": [round(v, 6) for v in bounds[1]]}


def bounds_union(parts: list[Part]) -> Box:
    return (tuple(min(p.mesh.bounds[0][i] for p in parts) for i in range(3)),
            tuple(max(p.mesh.bounds[1][i] for p in parts) for i in range(3)))


def capture_checks(d: dict) -> dict:
    xhalf = d["x_flange_half_length"]
    x_ok = (d["x_track_min"] < d["carriage_x"]-xhalf and
            d["carriage_x"]+xhalf < d["x_track_max"] and
            d["x_track_max"]-d["x_track_min"] > 2*xhalf + 2*d["slide_clearance"] and
            d["stop_thickness"] >= d["slide_clearance"])
    zhalf = d["vertical_flange_half_height"]
    z_ok = (d["vertical_min_z"] < d["cassette_z"]-zhalf and
            d["cassette_z"]+zhalf < d["vertical_max_z"] and
            d["vertical_max_z"]-d["vertical_min_z"] > 2*zhalf + 2*d["slide_clearance"] and
            d["stop_thickness"] >= d["slide_clearance"])
    return {
        "x_ballast": {"passed": x_ok, "rail_min_mm": d["x_track_min"], "rail_max_mm": d["x_track_max"],
                      "nominal_center_mm": d["carriage_x"], "half_length_mm": xhalf,
                      "end_stops": ["x_end_stop_rear", "x_end_stop_targetward"], "capture_lip_mm": d["slide_clearance"]},
        "vertical_ballast": {"passed": z_ok, "track_min_mm": d["vertical_min_z"], "track_max_mm": d["vertical_max_z"],
                             "nominal_center_mm": d["cassette_z"], "half_height_mm": zhalf,
                             "end_stops": ["vertical_end_stop_lower", "vertical_end_stop_upper"], "capture_lip_mm": d["slide_clearance"]}
    }


def validate_parts(parts: list[Part], assembly: dict, profile: dict, config: dict) -> dict:
    errors = []
    by_id = {part.id: part for part in parts}
    for part in parts:
        try:
            part.mesh.validate()
        except ValueError as exc:
            errors.append(f"{part.id}: {exc}")
    d = parameters(assembly, profile, config)
    whole = bounds_union(parts)
    limits = (tuple(assembly["envelope_limits_mm"]["min"]), tuple(assembly["envelope_limits_mm"]["max"]))
    envelope_ok = all(whole[0][i] >= limits[0][i]-EPS and whole[1][i] <= limits[1][i]+EPS for i in range(3))
    if not envelope_ok:
        errors.append(f"assembly exceeds envelope: {bounds_to_json(whole)}")
    capture = capture_checks(d)
    if not all(item["passed"] for item in capture.values()):
        errors.append("one or more ballast tracks fail capture/end-stop sanity")
    required_roles = set(assembly["required_roles"])
    present_roles = {part.role for part in parts}
    missing_roles = sorted(required_roles - present_roles)
    if missing_roles:
        errors.append("missing roles: " + ", ".join(missing_roles))
    # Only declared forbidden pairs are considered collisions. Mounting and
    # captive solids are expected to overlap in this simple G0 representation.
    collision_pairs = [("phone_reference", "passive_fiducial_mount"), ("phone_reference", "imu_mount"),
                       ("phone_reference", "ble_mount")]
    collisions = []
    for first, second in collision_pairs:
        if first in by_id and second in by_id and intersects(by_id[first].mesh.bounds, by_id[second].mesh.bounds):
            collisions.append([first, second])
    if collisions:
        errors.append("forbidden collisions: " + json.dumps(collisions))
    return {"passed": not errors, "errors": errors, "envelope": {"passed": envelope_ok, "bounds_mm": bounds_to_json(whole), "limits_mm": bounds_to_json(limits)},
            "capture": capture, "forbidden_collisions": {"passed": not collisions, "pairs": collisions}}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(config_path: Path, output_dir: Path, write_step_files: bool = True) -> dict:
    assembly, profile, config = load_sources(config_path)
    parts = build_parts(assembly, profile, config)
    validation = validate_parts(parts, assembly, profile, config)
    if not validation["passed"]:
        raise ValueError("CAD validation failed: " + "; ".join(validation["errors"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    step_meshes = {}
    for part in parts:
        stl_path = output_dir / f"{part.id}.stl"
        stats = write_ascii_stl(part.mesh, stl_path, part.id)
        entry = {"id": part.id, "role": part.role, "stl": stl_path.name, "sha256": sha256(stl_path),
                 "bounds_mm": bounds_to_json(part.mesh.bounds), "color": part.color, "note": part.note,
                 "reference_only": part.reference_only, "mesh": stats}
        if write_step_files:
            step_path = output_dir / f"{part.id}.step"
            write_step({part.id: part.mesh}, step_path, part.id)
            entry["step"] = step_path.name
            entry["step_sha256"] = sha256(step_path)
        entries.append(entry)
        step_meshes[part.id] = part.mesh
    if write_step_files:
        master_step = output_dir / "assembly.step"
        write_step(step_meshes, master_step, config["id"])
    manifest = {
        "manifest_version": 1,
        "generator": "scripts/generate_cad.py",
        "generator_version": "1.1.0",
        "source": {"assembly": str(Path("cad/parametric") / "assembly.json"),
                   "configuration": str(Path("cad/parametric/configurations") / config_path.name),
                   "profile": str(Path("cad/parametric/phone_profiles") / (profile["id"] + ".json"))},
        "configuration_id": config["id"], "profile_id": profile["id"], "units": "mm",
        "axes": assembly["axes"], "appearance": assembly["appearance"],
        "phone": {"body_mm": profile["body_mm"], "dimension_status": profile["dimension_status"],
                   "case_allowance_mm": profile.get("case_allowance_mm"),
                   "mass_g": profile.get("mass_g"), "mass_status": profile.get("mass_status"),
                   "camera_status": profile.get("camera_status", "UNVERIFIED"),
                   "camera_selection": profile.get("camera_selection"),
                   "camera_centres_mm": profile.get("camera_centres_mm"),
                   "camera_field_of_view_clearance": profile.get("camera_field_of_view_clearance"),
                   "camera_keepout": profile.get("camera_keepout"),
                   "adapter_id": profile.get("adapter_id"),
                   "phone_to_chassis_transform": profile.get("phone_to_chassis_transform"),
                   "phone_to_adapter_transform": profile.get("phone_to_adapter_transform"),
                   "adapter_to_chassis_transform": profile.get("adapter_to_chassis_transform"),
                   "reference_only": True},
        "validation": validation, "components": entries,
        "exports": {"assembly_step": "assembly.step" if write_step_files else None,
                     "step_kind": "faceted BREP with planar triangular faces" if write_step_files else None},
        "determinism": {"stl_ascii": True, "fixed_header_date": "2000-01-01T00:00:00"},
    }
    if write_step_files:
        manifest["exports"]["assembly_step_sha256"] = sha256(output_dir / "assembly.step")
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return manifest


def validate_export_dir(output_dir: Path) -> dict:
    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for component in manifest.get("components", []):
        stl = output_dir / component["stl"]
        if not stl.exists():
            errors.append(f"missing {stl.name}")
            continue
        try:
            stats = read_ascii_stl(stl).validate()
            if not stats["watertight"]:
                errors.append(f"not watertight: {stl.name}")
        except (OSError, ValueError) as exc:
            errors.append(f"{stl.name}: {exc}")
    step = manifest.get("exports", {}).get("assembly_step")
    if step and not (output_dir / step).exists():
        errors.append(f"missing {step}")
    return {"passed": not errors, "errors": errors, "configuration_id": manifest.get("configuration_id")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="editable configuration JSON (default: iphone15_g0)")
    parser.add_argument("--profile", type=Path, default=None, help="optional profile override")
    parser.add_argument("--output", type=Path, default=None, help="export directory")
    parser.add_argument("--validate-only", action="store_true", help="validate in memory without writing exports")
    parser.add_argument("--check-exports", type=Path, default=None, help="validate an existing manifest/export directory")
    parser.add_argument("--no-step", action="store_true", help="write STL and manifest but omit STEP files")
    args = parser.parse_args(argv)
    try:
        if args.check_exports:
            result = validate_export_dir(args.check_exports)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["passed"] else 1
        assembly, profile, config = load_sources(args.config, args.profile)
        if args.validate_only:
            result = validate_parts(build_parts(assembly, profile, config), assembly, profile, config)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["passed"] else 1
        output = args.output or ROOT / "cad/exports" / config["id"]
        manifest = generate(args.config, output, write_step_files=not args.no_step)
        print(f"wrote {len(manifest['components'])} components to {output}")
        print(f"manifest: {output / 'manifest.json'}")
        return 0
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"CAD generation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
