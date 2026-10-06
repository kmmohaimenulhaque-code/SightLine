"""Experiment E-002 — real target capture: static repeatability of the measured target centre (first real-world
camera baseline). Protocol: docs/experiments/E-002_E-003_PROTOCOL.md.

    python -m ml.evaluation.e002_static_capture analyse --capture <manifest.json> --video <clip>
    python -m ml.evaluation.e002_static_capture table ml/evaluation/results/E-002/<id> [<id> ...]

Phone and target fixed; one clip per configuration (Main 1x, Main 2x, Ultra Wide, Android ...). Reported separately
per configuration: mean, standard deviation, RMS, p95, maximum, drift, temporal spectrum — in pixels, in milliradians
and in millimetres at the target (using the MEASURED black diameter, never the nominal 59.5 mm).

This measures *precision* (repeatability) only. It cannot measure accuracy: a fixed bias of the estimated centre is
invisible in a static clip. Results are EXPERIMENTAL only for a validated TEAM_COLLECTED capture.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.vision.motion import write_frames_csv
from app.vision.video import iter_frames
from ml.datasets.capture import check_against_video, load_capture
from ml.datasets.provenance import git_commit, utc_now
from ml.evaluation.capture_analysis import MAX_INVALID_FRACTION, focal_length_px, frame_columns, scope, static_analysis, track
from ml.evaluation.status import result_status

EXPERIMENT_ID = "E-002"
RESULTS_DIR = "ml/evaluation/results/E-002"
MIN_DURATION_S = 10.0     # ASSUMED minimum for a repeatability figure and a spectrum down to 0.1 Hz
FROZEN_WARNING = 0.2      # ASSUMED: above this share of repeated positions, scatter is probably understated by the codec


def analyse(params: dict, category: str, frames, out_dir: str | Path, centre: str = "ellipse",
            video_errors: list[str] | None = None, warnings: list[str] | None = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    problems, warnings = list(video_errors or []), list(warnings or [])
    records, info = track(frames, gamma=params.get("gamma", 2.2), hint_px=params.get("target_hint_px"))
    if info["invalid_fraction"] > MAX_INVALID_FRACTION:
        problems.append(f"{info['n_invalid']} of {info['n_frames']} frames unusable (limit {MAX_INVALID_FRACTION:.0%})")
    focal, result = None, {}
    try:
        focal = focal_length_px(records, params)
        result, _ = static_analysis(records, focal["value"], out, centre, focal.get("mm_per_px_at_target"))
        if result["static"]["duration_s"] < MIN_DURATION_S:
            problems.append(f"only {result['static']['duration_s']:.1f} s of gap-free frames (need {MIN_DURATION_S:g} s)")
        if result["static"]["frozen_step_fraction"] > FROZEN_WARNING:
            warnings.append(f"{result['static']['frozen_step_fraction']:.0%} of frame-to-frame position changes are "
                            "below 0.001 px: the encoder is probably repeating picture content, so the scatter is a "
                            "lower estimate of the sensor's")
        dia = params["target"]["black_diameter_mm"]["value"]
        if abs(dia - 59.5) > 0.5:
            warnings.append(f"measured black diameter {dia} mm is outside the ISSF 59.5 ± 0.5 mm tolerance (CAL-04)")
    except (ValueError, KeyError) as exc:
        problems.append(f"analysis failed: {exc}")
    summary = {"experiment": EXPERIMENT_ID, "capture_id": params.get("capture_id"), "created_utc": utc_now(),
               "git_commit": git_commit(Path(__file__).resolve().parents[2]), "scope": scope(params),
               "setup": {k: params.get(k) for k in ("distance_mm", "target", "lighting", "orientation", "physical_setup")},
               "centre_estimator": centre, "tracking": info, "focal_length_px": focal, "result": result,
               "warnings": warnings, "status": result_status(category, not problems, "; ".join(problems) or None)}
    write_frames_csv(records, out / "frames.csv", extra=frame_columns(params))
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def table(summaries: list[dict]) -> str:
    lines = [f"# {EXPERIMENT_ID} — static repeatability per configuration", "",
             "Precision only (scatter of the estimated centre with phone and target fixed). Not accuracy.", "",
             "| Capture | Device / camera / mode | Status | mm/px | Std x, y (px) | RMS (px) | p95 (px) | Max (px) "
             "| RMS (mm at target) | p95 (mm) | Drift x, y (px/s) | Spectrum peak | Repeated-position share |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summaries:
        sc, st = s["scope"], s["status"]["experiment_status"]
        mode = f"{sc['device']} / {sc['camera']} / {sc['resolution']}@{sc['fps']}"
        if st != "COMPLETE" or not s["result"]:
            lines.append(f"| {s['capture_id']} | {mode} | **{st}** | — | — | — | — | — | — | — | — | — | — |")
            continue
        r, x = s["result"], s["result"]["static"]
        mm = r.get("at_target_mm", {})
        lines.append(f"| {s['capture_id']} | {mode} | {st} | {mm.get('mm_per_px', float('nan')):.3f} | "
                     f"{x['std_x_px']:.4f}, {x['std_y_px']:.4f} | {x['rms_px']:.4f} | {x['p95_px']:.4f} | {x['max_px']:.4f} | "
                     f"{mm.get('rms', float('nan')):.3f} | {mm.get('p95', float('nan')):.3f} | "
                     f"{x['drift_x_px_per_s']:+.5f}, {x['drift_y_px_per_s']:+.5f} | "
                     f"{r['spectrum_peak']['frequency_hz']:.2f} Hz ({r['spectrum_peak']['amplitude_px']:.4f} px) | "
                     f"{x['frozen_step_fraction']:.0%} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyse")
    a.add_argument("--capture", required=True)
    a.add_argument("--video", required=True)
    a.add_argument("--centre", default="ellipse", choices=("ellipse", "moments"))
    a.add_argument("--out", default=None)
    t = sub.add_parser("table")
    t.add_argument("runs", nargs="+")
    t.add_argument("--out", default=f"{RESULTS_DIR}/table.md")
    args = ap.parse_args(argv)
    if args.cmd == "analyse":
        rec = load_capture(args.capture)
        errors, warns = check_against_video(rec, args.video)
        out = args.out or f"{RESULTS_DIR}/{rec['sample_id']}"
        summ = analyse(rec["parameters"], rec["category"], ((i, t_, im) for i, t_, im, _ in iter_frames(args.video)),
                       out, args.centre, errors, warns)
        print(json.dumps(summ["status"], indent=2))
        print(f"results in {out}")
        return 0 if summ["status"]["experiment_status"] == "COMPLETE" else 2
    text = table([json.loads((Path(r) / "summary.json").read_text()) for r in args.runs])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
