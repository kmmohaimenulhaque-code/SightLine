"""Automated G1 CAD checks. PASS means the CAD model satisfies the rule; it is not a physical test."""

from __future__ import annotations

import time

import numpy as np

from . import geom as gm
from .assembly import build, frames, sight_geometry

VOL_TOL = 0.05     # mm³; a positive common volume above this is an interference (face contact is allowed)


def _bb(s):
    b = s.BoundingBox()
    return np.array([b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax])


def _overlap(a, b, pad=0.01):
    return not (a[1] < b[0] - pad or b[1] < a[0] - pad or a[3] < b[2] - pad or b[3] < a[2] - pad
                or a[5] < b[4] - pad or b[5] < a[4] - pad)


def common(a, b) -> float:
    try:
        return a.intersect(b).Volume()
    except Exception:  # pragma: no cover
        return float("nan")


def interferences(parts, others=None) -> tuple:
    """Pairs with a positive common volume. ``others`` given: only moving × static pairs."""
    A = [p for p in parts if p.collide]
    B = [p for p in (others if others is not None else parts) if p.collide]
    bbA = {p.id: _bb(p.shape) for p in A}
    bbB = {p.id: _bb(p.shape) for p in B}
    out, n = [], 0
    for i, p in enumerate(A):
        for j, q in enumerate(B):
            if others is None and j <= i:
                continue
            if p.id == q.id or not _overlap(bbA[p.id], bbB[q.id]):
                continue
            n += 1
            v = common(p.shape, q.shape)
            if not (v <= VOL_TOL):
                out.append({"a": p.id, "b": q.id, "volume_mm3": round(float(v), 3)})
    return out, n


def empty_regions(parts, regions) -> list:
    hits = []
    for k, r in enumerate(regions):
        br = _bb(r)
        for p in parts:
            if not p.collide or not _overlap(_bb(p.shape), br):
                continue
            v = common(p.shape, r)
            if not (v <= VOL_TOL):
                hits.append({"region": k, "part": p.id, "volume_mm3": round(float(v), 3)})
    return hits


def sight_line_box(P):
    s = P.sight
    return gm.box(-800, s.front_blade_x[0] - 0.2, -1.0, 1.0, s.line_z + 0.3, s.line_z + 1.3)


def _st(ok):
    return "PASS" if ok else "FAIL"


def _moving(asm, key):
    mv = [p for p in asm.parts if p.moving == key]
    st = [p for p in asm.parts if p.moving != key]
    return mv, st


def run_all(asm, full=True) -> dict:
    t0 = time.time()
    P, cfg = asm.P, asm.cfg
    res = {"config_id": asm.id, "profile": asm.prof["id"], "hand": cfg.get("hand", "right")}
    bad = [p.id for p in asm.parts if not (p.shape.isValid() and len(p.shape.Solids()) == 1 and p.shape.Volume() > 0)]
    res["solids_valid"] = {"status": _st(not bad), "invalid": bad, "n_parts": len(asm.parts)}
    inter, n = interferences(asm.parts)
    res["collision_matrix"] = {"status": _st(not inter), "pairs_tested": n, "interferences": inter,
                               "allowed_contacts": "face contact and equal-diameter threaded/press engagement (common "
                                                   f"volume ≤ {VOL_TOL} mm³); the elevation spring is compliant and "
                                                   "excluded"}
    hits = empty_regions(asm.parts, asm.keepouts)
    res["camera_keepout"] = {"status": _st(not hits), "regions": len(asm.keepouts), "hits": hits,
                             "note": "camera centre/protrusion/FOV PENDING; both short-end zones kept empty"}
    sl = empty_regions(asm.parts, [sight_line_box(P)])
    res["sight_line_clear"] = {"status": _st(not sl), "hits": sl,
                               "note": "2 × 1 mm corridor from 800 mm behind the instrument to the front blade, "
                                       "0.3 mm above the line of sight"}
    sg = sight_geometry(P)
    nb = asm.get("S-REAR-NOTCH")
    fb = asm.get("S-FRONT-BLADE")
    blade_top = _bb(fb.shape)[5]
    res["active_sights"] = {"status": _st(abs(blade_top - P.sight.line_z) < 0.05 and sg["sight_radius_mm"] > 150),
                            "blade_top_z": round(blade_top, 3), "notch_part": nb.id, **sg}
    f = asm.frames
    g = asm.extras["phone_geom"]
    ph = asm.get("PHONE")
    pb = _bb(ph.shape)
    pc = ph.shape.Center()
    pc = np.array([pc.x, pc.y, pc.z])
    pred = (f["T_KP"] @ np.array([-g["T"] / 2, 0, 0, 1.0]))[:3]
    tc_err = float(np.linalg.norm(pred - pc))
    res["transform_chain"] = {"status": _st(tc_err < 0.05), "phone_centroid_error_mm": round(tc_err, 4),
                              "chain": "PHONE BODY → ADAPTER (Q) → YOKE (Y) → CHASSIS (K1) → GRIP DATUM (G)"}
    lx, ly = pb[1] - pb[0], pb[3] - pb[2]
    ori = {"phone_long_axis_K": np.round(f["phone_long_axis_K"], 4).tolist(),
           "screen_normal_K": np.round(f["screen_normal_K"], 4).tolist(),
           "rear_camera_axis_K": np.round(f["rear_camera_axis_K"], 4).tolist(),
           "operator_view_dir_K": [1, 0, 0], "target_dir_K": [1, 0, 0], "cradle_angle_deg": f["angle_deg"],
           "phone_bbox_K": np.round(pb, 2).tolist(),
           "phone_bottom_above_sight_line_mm": round(pb[4] - P.sight.line_z, 2),
           "phone_behind_rear_sight": bool(pb[1] < P.sight.rear_base_x[0])}
    ok = (abs(abs(f["phone_long_axis_K"][1]) - 1) < 0.02 and f["screen_normal_K"][0] < -0.98 and
          f["rear_camera_axis_K"][0] > 0.98 and ly > lx and pb[4] > P.sight.line_z and ori["phone_behind_rear_sight"])
    res["phone_orientation"] = {"status": _st(ok), **ori,
                                "rule": "landscape: long axis along Y; screen faces the shooter (−X); rear cameras "
                                        "face the target (+X); phone above the sight line at the operator end",
                                "camera_sensing": "NOT CLAIMED — camera position, protrusion and field of view are "
                                                  "PENDING measurement"}
    pr = [{"id": p.id, "size": np.round(_bb(p.shape)[1::2] - _bb(p.shape)[0::2], 1).tolist()}
          for p in asm.parts if p.kind in ("printed", "tpu")]
    bed = 256.0
    big = [r for r in pr if max(r["size"]) > bed]
    res["printability"] = {"status": _st(not big), "bed_mm": bed, "too_large": big}
    if full:
        res["moving_interfaces"] = moving_checks(asm, only_angle=(full == "angle"))
        mv_ok = all(v["status"] == "PASS" for v in res["moving_interfaces"].values())
        res["moving_interfaces_summary"] = {"status": _st(mv_ok)}
    st = [v["status"] for v in res.values() if isinstance(v, dict) and "status" in v]
    res["summary"] = {"PASS": st.count("PASS"), "FAIL": st.count("FAIL"), "runtime_s": round(time.time() - t0, 1)}
    return res


def moving_checks(asm, only_angle=False) -> dict:
    P, cfg = asm.P, asm.cfg
    out = {}
    prof = asm.prof
    # phone angle positions
    rows = []
    for a in (P.yoke.angle_range_deg[0], P.yoke.angle_nominal_deg, P.yoke.angle_range_deg[1]):
        mv = gm.angle_dial_parts(P, a) + gm.cradle_parts(P, prof, a) + gm.phone_parts(P, prof, a)
        static = [p for p in asm.parts if p.moving != "angle"]
        hits, _ = interferences(mv, static)
        ko = empty_regions(static + mv, gm.camera_keepouts(P, prof, a))
        sl = empty_regions(mv, [sight_line_box(P)])
        rows.append({"angle_deg": a, "collisions": hits, "keepout_hits": ko, "sight_line_hits": sl})
    out["phone_angle_positions"] = {"status": _st(all(not (r["collisions"] or r["keepout_hits"] or r["sight_line_hits"])
                                                      for r in rows)), "cases": rows,
                                    "lock": "detent pin in each upright engages the dial holes; knurled knobs clamp"}
    if only_angle:
        return out
    # X ballast travel
    X = P.x_ballast
    rows = []
    n = int(round((X.pos_max - X.pos_min) / X.pos_step))
    static = [p for p in asm.parts if p.moving != "x_ballast"]
    for k in range(n + 1):
        pos = X.pos_min + k * X.pos_step
        mv = gm.x_cassette_parts(P, pos, X.slug_max)
        hits, _ = interferences(mv, static)
        rows.append({"position_mm": pos, "collisions": hits})
    ch = asm.get("C-X-CHANNEL")
    beyond = []
    for pos in (X.pos_min - X.pos_step, X.pos_max + X.pos_step):
        mv = [p for p in gm.x_cassette_parts(P, pos, 0) if p.id == "C-X-CASSETTE"]
        beyond.append({"position_mm": pos, "stop_engaged": bool(interferences(mv, static)[0])})
    capture = X.slot_head_half - X.shoe_clear > X.slot_neck_half
    out["x_ballast_travel"] = {"status": _st(all(not r["collisions"] for r in rows) and all(b["stop_engaged"] for b in beyond)
                                             and capture),
                               "range_mm": [X.pos_min, X.pos_max], "step_mm": X.pos_step, "positions": len(rows),
                               "cases_with_max_slugs": rows, "hard_stops_beyond_range": beyond,
                               "vertically_captive": bool(capture), "channel": ch.id,
                               "rattle": "UNVERIFIED (no physical test)"}
    # Z ballast index positions
    Z = P.z_ballast
    drop = float(cfg.get("palm_shelf", {}).get("drop", P.palm_shelf.drop))
    left = cfg.get("hand", "right") == "left"
    static = [p for p in asm.parts if p.moving != "z_ballast"]
    rows = []
    for idx in Z.index_mm:
        mv = gm.z_ballast_parts(P, idx, Z.slug_max, drop, left)
        hits, _ = interferences(mv, static)
        rows.append({"index_mm": idx, "collisions": hits})
    out["z_ballast_index"] = {"status": _st(all(not r["collisions"] for r in rows)), "cases_with_max_slugs": rows,
                              "capture": "bore closed above; palm shelf and bottom spacer close it below"}
    # palm shelf drops and angle variants (Z stack rebuilt for each drop)
    rows = []
    zidx = float(cfg["ballast"]["z"]["index_mm"])
    zn = int(cfg["ballast"]["z"]["slugs"])
    for d in P.palm_shelf.drop_positions:
        for a in P.palm_shelf.angle_variants_deg:
            gp = gm.grip_parts(P, d, a, 0.0, left)
            zp = gm.z_ballast_parts(P, zidx, zn, d, left)
            mv = [p for p in gp if p.id in ("A-PALM-SHELF",)] + zp
            static = [p for p in asm.parts if p.group not in ("ballast_z",) and p.id != "A-PALM-SHELF"]
            hits, _ = interferences(mv, static)
            rows.append({"drop_mm": d, "angle_deg": a, "collisions": hits})
    out["palm_shelf_positions"] = {"status": _st(all(not r["collisions"] for r in rows)), "cases": rows,
                                   "index": "Ø4 cross pin through the grip and one of three tongue holes"}
    # backstrap variants
    rows = []
    for name, dlt in P.grip.backstrap_variants.items():
        gp = gm.grip_parts(P, drop, None, float(dlt), left)
        bs = [p for p in gp if p.id == "A-BACKSTRAP"]
        static = [p for p in asm.parts if p.id != "A-BACKSTRAP"]
        hits, _ = interferences(bs, static)
        rows.append({"variant": name, "offset_mm": dlt, "collisions": hits, "volume_mm3": round(bs[0].shape.Volume(), 1)})
    out["backstrap_variants"] = {"status": _st(all(not r["collisions"] for r in rows)), "cases": rows}
    # sight adjustment travel
    s = P.sight
    rows = []
    static = [p for p in asm.parts if p.group != "sights"]
    for e in (-s.rear_elev_range_mm, s.rear_elev_range_mm):
        for w in (-s.rear_wind_range_mm, s.rear_wind_range_mm):
            mv = gm.rear_sight_parts(P, e, w)
            hits, _ = interferences(mv, static)
            hits += interferences([q for q in mv if q.moving], [q for q in mv if not q.moving])[0]
            rows.append({"sight": "rear", "elev_mm": e, "wind_mm": w, "collisions": hits})
    lat = s.front_wall_inner - s.front_carrier_half_w - 0.4
    for t in s.front_shim_range:
        for la in (-lat, lat):
            mv = gm.front_sight_parts(P, t, la)
            hits, _ = interferences(mv, static)
            rows.append({"sight": "front", "shim_mm": t, "lat_mm": la, "collisions": hits})
    out["sight_adjustment_travel"] = {"status": _st(all(not r["collisions"] for r in rows)), "cases": rows,
                                      "note": "lateral shims are re-cut for each lateral offset; geometry checked at the extremes"}
    return out


def markdown(res: dict) -> str:
    L = [f"# G1 CAD checks — {res['config_id']} ({res['profile']}, {res['hand']} hand)", "",
         "Automated, no hardware. PASS = the CAD model satisfies the rule; it is **not** a physical test.", "",
         "| Check | Status | Detail |", "|---|---|---|"]
    def detail(k, v):
        if k == "collision_matrix":
            return f"{v['pairs_tested']} pairs tested (bounding boxes overlap); {len(v['interferences'])} interferences"
        if k == "camera_keepout":
            return f"{v['regions']} keep-out solids; {len(v['hits'])} hits"
        if k == "sight_line_clear":
            return f"{len(v['hits'])} parts in the sight corridor"
        if k == "active_sights":
            return (f"radius {v['sight_radius_mm']} mm; height {v['nominal_sight_height_above_housing_mm']} mm; rear "
                    f"elev ±{v['rear_elevation_range_mm'][1]} mm, wind ±{v['rear_windage_range_mm'][1]} mm; front shim "
                    f"{v['front_elevation_shim_mm']} mm")
        if k == "transform_chain":
            return f"phone centroid error {v['phone_centroid_error_mm']} mm"
        if k == "phone_orientation":
            return (f"long axis {v['phone_long_axis_K']}, screen {v['screen_normal_K']}, camera "
                    f"{v['rear_camera_axis_K']}; {v['phone_bottom_above_sight_line_mm']} mm above the sight line")
        if k == "printability":
            return f"bed {v['bed_mm']} mm; too large: {v['too_large'] or 'none'}"
        if k == "solids_valid":
            return f"{v['n_parts']} parts; invalid: {v['invalid'] or 'none'}"
        return ""
    for k, v in res.items():
        if isinstance(v, dict) and "status" in v:
            L.append(f"| {k} | {v['status']} | {detail(k, v)} |")
    for k, v in res.get("moving_interfaces", {}).items():
        n = len(v.get("cases", v.get("cases_with_max_slugs", [])))
        L.append(f"| moving: {k} | {v['status']} | {n} cases |")
    s = res["summary"]
    L += ["", f"Summary: {s['PASS']} PASS · {s['FAIL']} FAIL · runtime {s['runtime_s']} s", ""]
    return "\n".join(L)
