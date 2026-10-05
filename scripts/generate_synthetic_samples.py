"""Generate the small, versioned synthetic sample set with provenance manifest (category SYNTHETIC).

Run:  python scripts/generate_synthetic_samples.py --out data/synthetic/v0.1.0 --manifest data/manifests/synthetic_v0.1.0.jsonl

The set is small on purpose (it is committed to git as a reference/golden set). Large sets are generated on demand
from the same code and seeds and are not committed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calibration.camera import CameraModel  # noqa: E402
from ml.datasets.provenance import git_commit, make_record, sha256_file, write_jsonl  # noqa: E402
from ml.datasets.synthetic_target import (  # noqa: E402
    GENERATOR_NAME,
    GENERATOR_VERSION,
    Degradation,
    random_spec,
    render,
)

PRESETS = {
    "wide_1080p": CameraModel.from_hfov(1920, 1080, 67.0, k1=-0.05),
    "wide_2160p": CameraModel.from_hfov(3840, 2160, 67.0, k1=-0.05),
    "tele3x_1080p": CameraModel.from_hfov(1920, 1080, 25.0),
}
CONDITIONS = {
    "good_light": Degradation(),
    "dim_light": Degradation(electrons_per_unit=300.0, read_noise_e=3.0),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/synthetic/v0.1.0")
    ap.add_argument("--manifest", default="data/manifests/synthetic_v0.1.0.jsonl")
    ap.add_argument("--per-cell", type=int, default=2)
    ap.add_argument("--seed", type=int, default=20261005)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / args.out
    out.mkdir(parents=True, exist_ok=True)
    commit = git_commit(root)
    records = []
    rng = np.random.default_rng(args.seed)
    idx = 0

    def emit(sample, preset, condition, mode):
        nonlocal idx
        idx += 1
        sid = f"syn-v0.1.0-{idx:06d}"
        img_path = out / f"{sid}.png"
        cv2.imwrite(str(img_path), sample.image)
        gt_path = out / f"{sid}.json"
        gt_path.write_text(json.dumps({"sample_id": sid, "category": "SYNTHETIC",
                                       "ground_truth": sample.ground_truth, "parameters": sample.parameters},
                                      indent=2))
        files = [{"path": str(img_path.relative_to(root)), "sha256": sha256_file(img_path), "media_type": "image/png"},
                 {"path": str(gt_path.relative_to(root)), "sha256": sha256_file(gt_path),
                  "media_type": "application/json"}]
        records.append(make_record(
            sid, "SYNTHETIC",
            {"name": GENERATOR_NAME, "version": GENERATOR_VERSION, "git_commit": commit,
             "script": "scripts/generate_synthetic_samples.py", "master_seed": args.seed},
            files, {"preset": preset, "condition": condition, "mode": mode} | sample.parameters,
            ground_truth={"impact_xy_mm": sample.ground_truth["impact_xy_mm"],
                          "impact_score": sample.ground_truth["impact_score"]},
            notes="SIMULATED image — not a real measurement."))

    for preset, cam in PRESETS.items():
        for condition, deg in CONDITIONS.items():
            for _ in range(args.per_cell):
                emit(render(random_spec(rng, cam, deg), rng), preset, condition, "roi")
    cam = PRESETS["wide_1080p"]
    emit(render(random_spec(rng, cam, Degradation()), rng, mode="full"), "wide_1080p", "good_light", "full")
    write_jsonl(records, root / args.manifest)
    print(f"wrote {len(records)} samples to {out} and manifest {args.manifest}")


if __name__ == "__main__":
    main()
