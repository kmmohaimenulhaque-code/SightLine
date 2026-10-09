"""Experiment E-004a — does the image follow a known camera rotation? (OIS/EIS transfer function, iPhone 15 first)

    physical angular motion  ->  expected image displacement  ->  observed image displacement

Protocol: docs/experiments/E-004A_PROTOCOL.md. Tests: A_static, B_step, C_ramp (ground truth = lever geometry),
D_oscillation (ground truth = an independent gyroscope rigidly fixed to the camera). The phone's Main camera is
compared with its Ultra Wide camera (no OIS listed by Apple) as the control.

Commands
    python -m ml.evaluation.e004a_ois_transfer expected
    python -m ml.evaluation.e004a_ois_transfer analyse --capture data/manifests/captures/<id>.json --video clip.mov
    python -m ml.evaluation.e004a_ois_transfer compare ml/evaluation/results/E-004a/<id> [<id> ...]
    python -m ml.evaluation.e004a_ois_transfer synthetic-sanity

Evidence rules: ``analyse`` yields EXPERIMENTAL evidence only for a validated TEAM_COLLECTED capture. The
``synthetic-sanity`` command exercises the same code on simulated frames with an injected, hypothetical stabiliser to
show that the harness recovers what was injected; its output is SIMULATED and says so in every file it writes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np

from app.analytics.timeseries import find_plateaus, gyro_referenced_gain, longest_contiguous, step_table
from app.calibration.angular import Measured, expected_image_shift_px, lever_angle_rad
from app.calibration.camera import CameraModel
from app.imu.gyro import load_gyro_csv
from app.vision.motion import write_frames_csv
from app.vision.video import iter_frames
from ml.datasets.capture import check_against_video, load_capture
from ml.datasets.provenance import git_commit, utc_now
from ml.datasets.synthetic_sequence import hypothetical_stabiliser, render_sequence
from ml.datasets.synthetic_target import Degradation
from ml.evaluation.capture_analysis import (
    MAX_INVALID_FRACTION,
    focal_length_px,
    frame_columns,
    positions,
    scope,
    static_analysis,
    track,
)
from ml.evaluation.status import SANITY_BANNER, result_status

EXPERIMENT_ID = "E-004a"
DEFAULT_CONFIG = "ml/configs/e004a.json"
RESULTS_DIR = "ml/evaluation/results/E-004a"


# ----------------------------------------------------------------------------------------------------------------------
# Analysis of one capture
# ----------------------------------------------------------------------------------------------------------------------
def _expected_steps_px(params: dict, f_px: Measured) -> tuple[list[float], list[float], list[dict]]:
    jig = params["jig"]
    base = Measured.of(jig["plateaus"][0]["displacement_mm"])
    exp, sig, angles = [], [], []
    for plat in jig["plateaus"]:
        d = Measured.of(plat["displacement_mm"])
        rel = Measured(d.value - base.value, math.hypot(d.sigma, base.sigma) if d.value != base.value else 0.0)
        th = lever_angle_rad(rel, jig["radius_mm"])
        e = expected_image_shift_px(th, f_px, jig["pivot_ahead_mm"], params["distance_mm"])
        exp.append(e.value)
        sig.append(e.sigma)
        angles.append({"theta_mrad": th.value * 1e3, "theta_sigma_mrad": th.sigma * 1e3})
    return exp, sig, angles


def analyse(params: dict, category: str, frames, out_dir: str | Path, gyro_path: str | Path | None = None,
            centre: str = "ellipse", video_errors: list[str] | None = None, warnings: list[str] | None = None) -> dict:
    """Analyse one clip. ``frames`` yields ``(frame_id, timestamp_s, image)``. Writes frames.csv and summary.json."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    test = params["test"]
    problems = list(video_errors or [])
    warnings = list(warnings or [])
    records, info = track(frames, gamma=params.get("gamma", 2.2), hint_px=params.get("target_hint_px"))
    if info["invalid_fraction"] > MAX_INVALID_FRACTION:
        problems.append(f"{info['n_invalid']} of {info['n_frames']} frames unusable (limit {MAX_INVALID_FRACTION:.0%})")
    idx, t, xy = positions(records, centre)
    summary: dict = {"experiment": EXPERIMENT_ID, "capture_id": params.get("capture_id"), "test": test,
                     "created_utc": utc_now(), "git_commit": git_commit(Path(__file__).resolve().parents[2]),
                     "scope": scope(params), "centre_estimator": centre, "tracking": info}
    n = len(records)
    est = [float("nan")] * n
    expd = [float("nan")] * n
    result: dict = {}
    focal = None
    try:
        focal = focal_length_px(records, params)
        f = Measured(focal["value"], focal["sigma"])
        if test == "A_static":
            result, mean = static_analysis(records, f.value, out, centre, focal.get("mm_per_px_at_target"))
            for i, p in zip(idx, xy):
                est[i], expd[i] = float(np.hypot(*(p - mean)) / f.value * 1e3), 0.0
        elif test in ("B_step", "C_ramp"):
            exp_px, exp_sig, angles = _expected_steps_px(params, f)
            windows = [p.get("window_s") for p in params["jig"]["plateaus"]]
            if all(w is not None for w in windows):
                plateaus = [(int(np.searchsorted(t, w[0])), int(np.searchsorted(t, w[1], side="right"))) for w in windows]
                source = "operator time windows"
            else:
                smallest = min(abs(b - a) for a, b in zip(exp_px[:-1], exp_px[1:]))
                plateaus = find_plateaus(t, xy, floor_px=max(0.02, 0.25 * smallest))
                source = "automatic segmentation (stillness floor = 25 % of the smallest expected step)"
            table = step_table(t, xy, plateaus, exp_px, exp_sig)
            for row, ang in zip(table["rows"], angles):
                row.update(ang)
            result = {"plateau_source": source, "steps": table}
            axis, base = np.array(table["axis_unit"]), xy[plateaus[0][0]:plateaus[0][1]].mean(axis=0)
            for i, p in zip(idx, xy):
                est[i] = float((p - base) @ axis / f.value * 1e3)
            for (i0, i1), row in zip(plateaus, table["rows"]):
                for i in idx[i0:i1]:
                    expd[i] = row["expected_px"] / f.value * 1e3
        elif test == "D_oscillation":
            if gyro_path is None:
                raise ValueError("D_oscillation needs the gyroscope log")
            g = params["gyro_log"]
            cols = g.get("columns") or {}
            log = load_gyro_csv(gyro_path, cols.get("time"), cols.get("x"), cols.get("y"), cols.get("z"),
                                g.get("time_unit"), g.get("rate_unit", "rad/s"))
            run = longest_contiguous(idx)
            exposure = params.get("exposure") if isinstance(params.get("exposure"), (int, float)) else 0.0
            if not exposure:
                warnings.append("exposure time unknown: the exposure averaging of fast motion is not modelled")
            bands = tuple(tuple(b) for b in params.get("bands_hz", ((0.5, 2.0), (2.0, 5.0), (5.0, 10.0), (10.0, 14.0))))
            gain = gyro_referenced_gain(t[run], (xy[run] - xy[run].mean(axis=0)) / f.value, log.t, log.omega,
                                        bands=bands, exposure_s=float(exposure))
            series = gain.pop("series")
            if series is not None:
                pos, img_bp, ref_bp = series
                sign = 1.0 if float(img_bp @ ref_bp) >= 0 else -1.0
                for j, a, b in zip(pos, img_bp, ref_bp):
                    i = idx[run][j]
                    est[i], expd[i] = float(a * 1e3), float(sign * b * 1e3)
            result = {"gyro": {"columns": log.columns, "time_unit": log.time_unit, "rate_unit": log.rate_unit},
                      "response": gain, "frames_used": int(run.stop - run.start)}
            if not any(b["usable"] for b in gain["bands"]):
                problems.append("no frequency band had enough excitation to measure a gain")
        else:
            raise ValueError(f"unknown test {test!r}")
    except (ValueError, KeyError, np.linalg.LinAlgError) as exc:
        problems.append(f"analysis failed: {exc}")
    summary["focal_length_px"] = focal
    summary["result"] = result
    summary["warnings"] = warnings
    summary["status"] = result_status(category, not problems, "; ".join(problems) or None)
    resid = [e - x if math.isfinite(e) and math.isfinite(x) else float("nan") for e, x in zip(est, expd)]
    write_frames_csv(records, out / "frames.csv", extra=frame_columns(params),
                     per_frame={"estimated_rotation_mrad": est, "expected_rotation_mrad": expd, "residual_mrad": resid})
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


# ----------------------------------------------------------------------------------------------------------------------
# Main vs Ultra Wide comparison
# ----------------------------------------------------------------------------------------------------------------------
def classify(ratio: float, sigma: float, th: dict) -> str:
    """TRACKS / SUPPRESSED / INCONCLUSIVE for a response ratio (thresholds are ASSUMED; see ml/configs/e004a.json).

    TRACKS needs both agreement with 1 and enough precision to exclude suppression: a ratio that is merely
    *compatible* with 1 because its uncertainty is large is INCONCLUSIVE, not TRACKS.
    """
    if abs(ratio - 1.0) <= max(th["tracks_tolerance"], 2.0 * sigma) and ratio - 2.0 * sigma > th["suppressed_below"]:
        return "TRACKS"
    if ratio < th["suppressed_below"] and ratio + 2.0 * sigma < 1.0:
        return "SUPPRESSED"
    return "INCONCLUSIVE"


def _conditions(summary: dict) -> dict[str, tuple[str, float, float, float]]:
    """condition label -> (expected text, observed value, ratio, ratio sigma) for one analysed capture."""
    out, res, test = {}, summary["result"], summary["test"]
    f = summary["focal_length_px"]["value"]
    if test in ("B_step", "C_ramp"):
        for row in res["steps"]["rows"][1:]:
            label = f"{test} {row['theta_mrad']:.2f} mrad"
            out[label] = (f"{row['theta_mrad']:.3f} ± {row['theta_sigma_mrad']:.3f} mrad",
                          row["observed_px"] / f * 1e3, row["response_ratio"], row["response_ratio_sigma"])
    elif test == "D_oscillation":
        for b in res["response"]["bands"]:
            if b["usable"]:
                label = f"D {b['f_lo_hz']:g}-{b['f_hi_hz']:g} Hz"
                out[label] = (f"{b['excitation_rms_rad'] * 1e3:.3f} mrad RMS (gyro)", b["image_rms_rad"] * 1e3,
                              b["gain"], float("nan"))
    return out


def compare(summaries: list[dict], thresholds: dict) -> str:
    """Markdown comparison table (brief §8) with a rule-based, scoped reading. Only COMPLETE runs are admitted."""
    usable = [s for s in summaries if s["status"]["experiment_status"] == "COMPLETE"]
    rejected = [s for s in summaries if s not in usable]
    by_cam: dict[str, dict] = {}
    for s in usable:
        by_cam.setdefault(s["scope"]["camera"], {}).update(_conditions(s))
    lines = [f"# {EXPERIMENT_ID} — Main vs Ultra Wide response to known rotation", ""]
    if rejected:
        lines += ["Excluded (not COMPLETE): " + ", ".join(f"{s['capture_id']} [{s['status']['experiment_status']}]"
                                                           for s in rejected), ""]
    main = next((c for c in by_cam if c.startswith("main_1x")), None)
    uw = next((c for c in by_cam if c.startswith("ultra_wide")), None)
    if not main or not uw:
        return "\n".join(lines + ["**No comparison possible:** need at least one COMPLETE Main (main_1x) and one "
                                  "COMPLETE Ultra Wide (ultra_wide) run.", ""])
    lines += ["| Condition | Expected motion | Main observed (mrad) | Ultra Wide observed (mrad) | Main response ratio "
              "| UW response ratio | Reading |", "|---|---|---|---|---|---|---|"]
    verdicts = []
    for label in sorted(set(by_cam[main]) & set(by_cam[uw])):
        e, mo, mr, ms = by_cam[main][label]
        _, uo, ur, us = by_cam[uw][label]
        ms0, us0 = (0.0 if math.isnan(ms) else ms), (0.0 if math.isnan(us) else us)
        cm, cu = classify(mr, ms0, thresholds), classify(ur, us0, thresholds)
        if cu == "TRACKS" and cm == "SUPPRESSED":
            v = "Main suppressed, control tracks"
        elif cu == "TRACKS" and cm == "TRACKS":
            v = "both track"
        elif cu == "SUPPRESSED" and cm == "SUPPRESSED":
            v = "both suppressed"
        elif cu != "TRACKS":
            v = "control does not track — check setup"
        else:
            v = "inconclusive"
        verdicts.append(v)
        fmt = lambda r, s: f"{r:.3f}" + (f" ± {s:.3f}" if not math.isnan(s) else "")
        lines.append(f"| {label} | {e} | {mo:.3f} | {uo:.3f} | {fmt(mr, ms)} | {fmt(ur, us)} | {v} |")
    lines.append("")
    if not verdicts:
        lines.append("**No common conditions** between the Main and Ultra Wide runs.")
    elif any(v.startswith("control does not") for v in verdicts):
        lines.append("**Reading: INVALID comparison.** The Ultra Wide control did not reproduce the expected motion in at "
                     "least one condition; the geometry, mounting or focal length must be checked before anything is "
                     "concluded about the Main camera.")
    elif any(v.startswith("Main suppressed") for v in verdicts):
        lines.append("**Reading:** in the conditions marked, the Main camera showed less image motion than the known "
                     "rotation while the Ultra Wide control followed it. This is strong evidence that stabilisation "
                     "suppressed image motion on the Main camera in those conditions.")
    elif any(v == "both suppressed" for v in verdicts):
        lines.append("**Reading:** both cameras showed less motion than expected. Electronic/software stabilisation, or "
                     "a setup error common to both runs, must be investigated before attributing this to OIS.")
    elif all(v == "both track" for v in verdicts):
        lines.append("**Reading:** both cameras followed the known rotation in every condition tested. No suppression "
                     "was observed *in these conditions*. Step and ramp tests probe the settled (DC) response only: "
                     "they cannot exclude a stabiliser that acts on faster motion and then re-centres. Only the "
                     "oscillation bands of test D speak to that.")
    else:
        lines.append("**Reading:** inconclusive in at least one condition; see the table.")
    sc = next(s for s in usable if s["scope"]["camera"] == main)["scope"]
    lines += ["", f"**Scope.** These results apply to: {sc['device']}, {sc['os_version']}, cameras `{main}` and `{uw}`, "
              f"{sc['capture_app']}, {sc['resolution']} @ {sc['fps']} fps, {sc['codec']}, stabilisation setting "
              f"\"{sc['stabilisation_mode']}\". They are not a statement about iPhones in general.",
              "", f"Thresholds (ASSUMED): tracks if |ratio − 1| ≤ max({thresholds['tracks_tolerance']}, 2σ) and ratio − 2σ > "
              f"{thresholds['suppressed_below']}; suppressed if ratio < {thresholds['suppressed_below']} and "
              f"ratio + 2σ < 1; otherwise inconclusive.", ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------------------------------
# Expected-result calculations (DERIVED)
# ----------------------------------------------------------------------------------------------------------------------
def expected_table(cfg: dict) -> str:
    lines = ["# E-004a — expected image displacement for known rotations (DERIVED, not measured)", "",
             "Δu = f_px · tan θ. The focal lengths below are **prior estimates** used only to plan the experiment "
             "(`ml/configs/e004a.json` states where each comes from). The analysis never uses them: it measures f_px "
             "from the printed target in each clip.", "",
             "| Camera mode (prior f_px) | " + " | ".join(f"{a:g} mrad" for a in cfg["target_angles_mrad"]) + " |",
             "|---|" + "---|" * len(cfg["target_angles_mrad"])]
    for name, cam in cfg["camera_priors"].items():
        cells = [f"{expected_image_shift_px(a * 1e-3, cam['f_px']).value:.2f} px" for a in cfg["target_angles_mrad"]]
        lines.append(f"| {name} ({cam['f_px']:g} px, {cam['status']}) | " + " | ".join(cells) + " |")
    lines += ["", "Lever displacement needed, d = r · tan θ:", "",
              "| Lever radius | " + " | ".join(f"{a:g} mrad" for a in cfg["target_angles_mrad"]) + " |",
              "|---|" + "---|" * len(cfg["target_angles_mrad"])]
    for r in cfg["example_radii_mm"]:
        lines.append(f"| {r:g} mm | " + " | ".join(f"{r * math.tan(a * 1e-3):.3f} mm" for a in cfg["target_angles_mrad"]) + " |")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------------------------------------------------
# Synthetic sanity check (SIMULATED) — verifies the harness, says nothing about any phone
# ----------------------------------------------------------------------------------------------------------------------
def _through_codec(frames: np.ndarray, fps: float, workdir: Path, name: str, codec: dict) -> tuple[list, str]:
    """Encode with ffmpeg and read back through the normal video reader, if ffmpeg is installed; else pass through."""
    items = [(i, i / fps, f) for i, f in enumerate(frames)]
    exe = shutil.which("ffmpeg")
    if exe is None or not codec.get("enabled", True):
        return items, "none (frames passed directly)"
    path = workdir / f"{name}.mp4"
    h, w = frames.shape[1:]
    cmd = [exe, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}", "-r", f"{fps:g}", "-i", "-",
           "-c:v", codec["encoder"], "-crf", str(codec["crf"]), "-pix_fmt", "yuv420p", str(path)]
    try:
        subprocess.run(cmd, input=frames.tobytes(), check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        return items, "none (ffmpeg encode failed; frames passed directly)"
    decoded = [(i, t, img) for i, t, img, _ in iter_frames(path)]
    path.unlink(missing_ok=True)
    return decoded, f"{codec['encoder']} crf {codec['crf']}"


def _step_profile(levels_rad: list[float], fps: float, hold_s: float, move_s: float, rng) -> np.ndarray:
    parts = [np.full(int(hold_s * fps), levels_rad[0])]
    for a, b in zip(levels_rad[:-1], levels_rad[1:]):
        m = int(move_s * fps)
        parts += [np.linspace(a, b, m) + rng.normal(0, 3e-4, m), np.full(int(hold_s * fps), b)]  # disturbed move, hold
    return np.concatenate(parts)


def synthetic_sanity(cfg: dict, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sc, rng = cfg["synthetic_sanity"], np.random.default_rng(cfg["synthetic_sanity"]["seed"])
    deg = Degradation(jpeg_quality=None, **sc["degradation"])
    angles = [a * 1e-3 for a in sc["step_angles_mrad"]]
    jig_r = sc["jig_radius_mm"]
    rows, codec_used = [], None
    for cam_name, cam_cfg in sc["cameras"].items():
        cam = CameraModel(cam_cfg["width"], cam_cfg["height"], cam_cfg["f_px"], cam_cfg["f_px"],
                          (cam_cfg["width"] - 1) / 2.0, (cam_cfg["height"] - 1) / 2.0)
        base = {"capture_id": None, "camera": cam_name, "resolution": [cam.width, cam.height], "device": "SYNTHETIC",
                "distance_mm": {"value": 10000.0, "sigma": 5.0},
                "target": {"black_diameter_mm": {"value": 59.5, "sigma": 0.2}}, "exposure": 0.0}

        def run(test, hyp, theta_true, fps, extra, gyro=None):
            nonlocal codec_used
            h = sc["hypotheses"][hyp]
            apparent = theta_true if h is None else hypothetical_stabiliser(theta_true, fps, h["corner_hz"], h["gain"])
            frames, _ = render_sequence(cam, np.column_stack([np.zeros_like(apparent), apparent]), rng, deg)
            name = f"{cam_name}__{test}__{hyp}"
            items, codec_used = _through_codec(frames, fps, out, name, sc["codec"])
            params = dict(base, capture_id=f"synthetic-{name}", test=test, fps=fps, **extra)
            return analyse(params, "SYNTHETIC", items, out / name, gyro_path=gyro)

        # A — static
        s = run("A_static", "none", np.zeros(int(sc["static_s"] * sc["fps"])), sc["fps"], {})
        ok = s["status"]["sanity_check_passed_analysis_checks"]
        rows.append({"camera": cam_name, "test": "A_static", "hypothesis": "none", "quantity": "RMS (px)",
                     "injected": 0.0, "recovered": s["result"]["static"]["rms_px"] if ok else None, "tolerance": None,
                     "pass": ok})
        # B — steps
        theta = _step_profile(angles, sc["fps"], sc["hold_s"], sc["move_s"], rng)
        jig = {"radius_mm": {"value": jig_r, "sigma": 1.0}, "pivot_ahead_mm": {"value": 0.0, "sigma": 0.0},
               "plateaus": [{"displacement_mm": {"value": jig_r * math.tan(a), "sigma": 0.0}} for a in angles]}
        for hyp in sc["step_hypotheses"]:
            s = run("B_step", hyp, theta, sc["fps"], {"jig": jig})
            h = sc["hypotheses"][hyp]
            settled = 1.0 if h is None or h["corner_hz"] > 0 else 1.0 - h["gain"]   # DC gain of the injected model
            if not s["status"]["sanity_check_passed_analysis_checks"]:
                rows.append({"camera": cam_name, "test": "B_step", "hypothesis": hyp, "quantity": "analysis",
                             "injected": settled, "recovered": None, "tolerance": None, "pass": False,
                             "note": s["status"].get("reason")})
                continue
            for row in s["result"]["steps"]["rows"][1:]:
                tol = max(sc["ratio_tolerance"], 3.0 * sc["noise_floor_px"] / abs(row["expected_px"]))
                rows.append({"camera": cam_name, "test": "B_step", "hypothesis": hyp,
                             "quantity": f"settled ratio @ {row['theta_mrad']:.2f} mrad ({row['expected_px']:.2f} px)",
                             "injected": settled, "recovered": row["response_ratio"], "tolerance": tol,
                             "pass": abs(row["response_ratio"] - settled) <= tol, "creep_px": row["creep_px"]})
        # D — oscillation against a synthetic gyroscope
        fps_d, dur = sc["oscillation_fps"], sc["oscillation_s"]
        tt = np.arange(int(dur * fps_d)) / fps_d
        tg = np.arange(int((dur + 4.0) * sc["gyro_rate_hz"])) / sc["gyro_rate_hz"]
        offset = 1.732
        tone = lambda time: sum(a * 1e-3 * np.sin(2 * np.pi * f * time + k) for k, (f, a) in enumerate(sc["tones_hz_mrad"]))
        env = lambda time: 0.5 * (1 + np.tanh((time - 2.5) / 0.3))
        omega = np.zeros((len(tg), 3))
        omega[:, 0] = np.gradient(tone(tg) * env(tg), tg)
        omega += rng.normal(0, sc["gyro_noise_rad_s"], omega.shape) + np.array([0.004, -0.003, 0.002])
        gyro_file = out / f"{cam_name}__gyro.csv"
        with open(gyro_file, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["seconds_elapsed", "x", "y", "z"])
            w.writerows([f"{a:.6f}", f"{b:.8f}", f"{c:.8f}", f"{d:.8f}"] for a, (b, c, d) in zip(tg, omega))
        theta = tone(tt + offset) * env(tt + offset)
        for hyp in sc["oscillation_hypotheses"]:
            s = run("D_oscillation", hyp, theta, fps_d,
                    {"gyro_log": {"rate_unit": "rad/s"}, "bands_hz": sc["bands_hz"]}, gyro=gyro_file)
            h = sc["hypotheses"][hyp]
            injected = 1.0 if h is None else 1.0 - h["gain"]
            if not s["status"]["sanity_check_passed_analysis_checks"]:
                rows.append({"camera": cam_name, "test": "D_oscillation", "hypothesis": hyp, "quantity": "analysis",
                             "injected": injected, "recovered": None, "tolerance": None, "pass": False,
                             "note": s["status"].get("reason")})
                continue
            for b in s["result"]["response"]["bands"]:
                if b["usable"]:
                    rows.append({"camera": cam_name, "test": "D_oscillation", "hypothesis": hyp,
                                 "quantity": f"gain {b['f_lo_hz']:g}-{b['f_hi_hz']:g} Hz", "injected": injected,
                                 "recovered": b["gain"], "tolerance": sc["gain_tolerance"],
                                 "pass": abs(b["gain"] - injected) <= sc["gain_tolerance"]})
        gyro_file.unlink(missing_ok=True)
    report = {"experiment": EXPERIMENT_ID, "kind": "synthetic_sanity", "banner": SANITY_BANNER,
              "status": result_status("SYNTHETIC", all(r["pass"] for r in rows)), "created_utc": utc_now(),
              "git_commit": git_commit(Path(__file__).resolve().parents[2]), "codec": codec_used,
              "config": sc, "rows": rows}
    (out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    md = [f"# {EXPERIMENT_ID} — synthetic sanity check of the analysis harness", "", f"**{SANITY_BANNER}**", "",
          f"Experiment status: **{report['status']['experiment_status']}**. Evidence class of this file: "
          f"**{report['status']['evidence_class']}**. Codec path: {codec_used}. Seed {sc['seed']}.", "",
          "The \"hypotheses\" are invented stabiliser behaviours injected into simulated frames. They exist only to "
          "check that the harness reports what was injected. They are not models of an iPhone.", "",
          "| Camera scale | Test | Injected behaviour | Quantity | Injected | Recovered | Tolerance | Harness check |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rec = "—" if r["recovered"] is None else f"{r['recovered']:.3f}"
        tol = "—" if r["tolerance"] is None else f"±{r['tolerance']:.3f}"
        md.append(f"| {r['camera']} | {r['test']} | {r['hypothesis']} | {r['quantity']} | {r['injected']:.3f} | {rec} | "
                  f"{tol} | {'ok' if r['pass'] else 'FAIL'} |")
    (out / "summary.md").write_text("\n".join(md) + "\n")
    return report


# ----------------------------------------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("expected")
    a = sub.add_parser("analyse")
    a.add_argument("--capture", required=True)
    a.add_argument("--video", required=True)
    a.add_argument("--gyro", default=None)
    a.add_argument("--centre", default="ellipse", choices=("ellipse", "moments"))
    a.add_argument("--out", default=None)
    c = sub.add_parser("compare")
    c.add_argument("runs", nargs="+", help="result directories containing summary.json")
    c.add_argument("--out", default=f"{RESULTS_DIR}/comparison.md")
    s = sub.add_parser("synthetic-sanity")
    s.add_argument("--out", default=f"{RESULTS_DIR}/synthetic_sanity")
    args = ap.parse_args(argv)
    cfg = json.loads(Path(args.config).read_text())
    if args.cmd == "expected":
        print(expected_table(cfg))
        return 0
    if args.cmd == "analyse":
        rec = load_capture(args.capture)
        errors, warns = check_against_video(rec, args.video)
        p = rec["parameters"]
        gyro = args.gyro or (str(Path(args.capture).parent / p["gyro_log"]["file"]) if p.get("gyro_log") else None)
        out = args.out or f"{RESULTS_DIR}/{rec['sample_id']}"
        frames = ((i, t, img) for i, t, img, _ in iter_frames(args.video))
        summ = analyse(p, rec["category"], frames, out, gyro, args.centre, errors, warns)
        print(json.dumps(summ["status"], indent=2))
        print(f"results in {out}")
        return 0 if summ["status"]["experiment_status"] == "COMPLETE" else 2
    if args.cmd == "compare":
        text = compare([json.loads((Path(r) / "summary.json").read_text()) for r in args.runs], cfg["thresholds"])
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        print(text)
        return 0
    rep = synthetic_sanity(cfg, args.out)
    print(f"synthetic sanity: {sum(r['pass'] for r in rep['rows'])}/{len(rep['rows'])} harness checks ok -> {args.out}")
    return 0 if all(r["pass"] for r in rep["rows"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
