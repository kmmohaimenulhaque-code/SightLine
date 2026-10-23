"""G1 configuration → placed parts, transform chain and mass properties.

Transform chain (4×4, mm): PHONE BODY P → PHONE ADAPTER Q (cradle datums) → PHONE YOKE Y (pivot, carries the
indexed angle) → COMMON CHASSIS K1 → GRIP DATUM G.

* P: profile convention — origin at the back-face centre, +x out of the back, +y toward the phone's top end.
* Q: origin where datum plane A (phone back, back pads), B (bottom long edge, ledge pads) and C (+Y short edge, end
  block) meet; axes parallel to K1 at angle 0.
* Y: origin on the pivot axis; rotated about +Y by the dial angle (positive angle raises the camera axis).
* G: origin at the grip axis point on the housing underside; axes parallel to K1.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import geom as gm

REPO = Path(__file__).resolve().parents[3]


def load_params(path=None) -> gm.A:
    path = Path(path or REPO / "cad/parametric/parameters/g1.json")
    d = json.loads(path.read_text())
    if d.get("schema") != "sightline.cad.g1_parameters/1":
        raise ValueError(f"{path}: not a sightline.cad.g1_parameters/1 document")
    a = gm.A(d)
    a["_path"] = str(path)
    return a


def load_profile(path) -> dict:
    d = json.loads(Path(path).read_text())
    b = d["body"]
    v = lambda x: x["v"] if isinstance(x, dict) else x  # noqa: E731
    dev = d.get("device")
    if isinstance(dev, dict):
        dev = " ".join(str(dev.get(k, "")) for k in ("manufacturer", "model", "variant") if dev.get(k)) or d["profile_id"]
    return {"id": d["profile_id"], "device": dev or d["profile_id"], "L": float(v(b["length"])),
            "W": float(v(b["width"])), "T": float(v(b["thickness"])), "Rc": float(v(b["plan_corner_radius"])),
            "dims_status": b["length"].get("s", "") if isinstance(b["length"], dict) else "",
            "mass": {"v": float(d["mass"]["v"]), "s": d["mass"].get("s", ""), "sigma": d["mass"].get("sigma")},
            "com_status": d.get("com_offset", {}).get("s", "UNKNOWN"), "buttons": d.get("buttons", []),
            "camera_status": "PENDING (centre, lens assignment, protrusion, FOV not measured)",
            "path": str(Path(path).relative_to(REPO)) if str(path).startswith(str(REPO)) else str(path)}


def load_config(path) -> dict:
    cfg = json.loads(Path(path).read_text())
    if cfg.get("schema") != "sightline.cad.g1_configuration/1":
        raise ValueError(f"{path}: not a sightline.cad.g1_configuration/1 document")
    return cfg


@dataclass
class Assembly:
    cfg: dict
    P: gm.A
    prof: dict
    parts: list
    keepouts: list
    frames: dict
    extras: dict = field(default_factory=dict)

    @property
    def id(self):
        return self.cfg["config_id"]

    def get(self, pid):
        for p in self.parts:
            if p.id == pid:
                return p
        raise KeyError(pid)


def build(config, P=None, **over) -> Assembly:
    cfg = load_config(config) if isinstance(config, (str, Path)) else json.loads(json.dumps(config))
    for k, v in over.items():
        cfg[k] = v
    P = P or load_params(REPO / cfg["parameters"])
    prof = load_profile(REPO / cfg["phone_profile"])
    left = cfg.get("hand", "right") == "left"
    ang = float(cfg.get("angle_deg", P.yoke.angle_nominal_deg))
    sg = cfg.get("sight", {})
    sh = cfg.get("palm_shelf", {})
    drop = float(sh.get("drop", P.palm_shelf.drop))
    bsd = float(P.grip.backstrap_variants[cfg.get("backstrap", "M")])
    b = cfg["ballast"]
    parts = []
    parts += gm.housing_parts(P)
    parts += gm.guard_switch_parts(P)
    parts += gm.rear_sight_parts(P, float(sg.get("rear_elev", 0.0)), float(sg.get("rear_wind", 0.0)))
    parts += gm.front_sight_parts(P, float(sg.get("front_shim", P.sight.front_shim_nominal)),
                                  float(sg.get("front_lat", 0.0)))
    parts += gm.yoke_parts(P)
    parts += gm.angle_dial_parts(P, ang)
    parts += gm.cradle_parts(P, prof, ang)
    parts += gm.phone_parts(P, prof, ang)
    parts += gm.grip_parts(P, drop, float(sh.get("angle_deg", P.palm_shelf.angle_deg)), bsd, left)
    parts += gm.z_ballast_parts(P, float(b["z"]["index_mm"]), int(b["z"]["slugs"]), drop, left)
    parts += gm.x_channel_parts(P)
    parts += gm.x_cassette_parts(P, float(b["x"]["position_mm"]), int(b["x"]["slugs"]))
    parts += gm.fixed_bars(P, int(b.get("fixed_bars", 0)))
    ids = [p.id for p in parts]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError(f"duplicate part ids {dup}")
    asm = Assembly(cfg, P, prof, parts, gm.camera_keepouts(P, prof, ang), frames(P, prof, ang),
                   {"phone_geom": gm.phone_geometry(P, prof)})
    return asm


# ---------------------------------------------------------------- transforms

def Ry(deg):
    """Rotation used by ``geom.rotate_y``: about +Y by −deg (positive deg raises points ahead of the axis)."""
    t = math.radians(-deg)
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def T(R=None, t=(0, 0, 0)):
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    M[:3, 3] = t
    return M


def frames(P, prof, ang=0.0) -> dict:
    g = gm.phone_geometry(P, prof)
    piv = gm.pivot_point(P)
    T_QP = T(t=(0.0, -g["L"] / 2, g["W"] / 2))
    q_in_y = np.array([g["x_back"], g["L"] / 2, g["z_bot"]]) - piv
    T_YQ = T(t=q_in_y)
    T_KY = T(Ry(ang), piv)
    G0 = np.array([P.grip.top_x, 0.0, -P.housing.height])
    T_KG = T(t=G0)
    T_KP = T_KY @ T_YQ @ T_QP
    T_GP = np.linalg.inv(T_KG) @ T_KP
    cam_axis = T_KP[:3, :3] @ np.array([1.0, 0, 0])
    return {"T_QP": T_QP, "T_YQ": T_YQ, "T_KY": T_KY, "T_KG": T_KG, "T_KP": T_KP, "T_GP": T_GP,
            "pivot_K": piv, "grip_datum_K": G0, "angle_deg": ang,
            "phone_long_axis_K": T_KP[:3, :3] @ np.array([0, 1.0, 0]),
            "screen_normal_K": -cam_axis, "rear_camera_axis_K": cam_axis,
            "operator_view_dir_K": np.array([1.0, 0, 0]), "target_dir_K": np.array([1.0, 0, 0])}


def frames_report(asm) -> dict:
    f = asm.frames
    r = lambda M: np.round(M, 4).tolist()  # noqa: E731
    sight = sight_geometry(asm.P)
    return {"frame_K1": asm.P.frame, "chain": "p_K = T_KY · T_YQ · T_QP · p_P ;  p_G = T_KG⁻¹ · p_K",
            **{k: r(v) for k, v in f.items() if isinstance(v, np.ndarray)}, "angle_deg": f["angle_deg"],
            "sight_line_frame": sight, "phone_profile": asm.prof["id"]}


def sight_geometry(P) -> dict:
    s = P.sight
    rn = sum(s.rear_notch_x) / 2
    fb = sum(s.front_blade_x) / 2
    R = fb - rn
    eye = s.eye_distance_mm
    blade_ang = s.blade_w / (eye + R) * 1e3
    notch_ang = s.notch_w / eye * 1e3
    lever = rn - s.rear_hinge_x
    return {"rear_sight_origin_K": [rn, 0.0, s.line_z], "front_sight_origin_K": [fb, 0.0, s.line_z],
            "sight_radius_mm": round(R, 2), "nominal_sight_height_above_housing_mm": s.line_z,
            "reference_alignment_axis_K": [1.0, 0.0, 0.0],
            "rear_elevation_range_mm": [-s.rear_elev_range_mm, s.rear_elev_range_mm],
            "rear_elevation_range_mrad": round(s.rear_elev_range_mm / R * 1e3, 2),
            "rear_leaf_angle_range_deg": round(math.degrees(math.atan2(s.rear_elev_range_mm, lever)), 2),
            "rear_windage_range_mm": [-s.rear_wind_range_mm, s.rear_wind_range_mm],
            "rear_windage_range_mrad": round(s.rear_wind_range_mm / R * 1e3, 2),
            "front_elevation_shim_mm": list(s.front_shim_range), "front_shim_step_mm": s.front_shim_step,
            "front_lateral_shim_offset_mm": [-(s.front_wall_inner - s.front_carrier_half_w - 0.4),
                                             s.front_wall_inner - s.front_carrier_half_w - 0.4],
            "front_blade_width_mm": s.blade_w, "rear_notch_width_mm": s.notch_w,
            "sight_picture_at_assumed_eye_distance": {"eye_distance_mm": eye, "status": s.eye_distance_status,
                                                      "blade_mrad": round(blade_ang, 2),
                                                      "notch_mrad": round(notch_ang, 2),
                                                      "light_gap_each_side_mrad": round((notch_ang - blade_ang) / 2, 2)},
            "evidence": "MODEL OUTPUT (geometry); sight-alignment performance UNVERIFIED"}


# ---------------------------------------------------------------- mass properties

def part_mass(P, p) -> dict:
    """CAD-estimated mass, COM and inertia (about the COM, K1 axes) of one part."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    s = p.shape
    vol = s.Volume()
    if p.mass_override_g is not None:
        m = p.mass_override_g
        basis = p.status if p.kind in ("phone", "electronics") else "ESTIMATED (nominal)"
    elif p.kind in ("printed", "tpu"):
        mat = P.materials[p.material]
        shell = min(vol, s.Area() * mat["wall"])
        m = mat["rho"] * (shell + mat.get("infill", 1.0) * (vol - shell)) / 1000.0
        basis = f"ESTIMATED ({p.material}, {100 * mat.get('infill', 1.0):.0f} % infill, {mat['wall']} mm walls)"
    else:
        m = P.materials["steel"]["rho"] * vol / 1000.0
        basis = "ESTIMATED (steel, solid)"
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(s.wrapped, props)
    c = props.CentreOfMass()
    com = np.array([c.X(), c.Y(), c.Z()])
    I = np.zeros((3, 3))
    if vol > 0 and m > 0:
        Mi = props.MatrixOfInertia()
        I = np.array([[Mi.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)]) * (m / vol)
    return {"id": p.id, "mass_g": m, "com": com, "I": I, "basis": basis, "group": p.group, "moving": p.moving}


def combine(rows) -> dict:
    M = sum(r["mass_g"] for r in rows)
    com = sum(r["mass_g"] * r["com"] for r in rows) / M
    I = np.zeros((3, 3))
    for r in rows:
        d = r["com"] - com
        I += r["I"] + r["mass_g"] * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    return {"mass_g": M, "com": com, "I": I}


def mass_table(asm) -> list:
    return [part_mass(asm.P, p) for p in asm.parts]


def mass_summary(asm, rows=None) -> dict:
    rows = rows or mass_table(asm)
    tot = combine(rows)
    unc = {"phone": asm.prof["mass"].get("sigma") or 0.0}
    printed = sum(r["mass_g"] for r in rows if r["basis"].startswith("ESTIMATED (PETG") or "TPU" in r["basis"])
    sigma = math.sqrt(unc["phone"] ** 2 + (0.10 * printed) ** 2 + 6.0 ** 2)
    G0 = asm.frames["grip_datum_K"]
    return {"config_id": asm.id, "profile": asm.prof["id"], "mass_g": round(tot["mass_g"], 1),
            "mass_sigma_g": round(sigma, 1), "com_K_mm": np.round(tot["com"], 2).tolist(),
            "com_G_mm": np.round(tot["com"] - G0, 2).tolist(),
            "inertia_about_com_K_gmm2": np.round(tot["I"], 0).tolist(),
            "status": "MODEL OUTPUT (CAD estimate: printed parts volume × density with a wall/infill model, steel "
                      "solid, phone at its box centre with manufacturer/placeholder mass, electronics PLACEHOLDER). "
                      "Not measured.",
            "sigma_basis": "1σ from phone mass σ, ±10 % on printed-part mass, ±6 g hardware/electronics (ESTIMATED)",
            "by_group": {g: round(sum(r["mass_g"] for r in rows if r["group"] == g), 1)
                         for g in sorted({r["group"] for r in rows})}}
