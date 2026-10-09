"""Experiment E-004b — Android Camera2 capability probe and OIS-sample validation (off-device analysis).

The probe app (app/mobile/android-probe) writes two kinds of JSON on the phone:

* ``sightline_camera2_probe`` — every CameraCharacteristics key of every camera, plus motion-sensor facts;
* ``sightline_ois_log``       — a 10 s metadata-only capture: per-frame sensor timestamp and OIS samples, and raw
                                gyroscope events, with OIS requested ON or OFF.

    python -m ml.evaluation.e004b_android_probe capabilities <probe.json>
    python -m ml.evaluation.e004b_android_probe ois-log <ois_log.json> [<ois_log.json> ...]

Nothing is assumed about a device before its own file has been read. Results describe that one device and Android
build. A JSON from a real phone is TEAM_COLLECTED data; pass ``--category SYNTHETIC`` for fabricated test files.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from app.analytics.timeseries import _bandpass, integrate_rate
from ml.datasets.provenance import git_commit, sha256_file, utc_now
from ml.evaluation.status import result_status

EXPERIMENT_ID = "E-004b"
RESULTS_DIR = "ml/evaluation/results/E-004b"
# Android constants (android.hardware.camera2.CameraMetadata), written out so the report is readable.
LENS_FACING = {0: "FRONT", 1: "BACK", 2: "EXTERNAL"}
HARDWARE_LEVEL = {0: "LIMITED", 1: "FULL", 2: "LEGACY", 3: "LEVEL_3", 4: "EXTERNAL"}
TIMESTAMP_SOURCE = {0: "UNKNOWN", 1: "REALTIME"}
MIN_GYRO_RMS_RAD_S = 0.02     # ASSUMED: below this the phone was not moved enough to test OIS against the gyroscope
OIS_STILL_PX = 0.05           # ASSUMED: OIS position scatter below this counts as "not moving"


def _modes(v) -> list:
    return list(v) if isinstance(v, list) else []


def camera_capabilities(cam: dict) -> dict:
    """Decisions SIGHTLINE needs for one camera, each derived only from what the device reported."""
    ois, eis, ois_data = _modes(cam.get("available_ois_modes")), _modes(cam.get("available_video_stabilization_modes")), \
        _modes(cam.get("available_ois_data_modes"))
    keys = set(cam.get("available_result_keys") or [])
    phys, active = cam.get("sensor_physical_size_mm"), cam.get("active_array")
    focal = (cam.get("focal_lengths_mm") or [None])[0]
    f_px = None
    intr = cam.get("lens_intrinsic_calibration")
    if isinstance(intr, list) and len(intr) == 5 and intr[0]:
        f_px = {"value": float(intr[0]), "source": "LENS_INTRINSIC_CALIBRATION (device-reported)"}
    return {
        "camera_id": cam.get("camera_id"), "lens_facing": LENS_FACING.get(cam.get("lens_facing"), cam.get("lens_facing")),
        "hardware_level": HARDWARE_LEVEL.get(cam.get("hardware_level"), cam.get("hardware_level")),
        "focal_length_mm": focal, "sensor_physical_size": phys, "active_array": active,
        "pixel_array": cam.get("pixel_array"), "physical_camera_ids": cam.get("physical_camera_ids"),
        "ois_present": 1 in ois, "ois_off_listed": 0 in ois if ois else None,
        "ois_controllable": (0 in ois and 1 in ois),
        "eis_off_listed": 0 in eis if eis else None, "video_stabilization_modes": eis,
        "ois_samples_available": 1 in ois_data,
        "ois_samples_result_key": "android.statistics.oisSamples" in keys,
        "timestamp_source": TIMESTAMP_SOURCE.get(cam.get("timestamp_source"), cam.get("timestamp_source")),
        "rolling_shutter_skew_reported": "android.sensor.rollingShutterSkew" in keys,
        "per_frame_intrinsics_key": "android.lens.intrinsicCalibration" in keys,
        "intrinsic_calibration_static": intr, "f_px_reported": f_px,
        "lens_distortion": cam.get("lens_distortion"),
        "manual_exposure": 1 in _modes(cam.get("capabilities")),      # MANUAL_SENSOR capability
        "raw_capability": 3 in _modes(cam.get("capabilities")),
        "exposure_time_range_ns": cam.get("exposure_time_range_ns"),
        "focus_calibration": cam.get("focus_distance_calibration"),
        "min_focus_distance_diopters": cam.get("min_focus_distance_diopters"),
    }


def capabilities_report(probe: dict, category: str = "TEAM_COLLECTED") -> dict:
    problems = []
    if probe.get("kind") != "sightline_camera2_probe":
        problems.append("not a sightline_camera2_probe file")
    cams = [camera_capabilities(c) for c in probe.get("cameras", []) if "error" not in c]
    if not cams and not problems:
        problems.append("no camera could be described")
    back = [c for c in cams if c["lens_facing"] == "BACK"]
    verdict = {
        "any_back_camera_with_ois": any(c["ois_present"] for c in back),
        "back_cameras_without_ois": [c["camera_id"] for c in back if not c["ois_present"]],
        "ois_off_requestable_on": [c["camera_id"] for c in back if c["ois_controllable"]],
        "ois_samples_on": [c["camera_id"] for c in back if c["ois_samples_available"]],
        "realtime_timestamps_on": [c["camera_id"] for c in back if c["timestamp_source"] == "REALTIME"],
    }
    return {"experiment": EXPERIMENT_ID, "part": "capabilities", "created_utc": utc_now(),
            "git_commit": git_commit(Path(__file__).resolve().parents[2]), "device": probe.get("device"),
            "cameras": cams, "sensors": probe.get("sensors"), "verdict": verdict,
            "note": "Listed modes are what the device advertises. Whether OIS OFF is honoured, and whether OIS samples "
                    "are correct, is only shown by the OIS log (buttons 3 and 4 of the probe).",
            "status": result_status(category, not problems, "; ".join(problems) or None)}


def capabilities_markdown(rep: dict) -> str:
    d = rep.get("device") or {}
    lines = [f"# {EXPERIMENT_ID} — Camera2 capabilities: {d.get('manufacturer')} {d.get('model')} "
             f"(Android {d.get('android_release')}, API {d.get('sdk_int')})", "",
             f"Status: **{rep['status']['experiment_status']}** · evidence: **{rep['status']['evidence_class']}**. "
             "Scope: this device and build only.", ""]
    if rep["status"].get("banner"):
        lines += [f"**{rep['status']['banner']}**", ""]
    lines += ["| Camera | Facing | Level | Focal (mm) | OIS present | OIS OFF listed | EIS OFF listed | OIS samples "
              "| Timestamp source | Skew key | Intrinsics | Manual exposure |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    yn = lambda v: "—" if v is None else ("yes" if v else "no")
    for c in rep["cameras"]:
        lines.append(f"| {c['camera_id']} | {c['lens_facing']} | {c['hardware_level']} | {c['focal_length_mm']} | "
                     f"{yn(c['ois_present'])} | {yn(c['ois_off_listed'])} | {yn(c['eis_off_listed'])} | "
                     f"{yn(c['ois_samples_available'])} | {c['timestamp_source']} | {yn(c['rolling_shutter_skew_reported'])} | "
                     f"{'reported' if c['intrinsic_calibration_static'] else 'not reported'} | {yn(c['manual_exposure'])} |")
    for s in rep.get("sensors") or []:
        if s.get("present"):
            lines.append(f"\n* {s['type']}: {s.get('name')} ({s.get('vendor')}), maximum rate from minDelay "
                         f"{s.get('max_rate_hz_from_min_delay')} Hz, resolution {s.get('resolution')}")
    lines += ["", rep["note"], ""]
    return "\n".join(lines)


def ois_log_report(log: dict, category: str = "TEAM_COLLECTED") -> dict:
    """Checks on one OIS log: were samples delivered, do OIS / frame / gyro timestamps share a timebase, did OIS OFF
    stop the lens, and does the reported OIS shift follow the gyroscope (scale in px/rad and sign per axis)."""
    problems, findings = [], {}
    if log.get("kind") != "sightline_ois_log":
        problems.append("not a sightline_ois_log file")
    if log.get("error"):
        problems.append(f"recording reported an error: {log['error']}")
    frames = [f for f in log.get("frames", []) if f.get("sensor_timestamp_ns") is not None]
    gyro = np.array(log.get("gyro", []), dtype=float).reshape(-1, 4)
    if len(frames) < 30:
        problems.append(f"only {len(frames)} frames")
    if not problems:
        ts = np.array([f["sensor_timestamp_ns"] for f in frames], dtype=float) * 1e-9
        dt = np.diff(ts)
        findings["frames"] = {"n": len(frames), "rate_hz": float(1.0 / np.median(dt)),
                              "interval_jitter_s": float(dt.std()),
                              "dropped": int(np.sum(dt > 1.5 * np.median(dt))),
                              "ois_mode_reported": sorted({str(f.get("ois_mode")) for f in frames}),
                              "video_stabilization_reported": sorted({str(f.get("video_stabilization_mode")) for f in frames}),
                              "rolling_shutter_skew_ns": frames[0].get("rolling_shutter_skew_ns"),
                              "exposure_time_ns": frames[0].get("exposure_time_ns")}
        intr = [f.get("lens_intrinsic_calibration") for f in frames if isinstance(f.get("lens_intrinsic_calibration"), list)]
        if intr:
            pp = np.array([[i[2], i[3]] for i in intr], dtype=float)
            findings["per_frame_principal_point_std_px"] = pp.std(axis=0).tolist()
        samples = np.array([s for f in frames for s in (f.get("ois_samples") or [])], dtype=float).reshape(-1, 3)
        with_samples = sum(1 for f in frames if f.get("ois_samples"))
        findings["ois_samples"] = {"frames_with_samples": with_samples, "n": int(len(samples))}
        start, stop = log.get("start_elapsed_realtime_ns"), log.get("stop_elapsed_realtime_ns")
        tb = {"timestamp_source_reported": TIMESTAMP_SOURCE.get(log.get("timestamp_source"), log.get("timestamp_source"))}
        if start and stop:
            lo, hi = start * 1e-9 - 1.0, stop * 1e-9 + 1.0
            tb["frame_timestamps_in_elapsed_realtime_window"] = bool(ts.min() >= lo and ts.max() <= hi)
            if len(gyro):
                tb["gyro_timestamps_in_elapsed_realtime_window"] = bool(gyro[0, 0] * 1e-9 >= lo and gyro[-1, 0] * 1e-9 <= hi)
        if len(gyro) > 10:
            gt = gyro[:, 0] * 1e-9
            findings["gyro"] = {"n": int(len(gyro)), "rate_hz": float(1.0 / np.median(np.diff(gt))),
                                "rms_rad_s": float(np.sqrt((gyro[:, 1:] ** 2).sum(axis=1).mean()))}
        if len(samples) > 10:
            st = samples[:, 0] * 1e-9
            order = np.argsort(st)
            st, sxy = st[order], samples[order, 1:]
            keep = np.concatenate([[True], np.diff(st) > 0])
            st, sxy = st[keep], sxy[keep]
            sd = np.diff(st)
            findings["ois_samples"].update(rate_hz=float(1.0 / np.median(sd)), std_px=sxy.std(axis=0).tolist(),
                                           peak_to_peak_px=np.ptp(sxy, axis=0).tolist())
            tb["ois_timestamps_within_frame_span"] = bool(st.min() >= ts.min() - 0.5 and st.max() <= ts.max() + 0.5)
            moving = bool(max(findings["ois_samples"]["std_px"]) > OIS_STILL_PX)
            findings["ois_lens_moving"] = moving
            g = findings.get("gyro")
            if g and g["rms_rad_s"] >= MIN_GYRO_RMS_RAD_S and tb.get("ois_timestamps_within_frame_span"):
                gt = gyro[:, 0] * 1e-9
                rate = min(g["rate_hz"], findings["ois_samples"]["rate_hz"], 200.0)
                t0, t1 = max(gt[0], st[0]), min(gt[-1], st[-1])
                grid = np.arange(t0, t1, 1.0 / rate)
                if len(grid) > 4 * rate:
                    theta = integrate_rate(gt, gyro[:, 1:])
                    hi = min(20.0, 0.4 * rate)
                    th = _bandpass(np.column_stack([np.interp(grid, gt, theta[:, a]) for a in range(3)]), rate, 0.5, hi)
                    ois = _bandpass(np.column_stack([np.interp(grid, st, sxy[:, a]) for a in range(2)]), rate, 0.5, hi)
                    cut = len(grid) // 20
                    th, ois = th[cut:-cut], ois[cut:-cut]
                    coef, *_ = np.linalg.lstsq(th, ois, rcond=None)      # px per rad, (3 gyro axes) x (2 image axes)
                    resid = ois - th @ coef
                    r2 = 1.0 - float((resid**2).sum()) / float((ois**2).sum())
                    findings["ois_vs_gyro"] = {
                        "px_per_rad_matrix_rows_gyro_xyz_cols_ois_xy": coef.tolist(),
                        "px_per_rad_x": float(np.linalg.norm(coef[:, 0])), "px_per_rad_y": float(np.linalg.norm(coef[:, 1])),
                        "r2": r2, "band_hz": [0.5, hi],
                        "reading": "OIS shift follows the gyroscope" if r2 > 0.5 else "OIS shift not explained by the gyroscope"}
                    intr = log.get("lens_intrinsic_calibration_static")
                    if isinstance(intr, list) and len(intr) == 5 and intr[0]:
                        findings["ois_vs_gyro"]["f_px_reported"] = float(intr[0])
                        findings["ois_vs_gyro"]["compensation_fraction_x"] = findings["ois_vs_gyro"]["px_per_rad_x"] / float(intr[0])
                        findings["ois_vs_gyro"]["compensation_fraction_y"] = findings["ois_vs_gyro"]["px_per_rad_y"] / float(intr[1] or intr[0])
            elif g:
                findings["ois_vs_gyro"] = {"reading": "not evaluated: the phone was not moved enough, or timebases differ"}
        findings["timebase"] = tb
        req = (log.get("request") or {}).get("ois_requested")
        if req == "OFF" and "ois_lens_moving" in findings:
            findings["ois_off_honoured"] = not findings["ois_lens_moving"]
        elif req == "OFF":
            findings["ois_off_honoured"] = None      # no samples: cannot be judged from metadata
    return {"experiment": EXPERIMENT_ID, "part": "ois_log", "created_utc": utc_now(),
            "git_commit": git_commit(Path(__file__).resolve().parents[2]), "device": log.get("device"),
            "camera_id": log.get("camera_id"), "request": log.get("request"), "findings": findings,
            "status": result_status(category, not problems, "; ".join(problems) or None)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category", default="TEAM_COLLECTED", choices=("TEAM_COLLECTED", "SYNTHETIC"))
    ap.add_argument("--out", default=RESULTS_DIR)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capabilities")
    c.add_argument("probe")
    o = sub.add_parser("ois-log")
    o.add_argument("logs", nargs="+")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.cmd == "capabilities":
        rep = capabilities_report(json.loads(Path(args.probe).read_text()), args.category)
        rep["input"] = {"file": Path(args.probe).name, "sha256": sha256_file(args.probe)}
        (out / "capabilities.json").write_text(json.dumps(rep, indent=2) + "\n")
        (out / "capabilities.md").write_text(capabilities_markdown(rep))
        print(capabilities_markdown(rep))
        return 0 if rep["status"]["experiment_status"] == "COMPLETE" else 2
    code = 0
    for path in args.logs:
        rep = ois_log_report(json.loads(Path(path).read_text()), args.category)
        rep["input"] = {"file": Path(path).name, "sha256": sha256_file(path)}
        (out / f"ois_log_{Path(path).stem}.json").write_text(json.dumps(rep, indent=2) + "\n")
        print(json.dumps({"file": Path(path).name, "status": rep["status"], "findings": rep["findings"]}, indent=2))
        code = code or (0 if rep["status"]["experiment_status"] == "COMPLETE" else 2)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
