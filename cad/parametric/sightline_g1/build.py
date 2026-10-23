"""Regenerate every G1 output from the editable source.

    python -m cad.parametric.sightline_g1.build                # all G1 configurations, exports, renders
    python -m cad.parametric.sightline_g1.build --quick        # checks + mass only (no exports, no renders)

Outputs (generated — never edit by hand):
    cad/exports/g1/<CONFIG>/   assembly STEP + STL (gzip-compressed, lossless), checks.json/.md, mass_report.json/.md, frames.json, parts.json
    cad/exports/g1/parts/      one STEP + STL per component (assembly pose, K1 frame); hardware/ for reference parts
    cad/exports/g1/MANIFEST.json   sha256, size, bbox, material, colour, source for every generated file
    docs/cad/renders/g1/       CAD-derived renders of the reference configuration (G1-IP15-RH)
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from cad.parametric.sightline_g1 import GENERATOR_VERSION  # noqa: E402
from cad.parametric.sightline_g1 import checks as ck  # noqa: E402
from cad.parametric.sightline_g1 import geom as gm  # noqa: E402
from cad.parametric.sightline_g1 import solver  # noqa: E402
from cad.parametric.sightline_g1.assembly import build, frames_report, load_params, mass_summary, mass_table  # noqa: E402

CONF = REPO / "cad/parametric/configurations/g1"
OUT = REPO / "cad/exports/g1"
RENDERS = REPO / "docs/cad/renders/g1"
REFERENCE_CONFIG = "G1-IP15-RH"


def jd(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_commit() -> str:
    import subprocess
    try:
        h = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain", "--", "cad/parametric"], cwd=REPO, capture_output=True,
                           text=True, check=True).stdout.strip()
        return h + ("+dirty" if d else "")
    except Exception:  # pragma: no cover
        return "unknown"


def mesh(shape, tol=0.05, ang=0.2):
    v, f = shape.tessellate(tol, ang)
    return np.array([[p.x, p.y, p.z] for p in v], float), np.array(f, int)


def export_shape(shape, base: Path) -> dict:
    """STEP + STL; STEP re-imported (volume within 0.1 %), STL checked watertight with trimesh."""
    import cadquery as cq
    import trimesh
    base.parent.mkdir(parents=True, exist_ok=True)
    step, stl = base.with_suffix(".step"), base.with_suffix(".stl")
    tol = 0.02
    cq.exporters.export(shape, str(step))
    cq.exporters.export(shape, str(stl), tolerance=tol, angularTolerance=0.1)
    v0 = shape.Volume()
    v1 = cq.importers.importStep(str(step)).val().Volume()
    t2 = trimesh.load(stl)
    return {"step": str(step.relative_to(REPO)), "stl": str(stl.relative_to(REPO)), "brep_volume_mm3": round(v0, 3),
            "step_reimport_volume_mm3": round(v1, 3), "step_ok": abs(v1 - v0) <= 1e-3 * max(v0, 1),
            "stl_watertight": bool(t2.is_watertight), "stl_volume_mm3": round(float(t2.volume), 3),
            "stl_tolerance_mm": tol,
            "stl_ok": bool(t2.is_watertight) and abs(t2.volume - v0) <= max(0.005 * v0, shape.Area() * tol, 1.0)}


def export_assembly(asm, od: Path) -> dict:
    import cadquery as cq
    import trimesh
    a = cq.Assembly(name=asm.id)
    meshes = []
    for p in asm.parts:
        if p.kind == "display":
            continue
        a.add(p.shape, name=p.id, color=cq.Color(*p.color))
        v, f = mesh(p.shape, 0.08, 0.25)
        meshes.append(trimesh.Trimesh(v, f, process=False))
    step = od / f"{asm.id}_assembly.step"
    a.save(str(step), exportType="STEP")
    stl = od / f"{asm.id}_assembly.stl"
    trimesh.util.concatenate(meshes).export(stl)
    out = []
    for p in (step, stl):                       # ~50 MB STEP → ~12 MB; lossless, gunzip before opening
        gz = p.with_name(p.name + ".gz")
        with open(p, "rb") as fi, gzip.GzipFile(gz, "wb", compresslevel=9, mtime=0) as fo:
            fo.write(fi.read())
        p.unlink()
        out.append(str(gz.relative_to(REPO)))
    return {"step": out[0], "stl": out[1], "parts": len(meshes), "compression": "gzip (lossless)"}


def part_rows(asm, rows):
    out = []
    for p, r in zip(asm.parts, rows):
        b = p.shape.BoundingBox()
        out.append({"id": p.id, "name": p.name, "group": p.group, "kind": p.kind, "material": p.material,
                    "color_rgb": p.color, "mass_g": round(r["mass_g"], 2), "mass_basis": r["basis"],
                    "com_K_mm": np.round(r["com"], 2).tolist(), "volume_mm3": round(p.shape.Volume(), 2),
                    "bbox_K_mm": [round(b.xmin, 2), round(b.xmax, 2), round(b.ymin, 2), round(b.ymax, 2),
                                  round(b.zmin, 2), round(b.zmax, 2)],
                    "transform_K": "identity (parts are modelled in place in K1)", "moving_interface": p.moving,
                    "phone_specific": p.phone_specific, "collide": p.collide,
                    "source": "cad/parametric/sightline_g1/geom.py"})
    return out


def variant_parts(P, asm_by_id) -> list:
    """Extra exported variants: backstraps S/L, palm-shelf wings ±5°, left-hand grip set, Android cradle set."""
    out = []
    for name, d in P.grip.backstrap_variants.items():
        if name == "M":
            continue
        b = [p for p in gm.grip_parts(P, None, None, float(d), False) if p.id == "A-BACKSTRAP"][0]
        b.id = f"A-BACKSTRAP-{name}"
        out.append(b)
    for a in P.palm_shelf.angle_variants_deg:
        if a == 0:
            continue
        s = [p for p in gm.grip_parts(P, None, a, 0.0, False) if p.id == "A-PALM-SHELF"][0]
        s.id = f"A-PALM-SHELF-{'P' if a > 0 else 'M'}{abs(a):g}DEG"
        out.append(s)
    for p in gm.front_sight_parts(P, P.sight.front_shim_range[1]):
        if p.id == "S-FRONT-SHIM":
            p.id = f"S-FRONT-SHIM-{P.sight.front_shim_range[1]:g}MM".replace(".", "P")
            out.append(p)
    for cid, asm in asm_by_id.items():
        if asm.cfg.get("hand") == "left":
            for p in asm.parts:
                if p.group == "grip" and p.kind == "printed":
                    q = gm.Part(**{**p.__dict__})
                    q.id = p.id + "-LH"
                    out.append(q)
        if asm.prof["id"] != "apple-iphone-15":
            for p in asm.parts:
                if p.phone_specific and p.kind in ("printed", "tpu"):
                    q = gm.Part(**{**p.__dict__})
                    q.id = f"{p.id}-{asm.prof['id'].upper()}"
                    out.append(q)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", action="append")
    ap.add_argument("--quick", action="store_true", help="checks (static only) and mass; no exports or renders")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    cfgs = a.config or sorted(str(p) for p in CONF.glob("*.json"))
    targets = solver.load_targets()
    fails = 0
    asms, manifest = {}, []
    commit = git_commit()
    for c in cfgs:
        asm = build(c)
        asms[asm.id] = asm
        od = OUT / asm.id
        od.mkdir(parents=True, exist_ok=True)
        rows = mass_table(asm)
        summ = mass_summary(asm, rows)
        sol = solver.solve(asm, targets)
        bal = asm.cfg["ballast"]
        cfg_setting = solver.evaluate(solver.contributions(asm), asm.P, int(bal["fixed_bars"]), int(bal["x"]["slugs"]),
                                      float(bal["x"]["position_mm"]), int(bal["z"]["slugs"]), float(bal["z"]["index_mm"]))
        consistency = abs(cfg_setting["mass_g"] - summ["mass_g"]) < 0.2 and \
            np.allclose(cfg_setting["com"], summ["com_K_mm"], atol=0.05)
        # the reference configuration runs every moving-interface case; the others run the static checks plus the
        # phone-angle cases (their chassis, sights and ballast are shared and the left-hand grip is a mirror image)
        res = ck.run_all(asm, full=False if a.quick else ("all" if asm.id == REFERENCE_CONFIG else "angle"))
        res["solver_cad_consistency"] = {"status": "PASS" if consistency else "FAIL",
                                         "configured_mass_g": summ["mass_g"],
                                         "solver_mass_g_for_configured_setting": round(cfg_setting["mass_g"], 2),
                                         "configured_com_K": summ["com_K_mm"],
                                         "solver_com_K": np.round(cfg_setting["com"], 2).tolist()}
        st = [v["status"] for v in res.values() if isinstance(v, dict) and "status" in v]
        res["summary"].update({"PASS": st.count("PASS"), "FAIL": st.count("FAIL")})
        fails += res["summary"]["FAIL"]
        (od / "checks.json").write_text(json.dumps(res, indent=1, default=jd))
        (od / "checks.md").write_text(ck.markdown(res))
        rep = {"generator": f"sightline_g1 {GENERATOR_VERSION}", "source_commit": commit, "summary": summ,
               "solver": sol, "settings": asm.cfg["ballast"]}
        (od / "mass_report.json").write_text(json.dumps(rep, indent=1, default=jd))
        (od / "mass_report.md").write_text(solver.markdown(sol, summ))
        (od / "frames.json").write_text(json.dumps(frames_report(asm), indent=1, default=jd))
        (od / "parts.json").write_text(json.dumps(part_rows(asm, rows), indent=1, default=jd))
        print(f"[{asm.id}] {res['summary']} mass {summ['mass_g']} ± {summ['mass_sigma_g']} g COM {summ['com_K_mm']}")
        if not a.quick:
            r = export_assembly(asm, od)
            manifest.append({"id": f"{asm.id}-assembly", **r})
            print(f"[{asm.id}] assembly exported ({r['parts']} parts)")
    if not a.quick:
        P = load_params()
        ref = asms.get(REFERENCE_CONFIG) or next(iter(asms.values()))
        pd = OUT / "parts"
        seen, exp = set(), []
        for p in ref.parts + variant_parts(P, asms):
            if p.id in seen or p.kind == "display":
                continue
            seen.add(p.id)
            sub = pd if p.kind in ("printed", "tpu") else pd / ("reference" if p.kind in ("phone", "electronics") else "hardware")
            r = export_shape(p.shape, sub / p.id)
            b = p.shape.BoundingBox()
            r.update({"id": p.id, "material": p.material, "color_rgb": p.color, "kind": p.kind,
                      "bbox_K_mm": [round(v, 2) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]})
            exp.append(r)
            if not (r["step_ok"] and r["stl_ok"]):
                fails += 1
                print("EXPORT FAIL", r)
        (OUT / "export_verification.json").write_text(json.dumps(exp, indent=1, default=jd))
        manifest += exp
        print(f"exported {len(exp)} components; all verified {all(r['step_ok'] and r['stl_ok'] for r in exp)}")
        if not a.no_render:
            from cad.parametric.sightline_g1.render import render_all
            made = render_all(ref, RENDERS)
            (RENDERS / "render_metadata.json").write_text(json.dumps(
                {"config": ref.id, "generator": f"sightline_g1 {GENERATOR_VERSION}", "source_commit": commit,
                 "renderer": "VTK offscreen (EGL), B-rep tessellation 0.12 mm", "files": made,
                 "reference_images": ["docs/cad/reference/g1_absolute_reference.jpg",
                                      "docs/cad/reference/g1_secondary_reference.png"],
                 "note": "renders are CAD-derived; the reference images are qualitative and nothing was measured from them"},
                indent=1))
            print("renders:", [m["file"] for m in made])
        files = []
        for p in sorted(OUT.rglob("*")):
            if p.is_file() and p.name != "MANIFEST.json":
                files.append({"file": str(p.relative_to(REPO)), "sha256": sha(p), "bytes": p.stat().st_size})
        P = load_params()
        (OUT / "MANIFEST.json").write_text(json.dumps(
            {"generator": f"sightline_g1 {GENERATOR_VERSION}", "source_commit": commit,
             "parameters": "cad/parametric/parameters/g1.json", "parameters_sha256": sha(Path(P["_path"])),
             "configurations": [str(Path(c).relative_to(REPO)) if Path(c).is_absolute() else c for c in cfgs],
             "note": "STEP headers carry a timestamp, so STEP hashes change on every regeneration; volumes and STL "
                     "geometry are deterministic", "components": manifest, "files": files}, indent=1, default=jd))
    print(f"done in {time.time() - t0:.0f} s; FAIL count {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
