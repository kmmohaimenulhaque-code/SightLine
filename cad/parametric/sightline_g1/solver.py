"""Ballast solver for G1: enumerate every discrete ballast setting (fixed bars, X slugs and X position, Z slugs
and Z index) from per-part CAD mass properties, and rank them against a mass target. COM-x/z and inertia targets are
used only when a targets file provides them; unknown targets are never filled in."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

from . import geom as gm
from .assembly import REPO, combine, part_mass

TARGET_DIR = REPO / "cad/parametric/configurations/targets"
SCALES = {"mass_g": 10.0, "com_mm": 1.0}


def _val(v):
    return v.get("value") if isinstance(v, dict) else v


def _known(v):
    v = _val(v)
    return v is not None and not (isinstance(v, str) and v.strip().upper() in ("TBD", "UNKNOWN", ""))


def load_targets():
    out = []
    for p in sorted(TARGET_DIR.glob("*.json")):
        out.append(json.loads(p.read_text()))
    return out


def contributions(asm) -> dict:
    """Mass rows of the fixed part of the assembly and of every adjustable element."""
    P, cfg = asm.P, asm.cfg
    X, Z = P.x_ballast, P.z_ballast
    left = cfg.get("hand", "right") == "left"
    drop = float(cfg.get("palm_shelf", {}).get("drop", P.palm_shelf.drop))
    adj = lambda p: p.group in ("ballast_z",) or p.moving == "x_ballast" or p.id.startswith("C-FIXED-BAR")  # noqa
    base = [part_mass(P, p) for p in asm.parts if not adj(p)]
    xg = {pos: combine([part_mass(P, p) for p in gm.x_cassette_parts(P, pos, 0)])
          for pos in np.arange(X.pos_min, X.pos_max + 1e-6, X.pos_step)}
    xs = []
    for k in range(X.slug_max):
        q = [p for p in gm.x_cassette_parts(P, X.pos_min, k + 1) if p.id == f"C-XSLUG-{k + 1}"][0]
        xs.append(part_mass(P, q))
    zg, zs = {}, {}
    for idx in Z.index_mm:
        rows = [part_mass(P, p) for p in gm.z_ballast_parts(P, idx, Z.slug_max, drop, left)]
        zg[idx] = combine([r for r in rows if not r["id"].startswith("C-ZSLUG")])
        zs[idx] = [r for r in rows if r["id"].startswith("C-ZSLUG")]
    bars = [part_mass(P, p) for p in gm.fixed_bars(P, P.fixed_ballast.bars_max)]
    return {"base": combine(base), "x_group": xg, "x_slugs": xs, "z_group": zg, "z_slugs": zs, "bars": bars,
            "base_rows": base}


def evaluate(c, P, nb, nx, pos, nz, idx) -> dict:
    rows = [c["base"], c["x_group"][pos]]
    for k in range(nx):
        r = dict(c["x_slugs"][k])
        r["com"] = r["com"] + np.array([pos - P.x_ballast.pos_min, 0, 0])
        rows.append(r)
    rows.append(c["z_group"][idx])
    rows += c["z_slugs"][idx][:nz]
    rows += c["bars"][:nb]
    return combine(rows)


def enumerate_all(asm, c=None):
    P = asm.P
    c = c or contributions(asm)
    X, Z = P.x_ballast, P.z_ballast
    res = []
    for nb, nx, pos, nz, idx in itertools.product(range(P.fixed_ballast.bars_max + 1), range(X.slug_max + 1),
                                                  sorted(c["x_group"]), range(Z.slug_max + 1), Z.index_mm):
        e = evaluate(c, P, nb, nx, pos, nz, idx)
        res.append({"fixed_bars": nb, "x_slugs": nx, "x_position_mm": float(pos), "z_slugs": nz,
                    "z_index_mm": float(idx), "mass_g": e["mass_g"], "com": e["com"], "I": e["I"]})
    return res, c


def solve(asm, targets=None) -> dict:
    allc, c = enumerate_all(asm)
    G0 = asm.frames["grip_datum_K"]
    m = np.array([r["mass_g"] for r in allc])
    com = np.array([r["com"] for r in allc])
    env = {"mass_g": [round(float(m.min()), 1), round(float(m.max()), 1)],
           "com_x_K_mm": [round(float(com[:, 0].min()), 1), round(float(com[:, 0].max()), 1)],
           "com_y_K_mm": [round(float(com[:, 1].min()), 2), round(float(com[:, 1].max()), 2)],
           "com_z_K_mm": [round(float(com[:, 2].min()), 1), round(float(com[:, 2].max()), 1)],
           "settings": len(allc)}
    out = {"config_id": asm.id, "profile": asm.prof["id"], "phone_mass": asm.prof["mass"], "envelope": env,
           "grip_datum_K": G0.tolist(), "targets": []}
    for t in targets if targets is not None else load_targets():
        tm = _val(t.get("target_mass_g"))
        tc_given = [_val(t.get(f"target_com_{a}_mm")) for a in "xyz"]
        # COM-x/z in the target files are expressed in the G0 chassis frame K and do not transfer to K1;
        # COM-y = 0 is the lateral symmetry plane in both frames.
        tc = [None, tc_given[1], None]
        frame_note = [f"COM-{a} {tc_given[i]} mm given in the G0 frame K — not transferable to K1, not used"
                      for i, a in enumerate("xyz") if i != 1 and _known(tc_given[i])]
        tol_m, tol_c = _val(t.get("mass_tolerance_g")), _val(t.get("com_tolerance_mm"))
        if not _known(tm):
            out["targets"].append({"target_id": t.get("reference_id"), "status": "NOT USED (mass target unknown)"})
            continue
        score = ((m - tm) / SCALES["mass_g"]) ** 2
        used = []
        for i, v in enumerate(tc):
            if _known(v):
                score = score + ((com[:, i] - float(v)) / SCALES["com_mm"]) ** 2
                used.append("xyz"[i])
        order = np.argsort(score)[:5]
        best = []
        for i in order:
            r = allc[i]
            best.append({k: r[k] for k in ("fixed_bars", "x_slugs", "x_position_mm", "z_slugs", "z_index_mm")}
                        | {"mass_g": round(r["mass_g"], 1), "com_K_mm": np.round(r["com"], 2).tolist(),
                           "com_G_mm": np.round(r["com"] - G0, 2).tolist(),
                           "inertia_diag_about_com_gmm2": np.round(np.diag(r["I"]), 0).tolist()})
        b = allc[order[0]]
        verdict = "NO VERDICT (tolerance TBD)"
        reasons = []
        if _known(tol_m):
            okm = abs(b["mass_g"] - tm) <= float(tol_m)
            okc = all(abs(b["com"][i] - float(tc[i])) <= float(tol_c) for i in range(3) if _known(tc[i])) \
                if used and _known(tol_c) else True
            verdict = "FEASIBLE" if (okm and okc) else "INFEASIBLE"
            if not okm:
                reasons.append("insufficient ballast" if tm > env["mass_g"][1] else
                               "mass below the lightest configuration" if tm < env["mass_g"][0] else "mass step")
            if not okc:
                for i in range(3):
                    if _known(tc[i]) and not (env[f"com_{'xyz'[i]}_K_mm"][0] - 1e-6 <= float(tc[i])
                                              <= env[f"com_{'xyz'[i]}_K_mm"][1] + 1e-6):
                        reasons.append(f"insufficient {'XYZ'[i]} travel (target COM-{'xyz'[i]} {tc[i]} outside "
                                       f"{env[f'com_{chr(120 + i)}_K_mm']})")
        out["targets"].append({"target_id": t.get("reference_id"), "target_mass_g": tm,
                               "target_com_mm": tc, "com_axes_used": used, "frame_notes": frame_note, "status": verdict, "reasons": reasons,
                               "mass_tolerance_g": tol_m, "com_tolerance_mm": tol_c,
                               "inertia_target": "UNKNOWN — not used" if not _known(t.get("target_inertia_tensor_gmm2"))
                               else "given (not yet used by the G1 solver)",
                               "best": best})
    return out


def markdown(sol: dict, summary: dict) -> str:
    e = sol["envelope"]
    L = [f"# G1 mass report — {sol['config_id']} ({sol['profile']})", "",
         "MODEL OUTPUT (CAD estimate). Nothing here has been weighed; replace with measured masses before any claim.",
         "", f"* Configured: **{summary['mass_g']} ± {summary['mass_sigma_g']} g** (1σ, ESTIMATED), COM K1 "
         f"{summary['com_K_mm']} mm, COM about the grip datum {summary['com_G_mm']} mm.",
         f"* Phone mass {sol['phone_mass']['v']} g ({sol['phone_mass']['s']}).",
         f"* Ballast envelope over {e['settings']} discrete settings: mass {e['mass_g']} g; COM-x {e['com_x_K_mm']} mm; "
         f"COM-y {e['com_y_K_mm']} mm; COM-z {e['com_z_K_mm']} mm (K1).", "",
         "| Target | Mass (g) | COM used | Status | Best setting (bars, X slugs @ pos, Z slugs @ index) | Mass (g) | COM K1 (mm) |",
         "|---|---|---|---|---|---|---|"]
    for t in sol["targets"]:
        if "best" not in t:
            L.append(f"| {t['target_id']} | — | — | {t['status']} | — | — | — |")
            continue
        b = t["best"][0]
        L.append(f"| {t['target_id']} | {t['target_mass_g']} | {''.join(t['com_axes_used']) or 'none (UNKNOWN)'} | "
                 f"{t['status']}{(' — ' + '; '.join(t['reasons'])) if t['reasons'] else ''} | {b['fixed_bars']}, "
                 f"{b['x_slugs']} @ {b['x_position_mm']:g}, {b['z_slugs']} @ {b['z_index_mm']:g} | {b['mass_g']} | "
                 f"{b['com_K_mm']} |")
    L += ["", "By group (configured): " + ", ".join(f"{k} {v} g" for k, v in summary["by_group"].items()), ""]
    return "\n".join(L)
