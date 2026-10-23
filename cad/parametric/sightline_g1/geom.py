"""G1 part builders: enclosed housing, active iron sights, landscape phone cradle on an indexed pivot yoke, sculpted
match grip (core, side panels, backstrap, palm shelf), integrated X and Z ballast, trigger guard and switch blade.

Frame K1: X toward the target, Y to the shooter's left, Z up; origin at the housing rear face, lateral centre plane,
housing top plane. Every dimension comes from ``cad/parametric/parameters/g1.json``; nothing is measured from the
reference images. All parts are passive: there is no bore, muzzle, chamber, pressure system or stored-energy part.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import cadquery as cq
import numpy as np

V = cq.Vector

NAVY = (0.17, 0.21, 0.31)
ORANGE = (0.95, 0.45, 0.06)
GREEN = (0.16, 0.46, 0.27)
STEEL = (0.74, 0.74, 0.76)
DARK = (0.10, 0.10, 0.11)
WOOD = (0.36, 0.29, 0.22)
WOOD2 = (0.29, 0.24, 0.19)
TPU = (0.06, 0.06, 0.06)
PHONE = (0.13, 0.13, 0.15)
SCREEN = (0.10, 0.22, 0.30)


@dataclass
class Part:
    id: str
    name: str
    group: str                    # housing / sights / cradle / grip / ballast_x / ballast_z / hardware / phone
    kind: str                     # printed / tpu / steel / hardware / phone / electronics / display
    material: str
    shape: cq.Shape
    color: tuple
    collide: bool = True
    export: bool = True
    phone_specific: bool = False
    mass_override_g: float | None = None
    status: str = "ESTIMATED"
    note: str = ""
    moving: str = ""              # moving interface it belongs to (angle / x_ballast / z_ballast / shelf / sight_*)
    meta: dict = field(default_factory=dict)


class A(dict):
    """Attribute access to the parameter JSON."""

    def __getattr__(self, k):
        v = self[k]
        return A(v) if isinstance(v, dict) else v


# ---------------------------------------------------------------- primitives

def box(x0, x1, y0, y1, z0, z1) -> cq.Shape:
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def rbox(x0, x1, y0, y1, z0, z1, r, sel="|X") -> cq.Shape:
    w = cq.Workplane("XY").box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    try:
        return w.edges(sel).fillet(r).val()
    except Exception:  # pragma: no cover
        return w.val()


def orient(s: cq.Shape, axis, p) -> cq.Shape:
    """Shape built along +Z at the origin, turned onto ``axis`` and moved to ``p``."""
    a = np.asarray(axis, float); a = a / np.linalg.norm(a)
    z = np.array([0.0, 0.0, 1.0])
    c = np.cross(z, a)
    if np.linalg.norm(c) < 1e-9:
        if a[2] < 0:
            s = s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    else:
        s = s.rotate(V(0, 0, 0), V(*c), math.degrees(math.acos(np.clip(a @ z, -1, 1))))
    return s.translate(V(*map(float, p)))


def cyl(p, axis, L, r) -> cq.Shape:
    return orient(cq.Solid.makeCylinder(r, L), axis, p)


def tube(p, axis, L, ro, ri) -> cq.Shape:
    return cyl(p, axis, L, ro).cut(cyl(p, axis, L, ri))


def knurl(p, axis, L, r, n=28, d=0.45) -> cq.Shape:
    pts = []
    for i in range(2 * n):
        t = math.pi * i / n
        rr = r if i % 2 == 0 else r - d
        pts.append((rr * math.cos(t), rr * math.sin(t)))
    s = cq.Workplane("XY").polyline(pts).close().extrude(L).val()
    return orient(s, axis, p)


def ellipse(c, normal, d1, r1, d2, r2) -> cq.Wire:
    if r1 >= r2:
        e = cq.Edge.makeEllipse(r1, r2, V(*c), V(*normal), V(*d1))
    else:
        e = cq.Edge.makeEllipse(r2, r1, V(*c), V(*normal), V(*d2))
    return cq.Wire.assembleEdges([e])


def solid(s) -> cq.Shape:
    """Single solid from a boolean result (largest solid if a fuse left fragments)."""
    if isinstance(s, cq.Workplane):
        s = s.val()
    sols = s.Solids()
    if len(sols) == 1:
        return sols[0]
    return max(sols, key=lambda q: q.Volume())


def fuse(*ss) -> cq.Shape:
    out = ss[0]
    for s in ss[1:]:
        out = out.fuse(s)
    return solid(out.clean())


def rotate_y(s, about, deg):
    return s.rotate(V(about[0], -1, about[2]), V(about[0], 1, about[2]), -deg)


# ---------------------------------------------------------------- housing, rail, nose, marking

def housing_parts(P) -> list:
    h = P.housing
    L, W, H, r, w, sx = h.length, h.width, h.height, h.edge_r, h.wall, h.split_x
    outer = rbox(0, L, -W / 2, W / 2, -H, 0, r)
    ri = max(r - w, 0.6)
    rear = outer.intersect(box(0, sx, -W, W, -H - 1, 1))
    rear = rear.cut(rbox(w, sx + 1, -W / 2 + w, W / 2 - w, -H + w, -w, ri))
    front = outer.intersect(box(sx, L, -W, W, -H - 1, 1))
    front = front.cut(rbox(sx - 1, L - w, -W / 2 + w, W / 2 - w, -H + w, -w, ri))
    for x in h.grip_screw_x:
        rear = rear.cut(cyl((x, 0, -H - 1), (0, 0, 1), w + 2, h.grip_screw_d / 2 + 0.2))
    s = P.switch
    rear = rear.cut(box(s.x - s.slot_half_x, s.x + s.slot_half_x, -s.slot_half_y, s.slot_half_y, -H - 1, -H + w + 1))
    rear = _marking(P, rear)
    c = h.coupler_half_len
    cl = h.coupler_clear
    cpl = rbox(sx - c, sx + c, -W / 2 + w + cl, W / 2 - w - cl, -H + w + cl, -w - cl, max(ri - cl, 0.5))
    cpl = cpl.cut(box(sx - c - 1, sx + c + 1, -W / 2 + w + cl + h.coupler_wall, W / 2 - w - cl - h.coupler_wall,
                      -H + w + cl + h.coupler_wall, -w - cl - h.coupler_wall))
    n = P.nose
    nose = rbox(L, L + n.length, -W / 2, W / 2, -H, 0, r)
    try:
        nose = cq.Workplane().add(nose).faces(">X").edges().fillet(3.0).val()
    except Exception:  # pragma: no cover
        pass
    ra = P.rail
    rail = rbox(ra.x0, ra.x1, -ra.half_w, ra.half_w, 0, ra.h, 1.0, "|X")
    ticks = None
    k = 0
    x = ra.x0 + 2
    while x <= ra.x1 - 2:
        hh = 2.6 if k % 5 == 0 else 1.4
        t = box(x - 0.2, x + 0.2, ra.half_w - ra.tick_depth, ra.half_w + 0.1, ra.h - hh, ra.h + 0.1)
        ticks = t if ticks is None else ticks.fuse(t)
        x += ra.tick_pitch
        k += 1
    rail = solid(rail.cut(ticks))
    sp = P.service_plate
    plate = rbox(sp.x0, sp.x1, -W / 2 - sp.t, -W / 2, sp.z0, sp.z1, 1.2, "|Y")
    for i in range(4):
        gx = sp.x0 + 12 + i * 8.5
        plate = plate.cut(box(gx - 1.2, gx + 1.2, -W / 2 - sp.t - 0.1, -W / 2 - sp.t + 1.2, sp.z0 + 3, sp.z1 - 3))
    out = [
        Part("A-HOUSING-R", "Housing, rear half (enclosed shell, grip and switch mounting)", "housing", "printed", "PETG",
             solid(rear), NAVY, note="no bore, no muzzle; closed shell"),
        Part("A-HOUSING-F", "Housing, front half (fixed-ballast bay, X-ballast channel mount)", "housing", "printed",
             "PETG", solid(front), NAVY),
        Part("A-HOUSING-COUPLER", "Housing coupler (joins the halves inside the cavity)", "housing", "printed", "PETG",
             solid(cpl), DARK),
        Part("A-NOSE", "High-visibility nose cap (solid, no opening)", "housing", "printed", "PETG", solid(nose), ORANGE),
        Part("A-RAIL", "Orange precision rail with 5 mm scale", "housing", "printed", "PETG", rail, ORANGE),
        Part("A-SERVICE-PLATE", "Orange side service plate (covers the coupler screws)", "housing", "printed", "PETG",
             solid(plate), ORANGE),
    ]
    return out


def _marking(P, shape):
    m, h = P.marking, P.housing
    try:
        for i, txt in enumerate((m.line1, m.line2)):
            zc = -h.height * (0.36 + 0.2 * i)
            pl = cq.Plane(origin=(m.x0 + 92.0 if i == 0 else m.x0 + 92.0, h.width / 2, zc), xDir=(-1, 0, 0),
                          normal=(0, 1, 0))
            t = cq.Workplane(pl).text(txt, m.font_h, -m.depth, combine=False, halign="left", valign="center").val()
            shape = shape.cut(t)
    except Exception:  # pragma: no cover - font back end missing
        pass
    return shape


# ---------------------------------------------------------------- sights

def rear_sight_parts(P, elev=0.0, wind=0.0) -> list:
    s, ra = P.sight, P.rail
    zs = s.line_z
    bx0, bx1 = s.rear_base_x
    hx = s.rear_hinge_x
    base = box(bx0, bx1, -10, 10, ra.h, ra.h + 4)
    for sg in (1, -1):
        base = base.fuse(box(bx0, bx1, sg * (ra.half_w + 0.2), sg * 10, 1.5, ra.h))
    base = base.fuse(box(hx - 3, hx + 3, -6.5, 6.5, ra.h + 4, ra.h + 7.5))
    pin_z = ra.h + 6.0
    base = base.cut(cyl((hx, -12, pin_z), (0, 1, 0), 24, 1.3))
    base = base.cut(cyl((s.rear_elev_screw_x, 0, ra.h - 0.5), (0, 0, 1), 6, 1.5))
    leaf_z0 = ra.h + 7.7
    leaf = box(hx - 3, bx1, -9, 9, leaf_z0, leaf_z0 + 4)
    for sg in (1, -1):
        leaf = leaf.fuse(box(hx - 3, hx + 3, sg * 6.7, sg * 9, ra.h + 4.3, leaf_z0))
    leaf = leaf.cut(cyl((hx, -12, pin_z), (0, 1, 0), 24, 1.3))
    leaf = leaf.cut(cyl((s.rear_elev_screw_x, 0, leaf_z0 - 1), (0, 0, 1), 6, 2.1))   # clearance for the leaf tilt
    wz = leaf_z0 + 2.0
    leaf = leaf.cut(cyl((58.0, -10, wz), (0, 1, 0), 20, 1.6))
    top = leaf_z0 + 4
    nx0, nx1 = s.rear_notch_x
    slide = box(56.0, nx0, -10 + wind, 10 + wind, top, top + 1.5)
    notch = box(nx0, nx1, -11.0 + wind, 11.0 + wind, top, zs + s.notch_depth)
    notch = notch.cut(box(nx0 - 1, nx1 + 1, -s.notch_w / 2 + wind, s.notch_w / 2 + wind, zs, zs + 10))
    pin = cyl((hx, -9, pin_z), (0, 1, 0), 18, 1.25)
    escrew = cyl((s.rear_elev_screw_x, 0, ra.h + 0.5), (0, 0, 1), top - ra.h + 1.0, 1.5)
    eknob = knurl((s.rear_elev_screw_x, 0, top), (0, 0, 1), min(2.8, zs - 0.5 - top), 4.0).cut(
        cyl((s.rear_elev_screw_x, 0, top - 1), (0, 0, 1), 5, 1.5))
    wscrew = cyl((58.0, -14, wz), (0, 1, 0), 20, 1.5)
    wknob = knurl((58.0, -14, wz), (0, -1, 0), 6, 4.0)
    spring = tube((s.rear_elev_screw_x, 0, ra.h + 4), (0, 0, 1), leaf_z0 - ra.h - 4, 3.0, 1.9)
    mv = "sight_rear"
    nxc = (nx0 + nx1) / 2
    ang = math.degrees(math.atan2(elev, nxc - hx))
    # the elevation screw stays in the base thread; everything carried by the leaf turns about the hinge pin
    leaf, slide, notch, eknob, wscrew, wknob = [rotate_y(q, (hx, 0, pin_z), ang) for q in
                                                (leaf, slide, notch, eknob, wscrew, wknob)]
    parts = [
        Part("S-REAR-BASE", "Rear sight base (clamps the rail)", "sights", "printed", "PETG", solid(base), DARK),
        Part("S-REAR-LEAF", "Rear sight elevation leaf (hinged, screw-set)", "sights", "printed", "PETG", solid(leaf),
             DARK, moving=mv),
        Part("S-REAR-SLIDE", "Rear sight windage slide", "sights", "printed", "PETG", solid(slide), DARK, moving=mv),
        Part("S-REAR-NOTCH", f"Rear notch insert ({s.notch_w:g} mm notch), replaceable", "sights", "printed", "PETG",
             solid(notch), DARK, moving=mv),
        Part("H-REAR-PIN", "Rear sight hinge pin Ø2.5", "sights", "hardware", "steel", pin, STEEL, export=False),
        Part("H-REAR-ELEV", "Elevation screw M3", "sights", "hardware", "steel", escrew, STEEL, export=False),
        Part("H-REAR-ELEV-KNOB", "Elevation knob (knurled)", "sights", "hardware", "steel", eknob, STEEL,
             export=False),
        Part("H-REAR-SPRING", "Elevation return spring (compliant envelope)", "sights", "hardware", "steel", spring,
             STEEL, collide=False, export=False, mass_override_g=0.4),
        Part("H-REAR-WIND", "Windage screw M3", "sights", "hardware", "steel", wscrew, STEEL, export=False),
        Part("H-REAR-WIND-KNOB", "Windage knob (knurled, right side)", "sights", "hardware", "steel", wknob, STEEL,
             export=False),
    ]
    return parts


def front_sight_parts(P, shim=None, lat=0.0) -> list:
    s = P.sight
    t = s.front_shim_nominal if shim is None else shim
    zs = s.line_z
    bx0, bx1 = s.front_base_x
    wi, ch = s.front_wall_inner, s.front_carrier_half_w
    base = box(bx0, bx1, -8, 8, 0, 6)
    for sg in (1, -1):
        base = base.fuse(box(bx0, bx1, sg * wi, sg * 8, 6, 12))
    slot = box(274.4, 277.6, -9, 9, 6.9, 11.1)
    base = base.cut(slot)
    c0 = 6 + t
    shim_p = box(274, 285, -ch, ch, 6, c0) if t > 1e-6 else None
    carrier = box(274, 285, -ch + lat, ch + lat, c0, c0 + 4)
    carrier = carrier.cut(cyl((276, -9, c0 + 2), (0, 1, 0), 18, 1.6))
    fx0, fx1 = s.front_blade_x
    blade_top = zs + (t - s.front_shim_nominal)
    blade = box(fx0, fx1, -s.blade_w / 2 + lat, s.blade_w / 2 + lat, c0 + 4, blade_top)
    lshim = box(274, 285, ch + lat, wi, c0, c0 + 4)
    rshim = box(274, 285, -wi, -ch + lat, c0, c0 + 4)
    lshim = lshim.cut(cyl((276, -9, c0 + 2), (0, 1, 0), 18, 1.6))
    rshim = rshim.cut(cyl((276, -9, c0 + 2), (0, 1, 0), 18, 1.6))
    screw = cyl((276, -9.5, c0 + 2), (0, 1, 0), 19, 1.5)
    mv = "sight_front"
    out = [
        Part("S-FRONT-BASE", "Front sight base (U-channel, screwed to the housing)", "sights", "printed", "PETG",
             solid(base), DARK),
        Part("S-FRONT-CARRIER", "Front blade carrier", "sights", "printed", "PETG", solid(carrier), DARK, moving=mv),
        Part("S-FRONT-BLADE", f"Front blade {s.blade_w:g} mm, high-contrast, replaceable", "sights", "printed", "PETG",
             solid(blade), ORANGE, moving=mv),
        Part("S-FRONT-LSHIM-L", "Lateral shim, left", "sights", "printed", "PETG", solid(lshim), DARK, moving=mv),
        Part("S-FRONT-LSHIM-R", "Lateral shim, right", "sights", "printed", "PETG", solid(rshim), DARK, moving=mv),
        Part("H-FRONT-CLAMP", "Front sight clamp screw M3", "sights", "hardware", "steel", screw, STEEL, export=False,
             moving=mv),
    ]
    if shim_p is not None:
        out.append(Part("S-FRONT-SHIM", f"Elevation shim {t:g} mm", "sights", "printed", "PETG", solid(shim_p), DARK,
                        moving=mv, meta={"t": t}))
    return out


# ---------------------------------------------------------------- yoke, angle plates, cradle, phone

def pivot_point(P):
    y = P.yoke
    return np.array([y.pivot_x, 0.0, P.sight.line_z + y.pivot_clear_above_line])


def yoke_parts(P) -> list:
    y, ra = P.yoke, P.rail
    px, _, pz = pivot_point(P)
    base = box(y.x0, y.x1, -y.half_w, y.half_w, ra.h, ra.h + y.base_t)
    for sg in (1, -1):
        base = base.fuse(box(y.x0, y.x1, sg * (ra.half_w + 0.2), sg * 10, 1.5, ra.h))
    ups = []
    for sg in (1, -1):
        yi, yo = sg * (y.half_w - y.upright_t), sg * y.half_w
        up = box(px - 8, px + 8, yi, yo, ra.h + y.base_t, pz)
        up = up.fuse(cyl((px, min(yi, yo), pz), (0, 1, 0), y.upright_t, 8.0))
        ups.append(up)
    yoke = fuse(base, *ups)
    yoke = yoke.cut(cyl((px, -y.half_w - 1, pz), (0, 1, 0), 2 * y.half_w + 2, y.shaft_d / 2 + 0.1))
    # detent pin holes (the pin sits in the upright and engages the dial index holes)
    for sg in (1, -1):
        yoke = yoke.cut(cyl((px, sg * (y.half_w - 3), pz - 12), (0, sg, 0), 4, 0.8))
    out = [Part("B-YOKE", "Pivot yoke (two uprights straddling the sight line)", "cradle", "printed", "PETG",
                solid(yoke), DARK)]
    for sg, tag in ((1, "L"), (-1, "R")):
        pin = cyl((px, sg * (y.half_w - 3), pz - 12), (0, sg, 0), 4.0, 0.75)
        out.append(Part(f"H-DETENT-{tag}", f"Angle detent pin Ø1.5 ({tag})", "cradle", "hardware", "steel", pin, STEEL,
                        export=False))
    return out


def angle_dial_parts(P, angle=0.0) -> list:
    y = P.yoke
    piv = pivot_point(P)
    px, _, pz = piv
    out = []
    n = int(round((y.angle_range_deg[1] - y.angle_range_deg[0]) / y.index_step_deg))
    for sg, tag in ((1, "L"), (-1, "R")):
        y0 = y.half_w if sg > 0 else -y.half_w - y.plate_t
        d = cyl((px, y0, pz), (0, 1, 0), y.plate_t, y.plate_d / 2)
        d = d.cut(cyl((px, y0 - 1, pz), (0, 1, 0), y.plate_t + 2, y.shaft_d / 2))
        for k in range(n + 1):
            a = math.radians(-90 + y.angle_range_deg[0] + k * y.index_step_deg)
            d = d.cut(cyl((px + 12 * math.cos(a), y0 - 1, pz + 12 * math.sin(a)), (0, 1, 0), y.plate_t + 2, 0.8))
        # engraved index ticks on the outer face
        for k in range(n + 1):
            a = math.radians(-90 + y.angle_range_deg[0] + k * y.index_step_deg)
            r0, r1 = 13.8, 15.6
            tk = box(-0.25, 0.25, 0, 0.5, r0, r1)
            tk = tk.rotate(V(0, 0, 0), V(0, 1, 0), -(math.degrees(a) - 90))
            yy = y0 + y.plate_t - 0.4 if sg > 0 else y0 - 0.1
            d = d.cut(tk.translate(V(px, yy, pz)))
        d = rotate_y(solid(d), piv, angle)
        ky0 = y.half_w + y.plate_t if sg > 0 else -y.half_w - y.plate_t - y.knob_l
        kn = knurl((px, ky0, pz), (0, 1, 0), y.knob_l, y.knob_d / 2).cut(
            cyl((px, ky0 - 1, pz), (0, 1, 0), y.knob_l + 2, y.shaft_d / 2))
        out.append(Part(f"B-ANGLE-DIAL-{tag}", f"Indexed angle dial ({tag}), {y.index_step_deg:g}° steps, "
                        f"{y.angle_range_deg[0]:g}…{y.angle_range_deg[1]:g}°", "cradle", "printed", "PETG", d, STEEL,
                        moving="angle"))
        out.append(Part(f"H-ANGLE-KNOB-{tag}", f"Angle lock knob ({tag}, knurled)", "cradle", "hardware", "steel",
                        solid(kn), STEEL, export=False, moving="angle"))
    sh = cyl((px, -y.half_w - y.plate_t - y.knob_l, pz), (0, 1, 0), 2 * (y.half_w + y.plate_t + y.knob_l), y.shaft_d / 2)
    out.append(Part("H-PIVOT-SHAFT", "Pivot shaft Ø6 (keyed to the cradle and dials)", "cradle", "hardware", "steel",
                    sh, STEEL, export=False, moving="angle"))
    return out


def phone_geometry(P, prof):
    """Phone placement in K1 at angle 0: landscape, long axis along Y, screen toward the shooter (−X), back and rear
    cameras toward the target (+X), top end toward +Y."""
    c = P.cradle
    ca = c.case_allowance
    L, W, T = prof["L"] + 2 * ca, prof["W"] + 2 * ca, prof["T"] + 2 * ca
    piv = pivot_point(P)
    x_back = c.back_x
    z_bot = piv[2] + c.beam_above_pivot + c.beam_t + c.ledge_pad_t
    return {"L": L, "W": W, "T": T, "x_back": x_back, "x_front": x_back - T, "z_bot": z_bot, "z_top": z_bot + W,
            "y_top_end": L / 2, "Rc": prof["Rc"]}


def cradle_parts(P, prof, angle=0.0) -> list:
    c, y = P.cradle, P.yoke
    g = phone_geometry(P, prof)
    piv = pivot_point(P)
    px, _, pz = piv
    L, Wp = g["L"], g["W"]
    xf, xb, zb, zt = g["x_front"], g["x_back"], g["z_bot"], g["z_top"]
    hub = cyl((px, -(y.half_w - y.upright_t) + 0.4, pz), (0, 1, 0), 2 * (y.half_w - y.upright_t) - 0.8, y.hub_d / 2)
    zb0 = pz + c.beam_above_pivot
    zb1 = zb0 + c.beam_t
    web = box(px - 5, px + 5, -(y.half_w - y.upright_t) + 0.4, (y.half_w - y.upright_t) - 0.4, pz, zb1)
    beam = box(xf - 0.2, xb + c.back_t, -L / 2 - c.beam_half_extra, L / 2 + c.beam_half_extra, zb0, zb1)
    bp_top = zt + 19
    back = box(xb + c.pad_t, xb + c.pad_t + c.back_t - 1, -c.back_half_w, c.back_half_w, zb0, bp_top)
    bracket = box(xf + 1, xb + c.pad_t + c.back_t - 1, -12, 12, zt + 14, zt + 19)
    datum = box(xf + 0.0, xb + c.pad_t + c.back_t - 1, L / 2, L / 2 + c.end_block_t, zb0, zb + c.end_block_h)
    lip = box(xf - c.lip, xf, L / 2 - c.lip, L / 2 + c.end_block_t, zb + 8, zb + 20)
    boss = box(xf + 1, xb + c.pad_t + c.back_t - 2, -L / 2 - 14, -L / 2 - 8, zb0, zb + 16)
    cr = fuse(hub, web, beam, back, bracket, datum, lip, boss)
    cr = cr.cut(cyl((px, -30, pz), (0, 1, 0), 60, y.shaft_d / 2))
    sy = (xf + xb) / 2 + 2.0
    cr = cr.cut(cyl((sy, -L / 2 - 15, zb + 9), (0, 1, 0), 8, 2.1))
    cr = cr.cut(cyl((sy - 2.0 - 1.4, 0, zt + 13), (0, 0, 1), 8, 2.1))
    cradle = solid(cr)
    # right retainer (preload toward the +Y datum) with lip over the frame edge
    ret = box(xf, xb + c.pad_t + c.back_t - 2, -L / 2 - c.end_block_t, -L / 2, zb + 2, zb + c.end_block_h)
    ret = ret.fuse(box(xf - c.lip, xf, -L / 2 - c.end_block_t, -L / 2 + c.lip, zb + 8, zb + 20))
    ret = solid(ret.cut(cyl((sy, -L / 2 - c.end_block_t - 1, zb + 9), (0, 1, 0), 4, 2.0)))
    rscrew = cyl((sy, -L / 2 - 22, zb + 9), (0, 1, 0), 22 - c.end_block_t + 3, 2.0)
    rknob = knurl((sy, -L / 2 - 22, zb + 9), (0, 1, 0), 8, 7.0).cut(cyl((sy, -L / 2 - 23, zb + 9), (0, 1, 0), 10, 2.0))
    # top anti-lift retainer: pad on the top edge, stem in front of the back plate, screw through the bracket
    tx = sy - 3.4
    tp_y = L / 2 - c.top_pad_from_top
    tret = box(xf + 0.4, xb + c.pad_t - 0.2, tp_y - 8, tp_y + 8, zt, zt + 3)
    stem = box(tx - 2.6, xb + c.pad_t - 0.2, -10, 10, zt, zt + 12)
    tret = solid(fuse(tret, box(tx - 2.6, xb + c.pad_t - 0.2, min(-10, tp_y - 8), max(10, tp_y + 8), zt + 2, zt + 3),
                      stem).cut(cyl((tx, 0, zt + 6), (0, 0, 1), 7, 2.0)))
    tscrew = cyl((tx, 0, zt + 7), (0, 0, 1), 20, 2.0)
    tknob = knurl((tx, 0, zt + 19), (0, 0, 1), 7, 6.0).cut(cyl((tx, 0, zt + 18), (0, 0, 1), 9, 2.0))
    # TPU pads: three back pads (datum A), two ledge pads (datum B); the +Y end block is datum C
    pads = []
    for i, (py, pzz) in enumerate(((20.0, zb + 16), (-20.0, zb + 16), (0.0, zt - 14))):
        pads.append(Part(f"B-PAD-BACK-{i + 1}", "Back pad (datum A), TPU 95A, replaceable", "cradle", "tpu", "TPU",
                         box(xb, xb + c.pad_t, py - 5, py + 5, pzz - 5, pzz + 5), TPU, phone_specific=True,
                         moving="angle"))
    for i, ft in enumerate(c.ledge_pad_from_top):
        py = L / 2 - ft
        pads.append(Part(f"B-PAD-LEDGE-{i + 1}", "Ledge pad (datum B), TPU 95A", "cradle", "tpu", "TPU",
                         box(xf + 0.6, xb - 0.6, py - 6, py + 6, zb1, zb), TPU, phone_specific=True,
                         moving="angle", meta={"from_top": ft}))
    parts = [
        Part("B-CRADLE", f"Landscape cradle for {prof['id']} (hub, ledge beam, back plate, +Y datum, bracket)",
             "cradle", "printed", "PETG", cradle, DARK, phone_specific=True, moving="angle"),
        Part("B-RETAINER-R", "Right retainer (screw preload toward the +Y datum)", "cradle", "printed", "PETG", ret,
             DARK, phone_specific=True, moving="angle"),
        Part("B-RETAINER-TOP", "Upper anti-lift retainer", "cradle", "printed", "PETG", tret, DARK,
             phone_specific=True, moving="angle"),
        Part("H-RET-R-SCREW", "Retainer screw M4 (nylon)", "cradle", "hardware", "nylon", rscrew, STEEL, export=False,
             moving="angle", mass_override_g=0.6),
        Part("H-RET-R-KNOB", "Retainer knob (knurled)", "cradle", "hardware", "aluminium", rknob, STEEL, export=False,
             moving="angle", mass_override_g=2.6),
        Part("H-RET-TOP-SCREW", "Top retainer screw M4 (nylon)", "cradle", "hardware", "nylon", tscrew, STEEL,
             export=False, moving="angle", mass_override_g=0.5),
        Part("H-RET-TOP-KNOB", "Top retainer knob (knurled)", "cradle", "hardware", "aluminium", tknob, STEEL,
             export=False, moving="angle", mass_override_g=2.0),
    ] + pads
    for p in parts:
        p.shape = rotate_y(p.shape, piv, angle)
    return parts


def phone_parts(P, prof, angle=0.0) -> list:
    g = phone_geometry(P, prof)
    piv = pivot_point(P)
    L, Wp, T = g["L"], g["W"], g["T"]
    r = min(g["Rc"], Wp / 2 - 1)
    body = (cq.Workplane("YZ", origin=(g["x_front"], 0, g["z_bot"] + Wp / 2)).rect(L, Wp).extrude(T)
            .edges("|X").fillet(r).val())
    try:
        body = cq.Workplane().add(body).faces("<X or >X").edges().fillet(1.2).val()
    except Exception:  # pragma: no cover
        pass
    scr = (cq.Workplane("YZ", origin=(g["x_front"] - 0.05, 0, g["z_bot"] + Wp / 2)).rect(L - 6, Wp - 6).extrude(0.05)
           .edges("|X").fillet(max(r - 3, 1)).val())
    m = prof["mass"]
    out = [Part("PHONE", f"{prof['device']} (landscape; screen −X, rear cameras +X, top end +Y)", "phone", "phone",
                "phone", rotate_y(body, piv, angle), PHONE, export=False, mass_override_g=m["v"],
                status=m["s"], moving="angle"),
           Part("PHONE-SCREEN", "Display face (visual only)", "phone", "display", "-", rotate_y(scr, piv, angle),
                SCREEN, collide=False, export=False, mass_override_g=0.0, moving="angle")]
    return out


def camera_keepouts(P, prof, angle=0.0) -> list:
    """Both short-end zones of the phone back, extended 30 mm toward the target (camera positions are pending, so
    either landscape direction is kept clear)."""
    c = P.cradle
    g = phone_geometry(P, prof)
    piv = pivot_point(P)
    e, d, m = c.camera_keepout_end_zone, c.camera_keepout_depth, c.camera_keepout_margin
    out = []
    for sg in (1, -1):
        ya, yb = sg * (g["L"] / 2 - m), sg * (g["L"] / 2 - e)
        k = box(g["x_back"] + 0.05, g["x_back"] + d, ya, yb, g["z_bot"] + m, g["z_top"] - m)
        out.append(rotate_y(k, piv, angle))
    return out


# ---------------------------------------------------------------- grip

def _gfun(G, s):
    a = math.radians(G.rake_deg)
    xc = G.top_x - s * math.tan(a)
    sw = math.exp(-((s - G.swell_s) / G.swell_r) ** 2)
    fg = sum(math.exp(-((s - sk) / G.finger_sigma) ** 2) for sk in G.finger_s)
    Df = G.front_depth - G.finger_depth * fg
    Db = (G.back_depth + G.rear_swell_h * math.exp(-((s - 50.0) / 30.0) ** 2)
          + G.heel_h * math.exp(-((s - G.heel_s) / G.heel_sigma) ** 2))
    wT = G.half_w_thumb + 1.0 * sw
    wP = G.half_w_palm + G.swell_h * sw
    return xc, Df, Db, wT, wP


def grip_section(P, s, back_delta=0.0, n=56):
    G = P.grip
    xc, Df, Db, wT, wP = _gfun(G, s)
    Db += back_delta
    z = -P.housing.height - s
    e = 2.0 / G.superellipse_n
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        u, v = math.cos(t), math.sin(t)
        a = Df if u >= 0 else Db
        b = wT if v >= 0 else wP
        pts.append(V(xc + math.copysign(abs(u) ** e, u) * a, math.copysign(abs(v) ** e, v) * b, z))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)])


def _grip_body(P, back_delta=0.0):
    G = P.grip
    ss = list(np.arange(0.0, G.length + 1e-6, G.station_step))
    if ss[-1] < G.length:
        ss.append(G.length)
    body = cq.Solid.makeLoft([grip_section(P, s, back_delta) for s in ss], False)
    H = P.housing.height
    xc0, Df0, Db0, _, _ = _gfun(G, 0.0)
    xb = xc0 - Db0 - back_delta
    secs = []
    for dx, ry, rz in ((8, 13, 7), (0, 13, 7), (-8, 12, 6), (-16, 9.5, 4.6), (-G.beavertail_len, 5.5, 2.6)):
        secs.append(ellipse((xb + dx, 0, -H - 6.0 + (0 if dx >= 0 else dx * 0.03)), (1, 0, 0), (0, 1, 0),
                            ry * G.beavertail_half_w / 13, (0, 0, 1), rz * G.beavertail_half_h / 7))
    bt = cq.Solid.makeLoft(secs, False).intersect(box(-100, 200, -60, 60, -300, -H))
    body = body.fuse(bt)
    st = G.thumb_rest_s
    xc, Df, Db, wT, wP = _gfun(G, st)
    x1 = xc - 0.55 * Db
    secs = []
    for f, sy, sz in ((0.0, 0.45, 0.6), (0.33, 1.0, 1.0), (0.7, 1.0, 1.0), (1.0, 0.5, 0.6)):
        ry = (G.thumb_rest_proud / 2 + 2.5) * sy
        secs.append(ellipse((x1 + f * G.thumb_rest_len, wT - 3.0 + G.thumb_rest_proud / 2, -H - st), (1, 0, 0),
                            (0, 1, 0), ry, (0, 0, 1), G.thumb_rest_half_t * sz))
    tr = cq.Solid.makeLoft(secs, False)
    body = body.fuse(tr)
    return solid(body.clean())


def _local_region(P, x0, x1, y0, y1):
    """Box bounded by planes parallel to the grip axis (local x across the axis, measured from it)."""
    G = P.grip
    H = P.housing.height
    b = box(x0, x1, y0, y1, -400, 60)
    return b.rotate(V(0, 0, 0), V(0, 1, 0), G.rake_deg).translate(V(G.top_x, 0, -H))


def _axis_pt(P, s, off=0.0):
    G = P.grip
    a = math.radians(G.rake_deg)
    return np.array([G.top_x - s * math.tan(a) + off, 0.0, -P.housing.height - s])


def _axis_dir(P):
    a = math.radians(P.grip.rake_deg)
    return np.array([-math.sin(a), 0.0, -math.cos(a)])


def _sheared(P, s0, s1, ox0, ox1, y0, y1):
    """Prism between two horizontal rectangles that follows the grip rake."""
    w = []
    for s in (s0, s1):
        p = _axis_pt(P, s)
        w.append(cq.Wire.makePolygon([V(p[0] + ox0, y0, p[2]), V(p[0] + ox1, y0, p[2]), V(p[0] + ox1, y1, p[2]),
                                      V(p[0] + ox0, y1, p[2])], close=True))
    return cq.Solid.makeLoft(w, True)


def grip_parts(P, drop=None, shelf_angle=None, backstrap_delta=0.0, mirror=None) -> list:
    G, PS, Z = P.grip, P.palm_shelf, P.z_ballast
    H = P.housing.height
    drop = PS.drop if drop is None else drop
    shelf_angle = PS.angle_deg if shelf_angle is None else shelf_angle
    left = (G.hand == "left") if mirror is None else mirror
    body = _grip_body(P)
    sy = G.panel_split_y
    bo = G.backstrap_offset
    core_reg = _local_region(P, bo, 200, -sy, sy)
    back_reg = _local_region(P, -200, bo, -sy, sy)
    core = body.intersect(core_reg)
    bs_body = _grip_body(P, backstrap_delta) if backstrap_delta else body
    back = bs_body.intersect(back_reg)
    pl = body.intersect(box(-200, 300, sy, 200, -400, 0))
    pr = body.intersect(box(-200, 300, -200, -sy, -400, 0))
    # grip-to-housing screws
    for x in P.housing.grip_screw_x:
        core = core.cut(cyl((x, 0, -H - 16), (0, 0, 1), 16.5, 2.1))
    # panel through-bolts (along Y) and backstrap screws (along X)
    bolts = []
    for s in G.panel_screw_s:
        p = _axis_pt(P, s, 9.0)
        hole = cyl((p[0], -60, p[2]), (0, 1, 0), 120, G.hole_d / 2)
        core, pl, pr = core.cut(hole), pl.cut(hole), pr.cut(hole)
        _, _, _, wT, wP = _gfun(G, s)
        bolts.append(cyl((p[0], -(wP - 2.5), p[2]), (0, 1, 0), wT + wP - 5.0, G.screw_d / 2))
    bs_screws = []
    for s in G.backstrap_screw_s:
        xc, Df, Db, _, _ = _gfun(G, s)
        p = _axis_pt(P, s)
        hole = cyl((xc - Db - 10, 0, p[2]), (1, 0, 0), Db + 8, G.hole_d / 2)
        core, back = core.cut(hole), back.cut(hole)
        bs_screws.append(cyl((xc - Db + 2.5 - backstrap_delta * 0, 0, p[2]), (1, 0, 0), Db - 5.5, G.screw_d / 2))
    # Z ballast bore along the grip axis
    Lb = Z.cass_len + Z.travel
    s_top = G.length - Lb
    d = _axis_dir(P)
    bore = cyl(_axis_pt(P, s_top, Z.axis_offset), d, Lb + 30, Z.bore_d / 2)
    core = core.cut(bore)
    # palm-shelf tongue pocket
    pk0, pk1 = G.pocket_local_x
    pocket = _sheared(P, G.length - G.pocket_depth, G.length + 5, pk0, pk1, -G.pocket_half_w, G.pocket_half_w)
    core = core.cut(pocket)
    # palm-shelf cross pin hole (indexed height)
    s_pin = G.length - 9.0
    pp = _axis_pt(P, s_pin, (pk0 + pk1) / 2)
    pin_hole = cyl((pp[0], -60, pp[2]), (0, 1, 0), 120, 2.1)
    core, pl, pr = core.cut(pin_hole), pl.cut(pin_hole), pr.cut(pin_hole)
    xcb, Dfb, Dbb, wTb, wPb = _gfun(G, G.length)
    pin = cyl((pp[0], -(wPb - 1.5), pp[2]), (0, 1, 0), wPb + wTb - 3.0, 2.0)
    # palm shelf
    zs = -H - G.length - drop
    pbase = _axis_pt(P, G.length)
    plate = rbox(pbase[0] - PS.rear, pbase[0] + PS.front, -PS.half_w_palm, PS.half_w_thumb, zs - PS.t, zs, 3.0, "|Z")
    wing_y0 = -wPb - 0.6
    ta = math.tan(math.radians(shelf_angle))
    yo = -PS.half_w_palm
    wing_pts = [(wing_y0, zs - 0.01), (yo, zs - 0.01), (yo, zs + 3.0 + (wing_y0 - yo) * ta), (wing_y0, zs + 3.0)]
    wing = (cq.Workplane("YZ", origin=(pbase[0] - PS.rear + 4, 0, 0)).polyline(wing_pts).close()
            .extrude(PS.rear + PS.front - 8).val())
    tongue = _sheared(P, G.length - G.pocket_depth + 0.5, G.length + drop, pk0 + 0.2, pk1 - 0.2,
                      -G.pocket_half_w + 0.2, G.pocket_half_w - 0.2)
    shelf = fuse(plate, wing, tongue)
    for dk in PS.drop_positions:
        hp = _axis_pt(P, s_pin - dk + drop, (pk0 + pk1) / 2)
        shelf = shelf.cut(cyl((hp[0], -20, hp[2]), (0, 1, 0), 40, 2.1))
    # Z ballast stack: top spacer, cassette with slugs, bottom spacer cut flat on the shelf
    parts = [
        Part("A-GRIP-CORE", "Sculpted grip core (Z-ballast bore, shelf pocket, panel and backstrap bosses)", "grip",
             "printed", "PETG", solid(core), WOOD),
        Part("A-GRIP-PANEL-L", "Grip side panel, thumb side (thumb rest), replaceable", "grip", "printed", "PETG",
             solid(pl), WOOD2),
        Part("A-GRIP-PANEL-R", "Grip side panel, palm side (palm swell), replaceable", "grip", "printed", "PETG",
             solid(pr), WOOD2),
        Part("A-BACKSTRAP", f"Backstrap with beavertail (variant offset {backstrap_delta:+g} mm), replaceable", "grip",
             "printed", "PETG", solid(back), WOOD, meta={"delta": backstrap_delta}),
        Part("A-PALM-SHELF", f"Adjustable palm shelf (drop {drop:g} mm, wing angle {shelf_angle:+g}°)", "grip",
             "printed", "PETG", solid(shelf), WOOD2, moving="shelf", meta={"drop": drop, "angle": shelf_angle}),
        Part("H-SHELF-PIN", "Palm-shelf index pin Ø4 (knurled head)", "grip", "hardware", "steel", pin, STEEL,
             export=False),
    ]
    for i, b in enumerate(bolts):
        parts.append(Part(f"H-PANEL-BOLT-{i + 1}", "Panel through-bolt M3", "grip", "hardware", "steel", b, STEEL,
                          export=False))
    for i, b in enumerate(bs_screws):
        parts.append(Part(f"H-BACKSTRAP-SCREW-{i + 1}", "Backstrap screw M3", "grip", "hardware", "steel", b, STEEL,
                          export=False))
    for i, x in enumerate(P.housing.grip_screw_x):
        parts.append(Part(f"H-GRIP-SCREW-{i + 1}", "Grip screw M4 (from inside the housing)", "grip", "hardware",
                          "steel", fuse(cyl((x, 0, -H - 14), (0, 0, 1), 14 + P.housing.wall, 2.0),
                                        cyl((x, 0, -H + P.housing.wall), (0, 0, 1), 2.4, 3.4)), STEEL, export=False))
    if left:
        for p in parts:
            p.shape = p.shape.mirror("XZ")
            if "PANEL-L" in p.id:
                p.name = p.name.replace("thumb side", "palm side (mirrored)")
            elif "PANEL-R" in p.id:
                p.name = p.name.replace("palm side", "thumb side (mirrored)")
    return parts


def z_ballast_parts(P, idx_mm=6.0, n_slugs=3, drop=None, mirror=False) -> list:
    G, Z, PS = P.grip, P.z_ballast, P.palm_shelf
    H = P.housing.height
    drop = PS.drop if drop is None else drop
    d = _axis_dir(P)
    Lb = Z.cass_len + Z.travel
    s_top = G.length - Lb
    out = []
    zs_top = -H - G.length - drop
    if idx_mm > 1e-6:
        sp = cyl(_axis_pt(P, s_top, Z.axis_offset), d, idx_mm, Z.cass_d / 2)
        out.append(Part("C-Z-SPACER-T", f"Z index spacer {idx_mm:g} mm (above the cassette)", "ballast_z", "printed",
                        "PETG", sp, GREEN, moving="z_ballast", meta={"len": idx_mm}))
    s0 = s_top + idx_mm
    cas = cyl(_axis_pt(P, s0, Z.axis_offset), d, Z.cass_len, Z.cass_d / 2)
    cas = cas.cut(cyl(_axis_pt(P, s0 + Z.cass_wall, Z.axis_offset), d, Z.cass_len, Z.cass_d / 2 - Z.cass_wall))
    out.append(Part("C-Z-CASSETTE", "Z ballast cassette (captive in the grip bore)", "ballast_z", "printed",
                    "PETG-ballast-cassette", solid(cas), GREEN, moving="z_ballast"))
    for k in range(n_slugs):
        sk = s0 + Z.cass_wall + 0.05 + k * Z.slug_l
        out.append(Part(f"C-ZSLUG-{k + 1}", f"Z ballast slug Ø{Z.slug_d:g}×{Z.slug_l:g} steel", "ballast_z", "steel",
                        "steel", cyl(_axis_pt(P, sk, Z.axis_offset), d, Z.slug_l - 0.1, Z.slug_d / 2), STEEL,
                        export=False, moving="z_ballast"))
    s1 = s0 + Z.cass_len
    bs = cyl(_axis_pt(P, s1, Z.axis_offset), d, Lb - idx_mm - Z.cass_len + drop + 10, Z.cass_d / 2)
    bs = bs.intersect(box(-200, 300, -50, 50, zs_top, 0))
    out.append(Part("C-Z-SPACER-B", "Z index spacer (below the cassette, seats on the palm shelf)", "ballast_z",
                    "printed", "PETG", solid(bs), GREEN, moving="z_ballast"))
    if mirror:
        for p in out:
            p.shape = p.shape.mirror("XZ")
    return out


# ---------------------------------------------------------------- X ballast, fixed ballast

def x_channel_parts(P) -> list:
    X = P.x_ballast
    H = P.housing.height
    c0, c1 = X.channel_x
    hw = X.channel_half_w
    zb = -H - X.channel_h
    ch = box(c0, c1, -hw, hw, zb, -H)
    rs = X.rear_stop_x[1]
    ch = ch.cut(box(rs, c1 + 1, -X.slot_neck_half, X.slot_neck_half, zb - 1, X.slot_head_z[0]))
    ch = ch.cut(box(rs, c1 + 1, -X.slot_head_half, X.slot_head_half, X.slot_head_z[0], X.slot_head_z[1]))
    n = int(round((X.pos_max - X.pos_min) / X.pos_step))
    lock_z = (zb + X.slot_head_z[0]) / 2
    for k in range(n + 1):
        xk = X.pos_min + 33.0 + k * X.pos_step
        ch = ch.cut(cyl((xk, -hw - 1, lock_z), (0, 1, 0), hw - X.slot_neck_half + 1.5, X.lock_hole_d / 2))
        hh = 3.0 if k % 5 == 0 else 1.8
        ch = ch.cut(box(xk - 0.2, xk + 0.2, hw - 0.4, hw + 0.1, zb + 0.6, zb + 0.6 + hh))
    fs0, fs1 = X.front_stop_x
    stop = box(fs0, fs1, -X.slot_neck_half + 0.05, X.slot_neck_half - 0.05, zb, X.slot_head_z[0])
    stop = stop.fuse(box(fs0, fs1, -X.slot_head_half + 0.05, X.slot_head_half - 0.05, X.slot_head_z[0],
                         X.slot_head_z[1]))
    stop = stop.fuse(box(c1, c1 + X.end_cap_t, -hw, hw, zb, -H))
    return [Part("C-X-CHANNEL", "X ballast channel (T-slot, capture lips, indexed lock holes, scale)", "ballast_x",
                 "printed", "PETG", solid(ch), DARK, meta={"lock_z": lock_z}),
            Part("C-X-STOP-F", "Front hard stop and end cap (removable to insert the carriage)", "ballast_x",
                 "printed", "PETG", solid(stop), DARK)]


def x_cassette_parts(P, pos, n_slugs) -> list:
    X = P.x_ballast
    H = P.housing.height
    zb = -H - X.channel_h
    ro, rb = X.tube_d / 2, X.bore_d / 2
    zc = zb - X.shoe_clear - ro
    p = pos
    tube_s = cyl((p, 0, zc), (1, 0, 0), X.len, ro)
    tube_s = tube_s.cut(cyl((p + X.rear_wall, 0, zc), (1, 0, 0), X.len, rb))
    s0, s1 = p + X.shoe_x[0], p + X.shoe_x[1]
    cl = X.shoe_clear
    neck = box(s0, s1, -X.slot_neck_half + cl, X.slot_neck_half - cl, zc + rb + 0.5, X.slot_head_z[0] + cl)
    head = box(s0, s1, -X.slot_head_half + cl, X.slot_head_half - cl, X.slot_head_z[0] + cl, X.slot_head_z[1] - cl)
    cas = fuse(tube_s, neck, head)
    lock_z = (zb + X.slot_head_z[0]) / 2
    lx = p + 33.0
    cas = solid(cas.cut(cyl((lx, -X.slot_neck_half, lock_z), (0, 1, 0), X.slot_neck_half, X.lock_d / 2)))
    cap = knurl((p + X.len, 0, zc), (1, 0, 0), X.cap_t, ro, n=36)
    hw = X.channel_half_w
    lock = cyl((lx, -hw - 3, lock_z), (0, 1, 0), hw + 3 - 0.5, X.lock_d / 2)
    knob = knurl((lx, -hw - 9, lock_z), (0, 1, 0), 6, X.lock_knob_d / 2)
    out = [Part("C-X-CASSETTE", "X ballast cassette (sliding, captive T-shoe, closed tube)", "ballast_x", "printed",
                "PETG-ballast-cassette", cas, GREEN, moving="x_ballast"),
           Part("C-X-CAP", "Cassette end cap (knurled, threaded)", "ballast_x", "printed", "PETG-ballast-cassette",
                cap, DARK, moving="x_ballast"),
           Part("H-X-LOCK", "Indexed lock screw M4", "ballast_x", "hardware", "steel", lock, STEEL, export=False,
                moving="x_ballast"),
           Part("H-X-LOCK-KNOB", "Lock knob (knurled)", "ballast_x", "hardware", "steel", knob, STEEL, export=False,
                moving="x_ballast")]
    for k in range(n_slugs):
        x0 = p + X.rear_wall + 0.05 + k * X.slug_l
        out.append(Part(f"C-XSLUG-{k + 1}", f"X ballast slug Ø{X.slug_d:g}×{X.slug_l:g} steel", "ballast_x", "steel",
                        "steel", cyl((x0, 0, zc), (1, 0, 0), X.slug_l - 0.1, X.slug_d / 2), STEEL, export=False,
                        moving="x_ballast"))
    return out


def fixed_bars(P, n) -> list:
    F, h = P.fixed_ballast, P.housing
    out = []
    z0 = -h.height + h.wall
    for k in range(n):
        out.append(Part(f"C-FIXED-BAR-{k + 1}", f"Fixed ballast bar {F.len:g}×{F.w:g}×{F.t:g} steel (front bay)",
                        "ballast_x", "steel", "steel",
                        box(F.x0, F.x0 + F.len, -F.w / 2, F.w / 2, z0 + k * F.t + 0.02, z0 + (k + 1) * F.t),
                        STEEL, export=False))
    return out


# ---------------------------------------------------------------- guard, switch, electronics

def guard_switch_parts(P) -> list:
    g, s, h = P.trigger_guard, P.switch, P.housing
    H = h.height
    x0, x1 = g.x
    outer = rbox(x0, x1, -g.half_w, g.half_w, g.bottom_z, -H + 8, 9.0, "|Y")
    inner = rbox(x0 + g.t, x1 - g.t, -g.half_w - 1, g.half_w + 1, g.bottom_z + g.t, -H + 20, 6.0, "|Y")
    guard = outer.cut(inner).intersect(box(x0 - 1, x1 + 1, -10, 10, g.bottom_z - 1, -H))
    pts = [(s.x - 2.0, -H - 0.4), (s.x + 2.6, -H - 0.4), (s.x + 2.0, -H - 8), (s.x + 3.5, -H - 16),
           (s.x + 1.0, -H - 18.5), (s.x - 1.0, -H - 16), (s.x - 2.2, -H - 8)]
    blade = cq.Workplane("XZ", origin=(0, s.blade_w / 2, 0)).polyline(pts).close().extrude(s.blade_w).val()
    stem = box(s.x - 1.8, s.x + 1.8, -2.5, 2.5, -H - 0.5, -H + h.wall + 3.5)
    blade = fuse(blade, stem)
    zf = -H + h.wall
    body = box(s.x - 10, s.x + 10, -6.8, 6.8, zf, zf + 7.4)
    body = body.cut(box(s.x - 2.2, s.x + 2.2, -2.9, 2.9, zf - 1, zf + 4.5))
    el = box(8, 38, -6.8, 6.8, zf, zf + 15)
    return [Part("A-TRIGGER-GUARD", "Trigger guard (finger protection for the switch blade)", "housing", "printed",
                 "PETG", solid(guard), NAVY),
            Part("D-SWITCH-BLADE", "Switch blade (contact switch actuator only; no sear, no energy store)",
                 "interfaces", "printed", "PETG", blade, DARK),
            Part("D-SWITCH-BODY", "Switch module housing (PLACEHOLDER envelope)", "interfaces", "electronics", "-",
                 solid(body), DARK, export=False, mass_override_g=6.0, status="PLACEHOLDER"),
            Part("E-ELECTRONICS", "Electronics bay envelope (BLE module, battery; PLACEHOLDER)", "interfaces",
                 "electronics", "-", el, DARK, export=False, mass_override_g=P.materials.electronics["mass_g"],
                 status="PLACEHOLDER")]
