# data/synthetic

Category **SYNTHETIC** — generated images with exact ground truth. Never present these as real measurements.

* `v0.1.0/` — small reference set (13 samples) produced by `scripts/generate_synthetic_samples.py` with master seed
  20261005: 3 camera presets × 2 light conditions × 2 ROI samples, plus 1 full 1080p frame. Each `<id>.png` has a
  `<id>.json` with full ground truth and parameters. Manifest: `data/manifests/synthetic_v0.1.0.jsonl`.
* PNG is only the container; the simulated pipeline already applied 10-bit quantisation, gamma 2.2 and JPEG (quality 90)
  compression where the parameters say so.
* Larger sets (e.g. for E-001) are regenerated on demand from code + seeds and are not committed.
