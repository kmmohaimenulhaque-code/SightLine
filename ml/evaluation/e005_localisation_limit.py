"""Experiment E-005 — theoretical localisation limit (Cramer-Rao bound) for the simulated impact, and how far the
deterministic baseline of E-001 is from it. Also gate G2 of docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md.

Run:  python -m ml.evaluation.e005_localisation_limit --config ml/configs/e005.json --out ml/evaluation/results/E-005

Status of the outputs: the bound is DERIVED from the synthetic image model (same camera presets, light levels and
noise ASSUMPTIONS as E-001); the comparison with E-001 is SIMULATED. Nothing here is a measurement of a phone.
The bound is a *precision* floor for that model; accuracy terms are budgeted separately (docs/science/ERROR_BUDGET.md).
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import cv2
import numpy as np

from app.calibration.camera import CameraModel
from ml.datasets.provenance import git_commit, utc_now
from app.vision.aiming_mark import measure_aiming_mark_all, shot_from_mark
from ml.datasets.synthetic_target import Degradation, SceneSpec, expected_canvas, random_spec, render
from ml.evaluation.crlb import crlb_covariance, fisher_information, numerical_jacobian

RAYLEIGH_P95 = math.sqrt(-2.0 * math.log(0.05))   # p95 of |e| for an isotropic 2-D Gaussian = 2.448 sigma_axis


def _seed(master: int, preset: str, condition: str) -> int:
    return int(hashlib.sha256(f"{master}:{preset}:{condition}".encode()).hexdigest()[:12], 16)


def _with(spec: SceneSpec, theta: np.ndarray) -> SceneSpec:
    ix, iy, dist, yaw, pitch, white, black, psf = (float(v) for v in theta)
    return dataclasses.replace(
        spec, impact_xy_mm=(ix, iy), distance_mm=dist, yaw_deg=yaw, pitch_deg=pitch,
        appearance=dataclasses.replace(spec.appearance, white=white, black=black),
        degradation=dataclasses.replace(spec.degradation, psf_sigma_px=psf))


def impact_bound(spec: SceneSpec, steps: np.ndarray, region_radius_mm: float, supersample: int) -> dict:
    """CRLB covariance (mm^2) of the simulated impact for one scene: with every other parameter unknown, and with
    every other parameter known."""
    deg = spec.degradation
    canvas, pose, bounds = expected_canvas(spec, context_mm=region_radius_mm + 10.0, supersample=supersample)
    u0, v0, u1, v1 = bounds
    vv, uu = np.mgrid[v0:v1, u0:u1].astype(float)
    xy = pose.intersect_rays(spec.camera.pixel_rays(np.stack([uu.ravel(), vv.ravel()], axis=1)))
    mask = np.hypot(xy[:, 0], xy[:, 1]) <= region_radius_mm
    theta0 = np.array([*spec.impact_xy_mm, spec.distance_mm, spec.yaw_deg, spec.pitch_deg,
                       spec.appearance.white, spec.appearance.black, deg.psf_sigma_px])

    def mean_electrons(theta: np.ndarray) -> np.ndarray:
        c, _, _ = expected_canvas(_with(spec, theta), supersample=supersample, bounds=bounds)
        return c.ravel()[mask] * deg.electrons_per_unit

    mu = canvas.ravel()[mask] * deg.electrons_per_unit
    fisher = fisher_information(numerical_jacobian(mean_electrons, theta0, steps), mu + deg.read_noise_e**2)
    full = crlb_covariance(fisher, slice(0, 2))
    known = crlb_covariance(fisher, slice(0, 2), nuisance_known=True)
    return {"trace_mm2": float(np.trace(full)), "trace_known_mm2": float(np.trace(known)), "n_pixels": int(mask.sum())}


def baseline_without_compression(cfg: dict, e1: dict) -> list[dict]:
    """Where does the gap to the bound come from? Re-measure the E-001 good-light baseline (hybrid estimator) on the
    same kind of frames with and without the per-frame JPEG step. The bound excludes compression, so the part of the
    gap that disappears without JPEG is information lost to compression, not estimator inefficiency. SIMULATED."""
    rows, sc, cond = [], e1["scene"], e1["conditions"]["good_light"]
    for preset, p in e1["presets"].items():
        cam = CameraModel.from_hfov(p["width"], p["height"], p["hfov_deg"])
        row = {"preset": preset}
        for label, quality in (("jpeg90", cond["jpeg_quality"]), ("no_jpeg", None)):
            rng = np.random.default_rng(_seed(cfg["master_seed"], preset, "decomposition"))   # same scenes for both
            deg = Degradation(psf_sigma_px=cond["psf_sigma_px"], electrons_per_unit=cond["electrons_per_unit"],
                              read_noise_e=cond["read_noise_e"], jpeg_quality=quality)
            errs = []
            for _ in range(cfg["decomposition_trials"]):
                s = render(random_spec(rng, cam, deg, sc["impact_radius_mm"], tuple(sc["distance_range_mm"]),
                                       sc["max_tilt_deg"], sc["max_roll_deg"]), rng)
                mark = measure_aiming_mark_all(s.image).get("hybrid")
                if mark is not None:
                    shot = shot_from_mark(mark, s.bore_px_canvas, up_direction_px=s.ground_truth["up_direction_px"])
                    errs.append(float(np.hypot(*(shot.impact_xy_mm - np.array(s.ground_truth["impact_xy_mm"])))))
            row[f"hybrid_rms_mm_{label}"] = math.sqrt(float(np.mean(np.square(errs))))
        rows.append(row)
    return rows


def run(config_path: str, out_dir: str) -> dict:
    cfg = json.loads(Path(config_path).read_text())
    e1 = json.loads(Path(cfg["e001_config"]).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    steps = np.array(list(cfg["parameters"].values()))
    sc = e1["scene"]
    t0 = time.time()
    cells = []
    for preset, p in e1["presets"].items():
        cam = CameraModel.from_hfov(p["width"], p["height"], p["hfov_deg"])
        mm_px = cam.mm_per_pixel_on_axis(10000.0)
        for cname in cfg["conditions"]:
            cond = e1["conditions"][cname]
            rng = np.random.default_rng(_seed(cfg["master_seed"], preset, cname))
            traces, traces_known = [], []
            for _ in range(cfg["specs_per_cell"]):
                blur = cond["aim_speed_mm_s"] * e1["exposure_s"] / mm_px
                deg = Degradation(psf_sigma_px=cond["psf_sigma_px"], motion_blur_px=blur,
                                  motion_blur_angle_deg=float(rng.uniform(0, 180)) if blur > 0 else 0.0,
                                  electrons_per_unit=cond["electrons_per_unit"], read_noise_e=cond["read_noise_e"])
                spec = random_spec(rng, cam, deg, sc["impact_radius_mm"], tuple(sc["distance_range_mm"]),
                                   sc["max_tilt_deg"], sc["max_roll_deg"])
                b = impact_bound(spec, steps, cfg["region_radius_mm"], cfg["supersample"])
                traces.append(b["trace_mm2"])
                traces_known.append(b["trace_known_mm2"])
            rms, rms_known = math.sqrt(float(np.mean(traces))), math.sqrt(float(np.mean(traces_known)))
            cells.append({"preset": preset, "condition": cname, "mm_per_px": mm_px,
                          "crlb_rms_mm": rms, "crlb_p95_mm": RAYLEIGH_P95 * rms / math.sqrt(2.0),
                          "crlb_rms_px": rms / mm_px, "crlb_rms_mm_nuisance_known": rms_known,
                          "nuisance_cost_factor": rms / rms_known})

    # ---- comparison with the E-001 baseline (SIMULATED) -----------------------------------------------------------
    errs: dict[tuple[str, str, str], list[float]] = {}
    with open(cfg["e001_trials"], newline="") as f:
        for row in csv.DictReader(f):
            if row["detected"] == "1":
                errs.setdefault((row["preset"], row["condition"], row["method"]), []).append(float(row["vector_error_mm"]))
    bound = {(c["preset"], c["condition"]): c for c in cells}
    comparison = []
    for (preset, cond, method), e in sorted(errs.items()):
        ref = bound.get((preset, "good_light" if cond == "good_light_jpeg60" else cond))
        if ref is None:
            continue
        rms = math.sqrt(float(np.mean(np.square(e))))
        comparison.append({"preset": preset, "condition": cond, "method": method, "baseline_rms_mm": rms,
                           "crlb_rms_mm": ref["crlb_rms_mm"], "efficiency_ratio": rms / ref["crlb_rms_mm"],
                           "bound_condition": ref["condition"]})
    for c in cells:
        rows = [r for r in comparison if (r["preset"], r["condition"]) == (c["preset"], c["condition"])]
        best = min(rows, key=lambda r: r["baseline_rms_mm"])
        c.update(best_method=best["method"], best_baseline_rms_mm=best["baseline_rms_mm"],
                 best_efficiency_ratio=best["efficiency_ratio"],
                 above_g4_threshold=bool(best["efficiency_ratio"] >= cfg["g4_efficiency_threshold"]))
    decomposition = baseline_without_compression(cfg, e1)
    for d in decomposition:
        d["crlb_rms_mm"] = bound[(d["preset"], "good_light")]["crlb_rms_mm"]
        d["ratio_jpeg90"] = d["hybrid_rms_mm_jpeg90"] / d["crlb_rms_mm"]
        d["ratio_no_jpeg"] = d["hybrid_rms_mm_no_jpeg"] / d["crlb_rms_mm"]
    meta = {"experiment_id": cfg["experiment_id"], "status_label": cfg["status_label"], "created_utc": utc_now(),
            "git_commit": git_commit(Path(__file__).resolve().parents[2]), "runtime_s": round(time.time() - t0, 1),
            "specs_per_cell": cfg["specs_per_cell"],
            "environment": {"python": platform.python_version(), "numpy": np.__version__, "opencv": cv2.__version__}}
    res = {"meta": meta, "cells": cells, "decomposition": decomposition, "comparison": comparison}
    (out / "summary.json").write_text(json.dumps(res, indent=2) + "\n")
    (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    (out / "summary.md").write_text(to_markdown(res, cfg))
    return res


def to_markdown(res: dict, cfg: dict) -> str:
    m = res["meta"]
    lines = [f"# {cfg['experiment_id']} — {cfg['title']}", "",
             f"**Status: {cfg['status_label']}.** Synthetic image model with the E-001 presets and ASSUMED noise levels; "
             "not a measurement of any phone. The bound is a precision floor for this model, not an accuracy claim.",
             f"Created {m['created_utc']} · commit `{m['git_commit']}` · {m['specs_per_cell']} scenes per cell · "
             f"runtime {m['runtime_s']} s (CPU).", "",
             "## Bound on the impact position (all nuisance parameters unknown)", "",
             "| Preset | Condition | mm/px | CRLB RMS (mm) | CRLB p95 (mm) | CRLB RMS (px) | Cost of unknown nuisances "
             "| Best E-001 estimator | Its RMS (mm) | RMS / CRLB | ≥ 1.5× (gate G4 condition) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in res["cells"]:
        lines.append(f"| {c['preset']} | {c['condition']} | {c['mm_per_px']:.2f} | {c['crlb_rms_mm']:.3f} | "
                     f"{c['crlb_p95_mm']:.3f} | {c['crlb_rms_px']:.4f} | ×{c['nuisance_cost_factor']:.2f} | "
                     f"{c['best_method']} | {c['best_baseline_rms_mm']:.3f} | {c['best_efficiency_ratio']:.2f} | "
                     f"{'yes' if c['above_g4_threshold'] else 'no'} |")
    lines += ["", "## Where the good-light gap comes from (hybrid estimator, same scenes with and without JPEG 90)", "",
              "| Preset | CRLB RMS (mm) | Hybrid RMS with JPEG 90 (mm) | ratio | Hybrid RMS without JPEG (mm) | ratio |",
              "|---|---|---|---|---|---|"]
    for d in res["decomposition"]:
        lines.append(f"| {d['preset']} | {d['crlb_rms_mm']:.3f} | {d['hybrid_rms_mm_jpeg90']:.3f} | {d['ratio_jpeg90']:.2f} | "
                     f"{d['hybrid_rms_mm_no_jpeg']:.3f} | {d['ratio_no_jpeg']:.2f} |")
    lines += ["", "## Every E-001 estimator against the bound", "",
              "JPEG-60 cells are compared with the good-light bound (compression can only lose information).", "",
              "| Preset | Condition | Method | Baseline RMS (mm) | CRLB RMS (mm) | RMS / CRLB |", "|---|---|---|---|---|---|"]
    for r in res["comparison"]:
        lines.append(f"| {r['preset']} | {r['condition']} | {r['method']} | {r['baseline_rms_mm']:.3f} | "
                     f"{r['crlb_rms_mm']:.3f} | {r['efficiency_ratio']:.2f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="ml/configs/e005.json")
    ap.add_argument("--out", default="ml/evaluation/results/E-005")
    args = ap.parse_args()
    res = run(args.config, args.out)
    print(f"E-005 done in {res['meta']['runtime_s']} s; results in {args.out}")


if __name__ == "__main__":
    main()
