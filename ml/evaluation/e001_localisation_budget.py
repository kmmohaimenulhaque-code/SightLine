"""Experiment E-001 — single-frame localisation and scoring error of the deterministic baseline (SIMULATED).

Run:  python -m ml.evaluation.e001_localisation_budget --config ml/configs/e001.json --out ml/evaluation/results/E-001

Measures the image term of the error budget (docs/science/ERROR_BUDGET.md, terms E1-E4, E10) on synthetic frames with
exact ground truth. It does not measure timing (E7), stabilisation (E6) or ISP effects (E11).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import shutil
import time
from pathlib import Path

import cv2
import numpy as np

from app.calibration.camera import CameraModel
from app.vision.aiming_mark import measure_aiming_mark_all, shot_from_mark
from ml.datasets.provenance import git_commit, utc_now
from ml.datasets.synthetic_target import GENERATOR_VERSION, Degradation, random_spec, render

FIELDS = [
    "preset", "condition", "trial", "method", "detected", "gt_x_mm", "gt_y_mm", "est_x_mm", "est_y_mm",
    "vector_error_mm", "radial_error_mm", "gt_decimal", "est_decimal", "gt_integer", "est_integer",
    "centre_error_px", "scale_error_pct", "blur_px", "mm_per_px", "time_ms",
]


def _cell_seed(master: int, preset: str, condition: str) -> int:
    h = hashlib.sha256(f"{master}:{preset}:{condition}".encode()).hexdigest()
    return int(h[:12], 16)


def _degradation(cond: dict, mm_per_px: float, exposure_s: float, rng: np.random.Generator) -> Degradation:
    blur = cond["aim_speed_mm_s"] * exposure_s / mm_per_px
    return Degradation(
        psf_sigma_px=cond["psf_sigma_px"],
        motion_blur_px=blur,
        motion_blur_angle_deg=float(rng.uniform(0.0, 180.0)) if blur > 0 else 0.0,
        electrons_per_unit=cond["electrons_per_unit"],
        read_noise_e=cond["read_noise_e"],
        jpeg_quality=cond["jpeg_quality"],
    )


def run(config_path: str, out_dir: str, trials: int | None = None) -> dict:
    cfg = json.loads(Path(config_path).read_text())
    n_trials = int(trials or cfg["trials_per_cell"])
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sc = cfg["scene"]
    rows: list[dict] = []
    t_start = time.time()
    for preset, p in cfg["presets"].items():
        cam = CameraModel.from_hfov(p["width"], p["height"], p["hfov_deg"])
        mm_px_nominal = cam.mm_per_pixel_on_axis(10000.0)
        for cname, cond in cfg["conditions"].items():
            rng = np.random.default_rng(_cell_seed(cfg["master_seed"], preset, cname))
            for k in range(n_trials):
                deg = _degradation(cond, mm_px_nominal, cfg["exposure_s"], rng)
                spec = random_spec(rng, cam, deg, sc["impact_radius_mm"], tuple(sc["distance_range_mm"]),
                                   sc["max_tilt_deg"], sc["max_roll_deg"])
                s = render(spec, rng)
                gt = s.ground_truth
                gt_xy = np.array(gt["impact_xy_mm"])
                t0 = time.perf_counter()
                marks = measure_aiming_mark_all(s.image)
                dt_ms = (time.perf_counter() - t0) * 1000.0
                for method in cfg["methods"]:
                    row = {"preset": preset, "condition": cname, "trial": k, "method": method,
                           "gt_x_mm": gt_xy[0], "gt_y_mm": gt_xy[1],
                           "gt_decimal": gt["impact_score"]["decimal"], "gt_integer": gt["impact_score"]["integer"],
                           "blur_px": deg.motion_blur_px, "mm_per_px": gt["local_mm_per_px"], "time_ms": dt_ms}
                    mark = marks.get(method)
                    if mark is None:
                        row.update(detected=0)
                        rows.append(row)
                        continue
                    shot = shot_from_mark(mark, s.bore_px_canvas, up_direction_px=gt["up_direction_px"])
                    est = shot.impact_xy_mm
                    r_gt = 29.75 / gt["local_mm_per_px"]
                    row.update(
                        detected=1, est_x_mm=est[0], est_y_mm=est[1],
                        vector_error_mm=float(np.hypot(*(est - gt_xy))),
                        radial_error_mm=float(abs(np.hypot(*est) - np.hypot(*gt_xy))),
                        est_decimal=shot.score.decimal, est_integer=shot.score.integer,
                        centre_error_px=float(np.hypot(*(mark.centre_px - np.array(gt["target_centre_px_canvas"])))),
                        scale_error_pct=float((mark.ellipse.mean_radius / r_gt - 1.0) * 100.0),
                    )
                    rows.append(row)
    runtime_s = time.time() - t_start

    with open(out / "trials.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})

    summary = summarise(rows, cfg)
    meta = {
        "experiment_id": cfg["experiment_id"], "status_label": cfg["status_label"], "created_utc": utc_now(),
        "git_commit": git_commit(Path(__file__).resolve().parents[2]), "runtime_s": round(runtime_s, 1),
        "trials_per_cell": n_trials, "generator_version": GENERATOR_VERSION,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "opencv": cv2.__version__,
                        "machine": platform.machine(), "cpu_count": os.cpu_count(), "gpu": "none"},
    }
    (out / "summary.json").write_text(json.dumps({"meta": meta, "cells": summary}, indent=2))
    (out / "summary.md").write_text(to_markdown(summary, meta, cfg))
    shutil.copy(config_path, out / "config.json")
    return {"meta": meta, "cells": summary}


def summarise(rows: list[dict], cfg: dict) -> list[dict]:
    t = cfg["design_targets"]
    cells = []
    keys = sorted({(r["preset"], r["condition"], r["method"]) for r in rows},
                  key=lambda k: (list(cfg["presets"]).index(k[0]), list(cfg["conditions"]).index(k[1]),
                                 cfg["methods"].index(k[2])))
    for preset, cond, method in keys:
        rs = [r for r in rows if (r["preset"], r["condition"], r["method"]) == (preset, cond, method)]
        det = [r for r in rs if r["detected"]]
        n, nd = len(rs), len(det)
        cell = {"preset": preset, "condition": cond, "method": method, "n": n,
                "detected_pct": 100.0 * nd / n if n else 0.0}
        if nd:
            ve = np.array([r["vector_error_mm"] for r in det])
            re = np.array([r["radial_error_mm"] for r in det])
            ex = np.array([r["est_x_mm"] - r["gt_x_mm"] for r in det])
            ey = np.array([r["est_y_mm"] - r["gt_y_mm"] for r in det])
            dd = np.array([round(10 * r["est_decimal"]) - round(10 * r["gt_decimal"]) for r in det])
            cell.update(
                vector_p50_mm=float(np.median(ve)), vector_p95_mm=float(np.percentile(ve, 95)),
                vector_max_mm=float(ve.max()), radial_p95_mm=float(np.percentile(re, 95)),
                bias_x_mm=float(ex.mean()), bias_y_mm=float(ey.mean()),
                decimal_exact_pct=float(100.0 * np.mean(dd == 0)),
                decimal_within_1_pct=float(100.0 * np.mean(np.abs(dd) <= 1)),
                integer_exact_pct=float(100.0 * np.mean([r["est_integer"] == r["gt_integer"] for r in det])),
                centre_p95_px=float(np.percentile([r["centre_error_px"] for r in det], 95)),
                scale_p95_abs_pct=float(np.percentile(np.abs([r["scale_error_pct"] for r in det]), 95)),
                mean_time_ms=float(np.mean([r["time_ms"] for r in det])),
            )
            cell["passes"] = {
                "MEA-01": cell["vector_p95_mm"] <= t["MEA-01_p95_vector_error_mm"],
                "MEA-02": cell["integer_exact_pct"] >= t["MEA-02_integer_agreement_pct"],
                "MEA-03": max(abs(cell["bias_x_mm"]), abs(cell["bias_y_mm"])) <= t["MEA-03_abs_bias_mm"],
                "MEA-04": cell["detected_pct"] >= t["MEA-04_detection_pct"],
            }
        cells.append(cell)
    return cells


def to_markdown(cells: list[dict], meta: dict, cfg: dict) -> str:
    lines = [
        f"# {cfg['experiment_id']} — {cfg['title']}",
        "",
        f"**Status: {cfg['status_label']}** (synthetic frames with exact ground truth; not real-world measurement).",
        f"Created {meta['created_utc']} · commit `{meta['git_commit']}` · runtime {meta['runtime_s']} s on CPU "
        f"({meta['environment']['cpu_count']} cores; no GPU) · {meta['trials_per_cell']} trials per cell.",
        "",
        "| Preset | Condition | Method | Detected % | Vector p50 / p95 / max (mm) | Radial p95 (mm) | Bias x, y (mm) "
        "| Decimal exact % | Integer exact % | Centre p95 (px) | MEA-01 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in cells:
        if "vector_p95_mm" not in c:
            lines.append(f"| {c['preset']} | {c['condition']} | {c['method']} | {c['detected_pct']:.1f} | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {c['preset']} | {c['condition']} | {c['method']} | {c['detected_pct']:.1f} | "
            f"{c['vector_p50_mm']:.3f} / {c['vector_p95_mm']:.3f} / {c['vector_max_mm']:.3f} | {c['radial_p95_mm']:.3f} | "
            f"{c['bias_x_mm']:+.3f}, {c['bias_y_mm']:+.3f} | {c['decimal_exact_pct']:.1f} | {c['integer_exact_pct']:.1f} | "
            f"{c['centre_p95_px']:.3f} | {'PASS' if c['passes']['MEA-01'] else 'fail'} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="ml/configs/e001.json")
    ap.add_argument("--out", default="ml/evaluation/results/E-001")
    ap.add_argument("--trials", type=int, default=None, help="override trials per cell (quick runs)")
    args = ap.parse_args()
    res = run(args.config, args.out, args.trials)
    print(f"E-001 done in {res['meta']['runtime_s']} s; results in {args.out}")


if __name__ == "__main__":
    main()
