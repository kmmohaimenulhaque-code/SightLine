"""Capture manifests for physical recordings (Mission 2 experimental brief §12, §21; DATASET_SPEC.md §2 and §4).

A capture manifest is an ordinary provenance record (``ml/datasets/provenance.py``) of category TEAM_COLLECTED whose
``parameters`` carry the capture metadata below. One JSON file per clip in ``data/manifests/captures/``. The video
itself is not committed: the manifest holds its file name and sha256.

Fields the operator could not determine are written as the string "UNKNOWN" (allowed only where listed in
``MAY_BE_UNKNOWN``). ``null`` means "not filled in yet" and never passes validation — a template is not a record.

CLI:
    python -m ml.datasets.capture new --experiment E-004a --video clip.mov --out data/manifests/captures/
    python -m ml.datasets.capture validate data/manifests/captures/<capture_id>.json [--video clip.mov]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from app.vision.video import HDR_TRANSFERS, probe_video
from ml.datasets.provenance import make_record, sha256_file, utc_now, validate_record

PROCESSING_VERSION = "capture-manifest/1"

# name -> meaning. All must be present and non-null.
CAPTURE_FIELDS = {
    "capture_id": "unique id, e.g. team-20261010-e004a-main-01",
    "experiment": "experiment id (E-002, E-004a, E-004b, CAL-EXP-6)",
    "test": "E-004a: A_static | B_step | C_ramp | D_oscillation; E-002: static; otherwise a short label",
    "operator": "who recorded it (initials are enough; no personal data beyond that)",
    "captured_local": "local date and time of the recording, ISO-8601",
    "device": "exact model, e.g. iPhone 15 (A3090)",
    "os_version": "e.g. iOS 26.0.1",
    "camera": "main_1x | main_2x | ultra_wide | front | Android camera id",
    "zoom_readout": "for 2x: crop | sensor_readout | digital | UNKNOWN (do not assume a separate optical camera)",
    "capture_app": "app name and version",
    "resolution": "[width, height] as recorded",
    "fps": "nominal frame rate selected",
    "codec": "hevc | h264 | ...",
    "file_format": "container, e.g. mov",
    "stabilisation_mode": "the app's setting, verbatim (e.g. Off)",
    "hdr": "off | on | UNKNOWN",
    "focus": "locked/auto and the lens position value shown by the app",
    "exposure": "shutter time in seconds, or 'auto'",
    "iso": "ISO value, or 'auto'",
    "white_balance": "locked value, or 'auto'",
    "lighting": "description, plus lux at the target if measured",
    "orientation": "landscape_left | landscape_right | portrait | ...",
    "distance_mm": "{value, sigma}: camera to target face, measured",
    "target": "{print_id, black_diameter_mm {value, sigma} MEASURED, card_mm [w, h], printer, paper}",
    "physical_setup": "free text: mount, tripod/jig, what was rigidly fixed to what",
}
MAY_BE_UNKNOWN = ("os_version", "zoom_readout", "hdr", "focus", "exposure", "iso", "white_balance", "codec",
                  "capture_app", "operator")
E004A_TESTS = ("A_static", "B_step", "C_ramp", "D_oscillation")

# Extra blocks required for specific E-004a tests (documented in docs/experiments/E-004A_PROTOCOL.md).
JIG_TEMPLATE = {
    "mechanism": None,                       # e.g. "board on two rods, paper shims under the front rod"
    "radius_mm": {"value": None, "sigma": None},          # pivot line to displacement line
    "pivot_ahead_mm": {"value": None, "sigma": None},     # camera lens ahead (+) / behind (-) of the pivot line
    "plateaus": [{"displacement_mm": {"value": 0.0, "sigma": 0.0}, "note": "baseline"}],
}
GYRO_TEMPLATE = {"file": None, "sha256": None, "device": None, "app": None, "rate_unit": "rad/s", "time_unit": None,
                 "columns": {"time": None, "x": None, "y": None, "z": None},
                 "rigidly_fixed_to_camera": None}


def _measured_ok(m) -> bool:
    return (isinstance(m, dict) and isinstance(m.get("value"), (int, float)) and isinstance(m.get("sigma"), (int, float))
            and math.isfinite(m["value"]) and math.isfinite(m["sigma"]) and m["sigma"] >= 0)


def validate_capture(record: dict) -> list[str]:
    """Return a list of problems (empty = valid). Checks the provenance record, then the capture metadata."""
    errors = validate_record(record)
    if errors:
        return errors
    if record["category"] != "TEAM_COLLECTED":
        errors.append("a physical capture must have category TEAM_COLLECTED")
    p = record["parameters"]
    for name in CAPTURE_FIELDS:
        v = p.get(name)
        if v is None:
            errors.append(f"'{name}' is not filled in")
        elif v == "UNKNOWN" and name not in MAY_BE_UNKNOWN:
            errors.append(f"'{name}' may not be UNKNOWN")
    if errors:
        return errors
    if not _measured_ok(p["distance_mm"]) or p["distance_mm"]["value"] <= 0:
        errors.append("distance_mm needs a positive measured value and a sigma")
    tgt = p["target"]
    if not isinstance(tgt, dict) or not _measured_ok(tgt.get("black_diameter_mm")) or tgt["black_diameter_mm"]["value"] <= 0:
        errors.append("target.black_diameter_mm must be the MEASURED diameter with a sigma (do not enter the nominal 59.5)")
    elif tgt["black_diameter_mm"]["sigma"] == 0:
        errors.append("target.black_diameter_mm.sigma is 0: a ruler or caliper reading has an uncertainty")
    if not (isinstance(p["resolution"], list) and len(p["resolution"]) == 2):
        errors.append("resolution must be [width, height]")
    if p["experiment"] == "E-004a":
        if p["test"] not in E004A_TESTS:
            errors.append(f"E-004a test must be one of {E004A_TESTS}")
        if p["test"] in ("B_step", "C_ramp"):
            jig = p.get("jig")
            if not isinstance(jig, dict) or not _measured_ok(jig.get("radius_mm")) or not _measured_ok(jig.get("pivot_ahead_mm")):
                errors.append("B_step/C_ramp need jig.radius_mm and jig.pivot_ahead_mm as {value, sigma}")
            elif jig["radius_mm"]["sigma"] == 0:
                errors.append("jig.radius_mm.sigma is 0: state the measurement uncertainty")
            plats = (jig or {}).get("plateaus") if isinstance(jig, dict) else None
            if not isinstance(plats, list) or len(plats) < 2 or not all(_measured_ok(q.get("displacement_mm")) for q in plats):
                errors.append("jig.plateaus needs a baseline and at least one step, each with displacement_mm {value, sigma}")
        if p["test"] == "D_oscillation":
            g = p.get("gyro_log")
            if not isinstance(g, dict) or not g.get("file") or not re.fullmatch(r"[0-9a-f]{64}", str(g.get("sha256", ""))):
                errors.append("D_oscillation needs gyro_log.file and gyro_log.sha256 (an independent angular reference)")
            elif g.get("rigidly_fixed_to_camera") is not True:
                errors.append("gyro_log.rigidly_fixed_to_camera must be true (same rigid body as the camera)")
    return errors


def check_against_video(record: dict, video_path: str | Path) -> tuple[list[str], list[str]]:
    """Compare the manifest with the actual file. Returns ``(errors, warnings)``. A checksum mismatch or an HDR
    transfer function is an error (wrong file / protocol violated); metadata differences are warnings."""
    errors, warnings = [], []
    p = record["parameters"]
    digest = sha256_file(video_path)
    listed = [f["sha256"] for f in record["files"]]
    if digest not in listed:
        errors.append(f"sha256 of {Path(video_path).name} ({digest[:12]}...) is not in the manifest")
    meta = probe_video(video_path)
    if meta["color_transfer"] in HDR_TRANSFERS:
        errors.append(f"video is HDR ({meta['color_transfer']}); the protocol requires HDR off")
    if meta["width"] and meta["height"] and sorted([meta["width"], meta["height"]]) != sorted(p["resolution"]):
        warnings.append(f"manifest resolution {p['resolution']} but file is {meta['width']}x{meta['height']}")
    if meta["fps_avg"] and isinstance(p["fps"], (int, float)) and abs(meta["fps_avg"] - p["fps"]) > 0.02 * p["fps"]:
        warnings.append(f"manifest fps {p['fps']} but file averages {meta['fps_avg']:.3f}")
    if meta["codec"] and p["codec"] not in ("UNKNOWN", meta["codec"]):
        warnings.append(f"manifest codec {p['codec']} but file is {meta['codec']}")
    return errors, warnings


def new_capture_template(experiment: str, video_path: str | Path | None = None, test: str | None = None) -> dict:
    """A manifest with everything the file can tell us filled in and everything else ``null`` for the operator."""
    params = {k: None for k in CAPTURE_FIELDS}
    params.update(experiment=experiment, test=test, processing_version=PROCESSING_VERSION,
                  distance_mm={"value": None, "sigma": None},
                  target={"print_id": None, "black_diameter_mm": {"value": None, "sigma": None},
                          "card_mm": [None, None], "printer": None, "paper": None})
    files = [{"path": "FILL_IN", "sha256": "0" * 64, "media_type": "video/quicktime"}]
    if video_path is not None:
        meta = probe_video(video_path)
        params.update(resolution=[meta["width"], meta["height"]], codec=meta["codec"],
                      file_format=Path(video_path).suffix.lstrip(".").lower() or None,
                      fps=round(meta["fps_avg"], 3) if meta["fps_avg"] else None,
                      container_metadata={k: meta[k] for k in ("fps_avg", "fps_nominal", "n_frames", "duration_s",
                                                               "rotation_deg", "pix_fmt", "color_transfer", "bit_rate",
                                                               "creation_time", "tags", "source")})
        if meta["color_transfer"] in HDR_TRANSFERS:
            params["hdr"] = "on"
        files = [{"path": Path(video_path).name, "sha256": sha256_file(video_path), "media_type": "video/*"}]
    if experiment == "E-004a" and test in ("B_step", "C_ramp"):
        params["jig"] = json.loads(json.dumps(JIG_TEMPLATE))
    if experiment == "E-004a" and test == "D_oscillation":
        params["gyro_log"] = json.loads(json.dumps(GYRO_TEMPLATE))
    return {"sample_id": None, "category": "TEAM_COLLECTED", "created_utc": utc_now(),
            "source": {"session": None, "note": "capture manifest; raw video is not committed (sha256 only)"},
            "files": files, "licence": "SIGHTLINE-internal", "parents": [], "parameters": params,
            "notes": "TEMPLATE - replace every null. Use \"UNKNOWN\" only where the value truly cannot be determined."}


def finalise(template: dict) -> dict:
    """Turn a filled-in template into a validated record (sample_id = capture_id). Raises ValueError if invalid."""
    rec = dict(template)
    rec["sample_id"] = rec["parameters"].get("capture_id")
    if not rec["sample_id"]:
        raise ValueError("'capture_id' is not filled in")
    if not isinstance(rec.get("source", {}).get("session"), str):
        rec["source"] = dict(rec.get("source") or {}, session=str(rec["parameters"].get("captured_local")))
    if str(rec.get("notes", "")).startswith("TEMPLATE"):
        rec.pop("notes")
    errors = validate_capture(rec)
    if errors:
        raise ValueError("; ".join(errors))
    return make_record(rec["sample_id"], rec["category"], rec["source"], rec["files"], rec["parameters"],
                       rec["licence"], rec["parents"], rec.get("ground_truth"), rec.get("notes"), rec["created_utc"])


def load_capture(path: str | Path) -> dict:
    """Load and validate a capture manifest. Raises ValueError listing every problem."""
    return finalise(json.loads(Path(path).read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create or validate capture manifests.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="write a template pre-filled from the video file")
    n.add_argument("--experiment", required=True)
    n.add_argument("--test", default=None)
    n.add_argument("--video", default=None)
    n.add_argument("--out", default="data/manifests/captures")
    v = sub.add_parser("validate", help="validate a filled-in manifest (and optionally its video)")
    v.add_argument("manifest")
    v.add_argument("--video", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "new":
        tpl = new_capture_template(args.experiment, args.video, args.test)
        stem = Path(args.video).stem if args.video else "capture"
        out = Path(args.out) / f"TEMPLATE_{args.experiment}_{stem}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(tpl, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out} - fill in every null, set capture_id, then run: validate {out}")
        return 0
    try:
        rec = load_capture(args.manifest)
    except ValueError as exc:
        print("INVALID:\n  " + "\n  ".join(str(exc).split("; ")))
        return 1
    if args.video:
        errors, warnings = check_against_video(rec, args.video)
        for w in warnings:
            print("warning:", w)
        if errors:
            print("INVALID:\n  " + "\n  ".join(errors))
            return 1
    print(f"OK: {rec['sample_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
