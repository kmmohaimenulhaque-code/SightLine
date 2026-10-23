"""G1 CAD: geometry validity, collisions, moving interfaces, sights, phone orientation, transforms, mass solver,
exports. Software checks only — none of these is a physical test."""

import json
import math
from pathlib import Path

import numpy as np
import pytest

cq = pytest.importorskip("cadquery")

from cad.parametric.sightline_g1 import checks as ck  # noqa: E402
from cad.parametric.sightline_g1 import geom as gm  # noqa: E402
from cad.parametric.sightline_g1 import solver  # noqa: E402
from cad.parametric.sightline_g1.assembly import REPO, build, mass_summary, sight_geometry  # noqa: E402

CONF = REPO / "cad/parametric/configurations/g1"
RH = CONF / "g1_iphone15_rh.json"


@pytest.fixture(scope="module")
def asm():
    return build(RH)


def test_closed_positive_solids(asm):
    for p in asm.parts:
        assert p.shape.isValid(), p.id
        assert len(p.shape.Solids()) == 1, p.id
        assert p.shape.Volume() > 0, p.id


def test_required_components_present(asm):
    ids = {p.id for p in asm.parts}
    need = {"A-HOUSING-R", "A-HOUSING-F", "A-NOSE", "A-RAIL", "A-TRIGGER-GUARD", "S-REAR-NOTCH", "S-REAR-LEAF",
            "S-FRONT-BLADE", "S-FRONT-CARRIER", "B-YOKE", "B-ANGLE-DIAL-L", "B-ANGLE-DIAL-R", "B-CRADLE",
            "B-RETAINER-R", "B-RETAINER-TOP", "A-GRIP-CORE", "A-GRIP-PANEL-L", "A-GRIP-PANEL-R", "A-BACKSTRAP",
            "A-PALM-SHELF", "C-X-CHANNEL", "C-X-CASSETTE", "C-Z-CASSETTE", "D-SWITCH-BLADE", "PHONE"}
    assert need <= ids


def test_no_bore_or_muzzle(asm):
    """The nose and housing are closed: a ray along the axis inside the housing hits the solid nose cap."""
    nose = asm.get("A-NOSE").shape
    probe = gm.box(asm.P.housing.length - 1, asm.P.housing.length + asm.P.nose.length + 1, -1, 1, -21, -19)
    assert ck.common(nose, probe) > 0.9 * asm.P.nose.length * 4


def test_collision_matrix(asm):
    inter, n = ck.interferences(asm.parts)
    assert n > 50
    assert inter == []


def test_camera_keepout_and_sight_line(asm):
    assert ck.empty_regions(asm.parts, asm.keepouts) == []
    assert ck.empty_regions(asm.parts, [ck.sight_line_box(asm.P)]) == []


def test_active_sight_geometry(asm):
    g = sight_geometry(asm.P)
    assert 200 < g["sight_radius_mm"] < 240
    top = asm.get("S-FRONT-BLADE").shape.BoundingBox().zmax
    assert top == pytest.approx(asm.P.sight.line_z, abs=1e-3)
    nb = asm.get("S-REAR-NOTCH").shape.BoundingBox()
    assert nb.zmax == pytest.approx(asm.P.sight.line_z, abs=1e-3)   # notch shoulders define the line of sight
    assert g["sight_picture_at_assumed_eye_distance"]["light_gap_each_side_mrad"] > 0


@pytest.mark.parametrize("elev,wind", [(-1.0, -1.5), (1.0, 1.5)])
def test_rear_sight_travel(asm, elev, wind):
    mv = gm.rear_sight_parts(asm.P, elev, wind)
    static = [p for p in asm.parts if p.group != "sights"]
    assert ck.interferences(mv, static)[0] == []
    top0 = [p for p in gm.rear_sight_parts(asm.P) if p.id == "S-REAR-NOTCH"][0].shape.BoundingBox().zmax
    top1 = [p for p in mv if p.id == "S-REAR-NOTCH"][0].shape.BoundingBox().zmax
    assert math.copysign(1, top1 - top0) == math.copysign(1, elev)


@pytest.mark.parametrize("shim,lat", [(0.0, -0.8), (2.0, 0.8)])
def test_front_sight_travel(asm, shim, lat):
    mv = gm.front_sight_parts(asm.P, shim, lat)
    static = [p for p in asm.parts if p.group != "sights"]
    assert ck.interferences(mv, static)[0] == []
    b = [p for p in mv if p.id == "S-FRONT-BLADE"][0].shape.BoundingBox()
    assert b.zmax == pytest.approx(asm.P.sight.line_z + shim - asm.P.sight.front_shim_nominal, abs=1e-3)


def test_phone_landscape_orientation(asm):
    f = asm.frames
    assert abs(f["phone_long_axis_K"][1]) == pytest.approx(1.0, abs=1e-6)
    assert f["screen_normal_K"][0] == pytest.approx(-1.0, abs=1e-6)
    assert f["rear_camera_axis_K"][0] == pytest.approx(1.0, abs=1e-6)
    b = asm.get("PHONE").shape.BoundingBox()
    assert (b.ymax - b.ymin) > (b.zmax - b.zmin) > (b.xmax - b.xmin)
    assert b.zmin > asm.P.sight.line_z
    assert b.xmax < asm.P.sight.rear_base_x[0]


@pytest.mark.parametrize("angle", [-10.0, 10.0])
def test_phone_angle_extremes(asm, angle):
    P, prof = asm.P, asm.prof
    mv = gm.angle_dial_parts(P, angle) + gm.cradle_parts(P, prof, angle) + gm.phone_parts(P, prof, angle)
    static = [p for p in asm.parts if p.moving != "angle"]
    assert ck.interferences(mv, static)[0] == []
    assert ck.empty_regions(static + mv, gm.camera_keepouts(P, prof, angle)) == []
    assert ck.empty_regions(mv, [ck.sight_line_box(P)]) == []


def test_transform_chain(asm):
    f = asm.frames
    g = asm.extras["phone_geom"]
    c = asm.get("PHONE").shape.Center()
    pred = (f["T_KP"] @ np.array([-g["T"] / 2, 0, 0, 1.0]))[:3]
    assert np.linalg.norm(pred - np.array([c.x, c.y, c.z])) < 0.05
    assert np.allclose(np.linalg.inv(f["T_KG"]) @ f["T_KP"], f["T_GP"])


@pytest.mark.parametrize("pos", ["min", "max"])
def test_x_ballast_travel_and_stops(asm, pos):
    X = asm.P.x_ballast
    p = X.pos_min if pos == "min" else X.pos_max
    static = [q for q in asm.parts if q.moving != "x_ballast"]
    assert ck.interferences(gm.x_cassette_parts(asm.P, p, X.slug_max), static)[0] == []
    beyond = p - X.pos_step if pos == "min" else p + X.pos_step
    cas = [q for q in gm.x_cassette_parts(asm.P, beyond, 0) if q.id == "C-X-CASSETTE"]
    assert ck.interferences(cas, static)[0], "hard stop must engage beyond the range"
    assert X.slot_head_half - X.shoe_clear > X.slot_neck_half      # captive T-shoe


@pytest.mark.parametrize("idx", [0.0, 18.0])
def test_z_ballast_index(asm, idx):
    static = [q for q in asm.parts if q.moving != "z_ballast"]
    assert ck.interferences(gm.z_ballast_parts(asm.P, idx, asm.P.z_ballast.slug_max), static)[0] == []


def test_mirrored_grip(asm):
    lh = gm.grip_parts(asm.P, mirror=True)
    rh = gm.grip_parts(asm.P, mirror=False)
    for a, b in zip(lh, rh):
        assert a.shape.Volume() == pytest.approx(b.shape.Volume(), rel=1e-6)
        ca, cb = a.shape.Center(), b.shape.Center()
        assert ca.y == pytest.approx(-cb.y, abs=1e-3)


def test_grip_is_sculpted(asm):
    """Sections vary: palm swell wider than the waist, finger relief shallower than the neighbouring section."""
    G = asm.P.grip
    _, Df_g, _, _, wP_s = gm._gfun(G, G.swell_s)
    _, _, _, _, wP_top = gm._gfun(G, 0.0)
    assert wP_s - wP_top > 3.0
    _, Df_f, _, _, _ = gm._gfun(G, G.finger_s[0])
    _, Df_b, _, _, _ = gm._gfun(G, (G.finger_s[0] + G.finger_s[1]) / 2)
    assert Df_b - Df_f > 1.0
    core = asm.get("A-GRIP-CORE").shape
    assert ck.common(core, gm.box(-200, 300, -100, 100, -300, -40)) > 1e4


def test_mass_summary_and_solver_consistency(asm):
    s = mass_summary(asm)
    assert 800 < s["mass_g"] < 1300
    assert abs(s["com_K_mm"][1]) < 2.0
    c = solver.contributions(asm)
    b = asm.cfg["ballast"]
    e = solver.evaluate(c, asm.P, b["fixed_bars"], b["x"]["slugs"], b["x"]["position_mm"], b["z"]["slugs"],
                        b["z"]["index_mm"])
    assert e["mass_g"] == pytest.approx(s["mass_g"], abs=0.2)
    assert np.allclose(e["com"], s["com_K_mm"], atol=0.05)


def test_solver_targets(asm):
    sol = solver.solve(asm)
    st = {t["target_id"]: t for t in sol["targets"]}
    assert st["DEMO-INFEASIBLE"]["status"] == "INFEASIBLE"
    assert st["STEYR-LP10-manual-older-edition"]["status"].startswith("NO VERDICT")
    assert abs(st["STEYR-LP10-manual-older-edition"]["best"][0]["mass_g"] - 1060) < 10
    assert all("x" not in t.get("com_axes_used", []) for t in sol["targets"])     # G0-frame COM-x not used


def test_unknown_target_not_filled():
    t = {"reference_id": "X", "target_mass_g": None}
    asm_ = build(RH)
    sol = solver.solve(asm_, [t])
    assert sol["targets"][0]["status"].startswith("NOT USED")


def test_deterministic_geometry():
    a, b = build(RH), build(RH)
    for p, q in zip(a.parts, b.parts):
        assert p.id == q.id
        assert p.shape.Volume() == pytest.approx(q.shape.Volume(), rel=1e-9)


def test_profiles_share_chassis_and_grip():
    a = build(RH)
    b = build(CONF / "g1_android_placeholder_rh.json")
    for pid in ("A-HOUSING-R", "A-GRIP-CORE", "C-X-CHANNEL", "B-YOKE"):
        assert a.get(pid).shape.Volume() == pytest.approx(b.get(pid).shape.Volume(), rel=1e-9)
    assert a.get("B-CRADLE").shape.Volume() != pytest.approx(b.get("B-CRADLE").shape.Volume(), rel=1e-3)
    assert ck.empty_regions(b.parts, b.keepouts) == []


def test_manifest_matches_files():
    m = REPO / "cad/exports/g1/MANIFEST.json"
    if not m.exists():
        pytest.skip("exports not generated")
    import hashlib
    d = json.loads(m.read_text())
    assert d["files"]
    for f in d["files"]:
        p = REPO / f["file"]
        assert p.exists(), f["file"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == f["sha256"], f["file"]
    assert all(c.get("step_ok", True) and c.get("stl_ok", True) for c in d["components"])


def test_render_coverage():
    meta = REPO / "docs/cad/renders/g1/render_metadata.json"
    if not meta.exists():
        pytest.skip("renders not generated")
    d = json.loads(meta.read_text())
    names = {f["file"] for f in d["files"]}
    assert names == {"01_hero.png", "02_ergonomic_side.png", "03_rear_camera.png", "04_sight_alignment.png",
                     "05_exploded.png", "06_dimensions.png"}
    for f in d["files"]:
        assert (REPO / "docs/cad/renders/g1" / f["file"]).stat().st_size > 20000
