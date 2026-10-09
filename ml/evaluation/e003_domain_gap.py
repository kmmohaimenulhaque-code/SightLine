"""Experiment E-003 — synthetic -> real domain gap: measure, on a static clip of the real target, the image
properties the synthetic generator assumes, and put them next to the same measurements on a matched synthetic clip.

    python -m ml.evaluation.e003_domain_gap analyse --capture <E-002 manifest.json> --video <clip>

Output per capture: ``gap.md`` / ``gap.json`` with, for each property, the synthetic value, the real observation and
the difference. The columns "importance" and "recommended generator change" are deliberately left for a decision
backed by a sensitivity run (re-run E-001 with the measured value and see whether the impact error moves): the
generator is not to be changed merely because real data looks different.

Measured here: geometry (size, axis ratio), edge blur, sharpening halo, levels/contrast, temporal noise and its
frame-to-frame correlation, block artefacts. Not measurable from this target and left open: tone curve (a two-level
target cannot give it), chromatic effects, rolling shutter and motion blur (static clip), lens distortion.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

from app.calibration.camera import CameraModel
from app.vision.aiming_mark import linearize
from app.vision.characterise import blockiness, edge_metrics, radial_profile, temporal_noise
from app.vision.motion import TargetTracker
from app.vision.video import iter_frames
from ml.datasets.capture import check_against_video, load_capture
from ml.datasets.provenance import git_commit, utc_now
from ml.datasets.synthetic_sequence import render_sequence
from ml.datasets.synthetic_target import Degradation
from ml.evaluation.capture_analysis import scope
from ml.evaluation.status import result_status

EXPERIMENT_ID = "E-003"
RESULTS_DIR = "ml/evaluation/results/E-003"
OPEN_ITEMS = ["tone curve / gamma (not measurable from a two-level target; needs a grey-step chart)",
              "local tone mapping and HDR behaviour", "chromatic aberration", "rolling shutter and motion blur "
              "(static clip)", "lens distortion (needs a calibration pattern)", "fixed-pattern noise",
              "ring numerals printed on official targets (the synthetic target and the E-002 print have none)"]


def characterise(frames, gamma: float | None = 2.2, max_frames: int = 120, hint_px=None) -> dict:
    """Track the target and measure its image properties over up to ``max_frames`` frames (static clip)."""
    tracker = TargetTracker(gamma=gamma, hint_px=hint_px)
    recs, crops, box, first_gray = [], [], None, None
    for fid, t, img in frames:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        r = tracker.process(fid, t, gray)
        if not r.valid:
            continue
        if box is None:
            half = int(math.ceil(2.2 * r.radius_px)) + 6
            x0, y0 = int(round(r.x)) - half, int(round(r.y)) - half
            if x0 < 0 or y0 < 0 or x0 + 2 * half > gray.shape[1] or y0 + 2 * half > gray.shape[0]:
                raise ValueError("target too close to the frame border")
            box, first_gray = (x0, y0, x0 + 2 * half, y0 + 2 * half), gray
        recs.append(r)
        crops.append(gray[box[1]:box[3], box[0]:box[2]])
        if len(recs) >= max_frames:
            break
    if len(recs) < 8:
        raise ValueError("fewer than 8 usable frames")
    med = lambda name: float(np.median([getattr(r, name) for r in recs]))
    cx, cy, a, b, th, rad = (med(n) for n in ("x", "y", "semi_major_px", "semi_minor_px", "ellipse_theta_rad", "radius_px"))
    stack = np.stack([linearize(c, gamma) for c in crops])
    mean_lin = stack.mean(axis=0)                      # averaging frames removes noise before the profile is taken
    prof_r, prof_v, _ = radial_profile(mean_lin, cx - box[0], cy - box[1], a, b, th)
    out = {"frames_used": len(recs), "black_radius_px": rad, "axis_ratio": b / a,
           "edge": edge_metrics(prof_r, prof_v, rad),
           "noise": temporal_noise(stack, cx - box[0], cy - box[1], rad),
           "blockiness_8": blockiness(first_gray[box[1]:box[3], box[0]:box[2]], 8),
           "blockiness_16": blockiness(first_gray[box[1]:box[3], box[0]:box[2]], 16),
           "profile": {"radius_px": prof_r.round(3).tolist(), "level": prof_v.round(5).tolist()}}
    return out


def matched_synthetic(real: dict, resolution: list[int], f_px: float, seed: int = 20261007) -> dict:
    """The same measurements on a synthetic static clip at the real clip's pixel scale, with the generator's default
    (E-001 good-light) assumptions. SIMULATED."""
    w, h = max(resolution), min(resolution)
    cam = CameraModel(w, h, f_px, f_px, (w - 1) / 2.0, (h - 1) / 2.0)
    size = int(2 ** math.ceil(math.log2(max(96.0, 6.0 * real["black_radius_px"]))))
    frames, _ = render_sequence(cam, np.zeros((real["frames_used"], 2)), np.random.default_rng(seed),
                                Degradation(), window_px=(size, size), yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0)
    return characterise(((i, i / 30.0, f) for i, f in enumerate(frames)), max_frames=real["frames_used"])


ROWS = [("Black radius (px)", ("black_radius_px",), "geometry: matched by construction (same f_px)"),
        ("Axis ratio b/a", ("axis_ratio",), "geometry: target tilt / perspective"),
        ("Edge 10-90 % width (px)", ("edge", "edge_10_90_px"), "optics + ISP: PSF sigma 0.7 px + pixel aperture"),
        ("Equivalent edge sigma (px)", ("edge", "edge_sigma_px"), "optics + ISP: blur"),
        ("Halo overshoot (fraction of contrast)", ("edge", "overshoot_fraction"), "ISP: no sharpening modelled"),
        ("Undershoot inside the edge", ("edge", "undershoot_fraction"), "ISP: no sharpening modelled"),
        ("White/black contrast ratio", ("edge", "contrast_ratio"), "reflectances 0.85 / 0.04, no flare"),
        ("Temporal noise, white (rel. to white)", ("noise", "white_noise_rel"), "shot + read noise, 3000 e-"),
        ("Temporal noise, black (rel. to white)", ("noise", "black_noise_rel"), "shot + read noise"),
        ("Noise lag-1 temporal correlation", ("noise", "white_lag1_correlation"), "independent frames (no denoiser/codec)"),
        ("Blockiness, 8 px grid", ("blockiness_8",), "compression: JPEG q90 per frame, no video codec"),
        ("Blockiness, 16 px grid", ("blockiness_16",), "compression: no video codec")]


def _get(d: dict, path: tuple) -> float:
    for k in path:
        d = d[k]
    return float(d)


def gap_table(real: dict, synthetic: dict) -> list[dict]:
    rows = []
    for name, path, assumption in ROWS:
        s, r = _get(synthetic, path), _get(real, path)
        rows.append({"property": name, "synthetic_assumption": assumption, "synthetic_value": s, "real_observation": r,
                     "difference": r - s, "relative_difference": (r - s) / abs(s) if abs(s) > 1e-9 else None,
                     "importance": "TO BE DECIDED by a sensitivity run against the measurement objective",
                     "recommended_generator_change": "none until importance is established"})
    return rows


def to_markdown(summary: dict) -> str:
    lines = [f"# {EXPERIMENT_ID} — synthetic → real gap for `{summary['capture_id']}`", "",
             f"Status: **{summary['status']['experiment_status']}** · evidence class of the real column: "
             f"**{summary['status']['evidence_class']}** · the synthetic column is SIMULATED.", ""]
    if summary["status"].get("banner"):
        lines += [f"**{summary['status']['banner']}**", ""]
    lines += ["| Property | Synthetic assumption | Synthetic value | Real observation | Difference | Importance "
              "| Recommended generator change |", "|---|---|---|---|---|---|---|"]
    for r in summary.get("rows", []):
        rel = "" if r["relative_difference"] is None else f" ({r['relative_difference']:+.0%})"
        lines.append(f"| {r['property']} | {r['synthetic_assumption']} | {r['synthetic_value']:.4g} | "
                     f"{r['real_observation']:.4g} | {r['difference']:+.3g}{rel} | {r['importance']} | "
                     f"{r['recommended_generator_change']} |")
    lines += ["", "Not measured by this experiment (open):"] + [f"* {x}" for x in OPEN_ITEMS]
    return "\n".join(lines) + "\n"


def analyse(params: dict, category: str, frames, out_dir: str | Path, f_px: float | None = None,
            video_errors: list[str] | None = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    problems = list(video_errors or [])
    summary = {"experiment": EXPERIMENT_ID, "capture_id": params.get("capture_id"), "created_utc": utc_now(),
               "git_commit": git_commit(Path(__file__).resolve().parents[2]), "scope": scope(params), "open_items": OPEN_ITEMS}
    try:
        real = characterise(frames, params.get("gamma", 2.2), hint_px=params.get("target_hint_px"))
        if f_px is None:    # target-anchored, as in E-002
            major = 2.0 * real["black_radius_px"] / math.sqrt(real["axis_ratio"])
            f_px = major * params["distance_mm"]["value"] / params["target"]["black_diameter_mm"]["value"]
        synth = matched_synthetic(real, params["resolution"], f_px)
        summary.update(f_px=f_px, real=real, synthetic=synth, rows=gap_table(real, synth))
    except (ValueError, KeyError) as exc:
        problems.append(f"analysis failed: {exc}")
    summary["status"] = result_status(category, not problems, "; ".join(problems) or None)
    (out / "gap.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "gap.md").write_text(to_markdown(summary))
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyse")
    a.add_argument("--capture", required=True)
    a.add_argument("--video", required=True)
    a.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    rec = load_capture(args.capture)
    errors, _ = check_against_video(rec, args.video)
    out = args.out or f"{RESULTS_DIR}/{rec['sample_id']}"
    summ = analyse(rec["parameters"], rec["category"], ((i, t, im) for i, t, im, _ in iter_frames(args.video)), out,
                   video_errors=errors)
    print(json.dumps(summ["status"], indent=2))
    print(f"results in {out}")
    return 0 if summ["status"]["experiment_status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
