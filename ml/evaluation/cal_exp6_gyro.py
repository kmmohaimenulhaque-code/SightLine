"""Experiment CAL-EXP-6 — raw gyroscope characterisation (sampling, timing, bias, noise, Allan deviation, axes).
Protocol: docs/experiments/CAL-EXP-6_GYRO_PROTOCOL.md. Deterministic; no Kalman filter, no fusion, no learning.

    python -m ml.evaluation.cal_exp6_gyro --manifest <gyro manifest.json> --log <Gyroscope.csv>

The manifest is a provenance record (category TEAM_COLLECTED) whose ``parameters`` hold: experiment "CAL-EXP-6",
capture_id, device, os_version, app, kind ("static" or "axis:<physical rotation, e.g. +pitch (lens end up)>"),
placement, requested_rate_hz, rate_unit, and optional time_unit / columns / temperature_column.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.imu.gyro import allan_deviation, allan_summary, dominant_axis, load_gyro_csv, sampling_report, static_report
from ml.datasets.provenance import git_commit, sha256_file, utc_now, validate_record
from ml.evaluation.status import result_status

EXPERIMENT_ID = "CAL-EXP-6"
REQUIRED = ("experiment", "capture_id", "device", "os_version", "app", "kind", "placement", "requested_rate_hz", "rate_unit")
ALLAN_MIN_DURATION_S = 600.0     # ASSUMED: below this the Allan curve cannot show a bias-instability floor


def analyse(record: dict, log_path: str | Path, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = record["parameters"]
    problems = validate_record(record) + [f"'{k}' is not filled in" for k in REQUIRED if p.get(k) is None]
    if not problems and sha256_file(log_path) not in [f["sha256"] for f in record["files"]]:
        problems.append("sha256 of the log is not in the manifest")
    summary = {"experiment": EXPERIMENT_ID, "capture_id": p.get("capture_id"), "created_utc": utc_now(),
               "git_commit": git_commit(Path(__file__).resolve().parents[2]),
               "scope": {k: p.get(k) for k in ("device", "os_version", "app", "placement", "requested_rate_hz")},
               "kind": p.get("kind"), "warnings": []}
    if not problems:
        try:
            cols = p.get("columns") or {}
            log = load_gyro_csv(log_path, cols.get("time"), cols.get("x"), cols.get("y"), cols.get("z"),
                                p.get("time_unit"), p["rate_unit"], p.get("temperature_column"))
            summary["columns_used"] = log.columns
            summary["sampling"] = samp = sampling_report(log.t)
            if str(p["kind"]).startswith("axis"):
                summary["axis"] = dominant_axis(log.omega) | {"physical_rotation": p["kind"]}
            else:
                summary["static"] = static_report(log)
                allan = {}
                with open(out / "allan.csv", "w", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["axis", "tau_s", "allan_deviation_rad_s"])
                    for k, name in enumerate("xyz"):
                        taus, adev = allan_deviation(log.omega[:, k], samp["rate_median_hz"])
                        w.writerows([name, f"{a:.6g}", f"{b:.6g}"] for a, b in zip(taus, adev))
                        allan[name] = allan_summary(taus, adev)
                summary["allan"] = allan
                if samp["duration_s"] < ALLAN_MIN_DURATION_S:
                    summary["warnings"].append(f"record is {samp['duration_s']:.0f} s: too short for a bias-instability "
                                               f"estimate (use >= {ALLAN_MIN_DURATION_S:.0f} s, ideally 1 h)")
            if samp["gaps"]:
                summary["warnings"].append(f"{samp['gaps']} gaps in the sample stream")
        except ValueError as exc:
            problems.append(f"analysis failed: {exc}")
    summary["status"] = result_status(record.get("category", "SYNTHETIC"), not problems, "; ".join(problems) or None)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    rec = json.loads(Path(args.manifest).read_text())
    out = args.out or f"ml/evaluation/results/CAL-EXP-6/{rec.get('sample_id')}"
    s = analyse(rec, args.log, out)
    print(json.dumps(s["status"], indent=2))
    print(f"results in {out}")
    return 0 if s["status"]["experiment_status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
