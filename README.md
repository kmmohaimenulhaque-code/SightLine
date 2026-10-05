# SIGHTLINE™

A **non-functional, smartphone-based training instrument** for ISSF 10 m air-pistol-style shooting. A phone on a
passive grip, a BLE trigger and a printed ISSF target at 10 m; computer vision scores dry-fire shots and will
quantify hold and trigger control. Nothing in SIGHTLINE launches, or can be adapted to launch, anything.

SIGHTLINE is not affiliated with AMD, NVIDIA, ISSF or any manufacturer, and is not an ISSF-approved scoring target.

## Status — v0.1.0 (2026-10-05): research foundation + deterministic baseline

Project readiness ≈ **35 %** (planning estimate; see `ARCHITECTURE.md` §20).

* Phases 1–2 (reconnaissance, foundation): done, with listed open items.
* Phase 3–4 (baseline, data): deterministic pipeline, synthetic generator and provenance implemented; 71 tests pass.
* Experiment E-001 (SIMULATED): single-frame impact error p95 0.07–0.23 mm in good light across four camera modes
  (EST-grade target 0.4 mm); 1080p in dim light fails (0.61 mm).
* No real-device data, mobile app, hardware or ML yet.

## Findings that changed the design

1. **The concept's "0.891° black bull" is the outer 1-ring.** The black subtends 0.341° at 10 m.
2. **The concept's "≈0.2 cm pellet drop" is wrong by ~10×** (≈1.9 cm at ~160 m/s) and irrelevant anyway: sights are
   zeroed at 10 m. No drop term is simulated.
3. **Rings cannot be detected at 10 m** — the lines are a few hundredths of a pixel wide. SIGHTLINE measures the
   black aiming mark as a whole and renders the rings from the ISSF geometry.
4. **Scoring needs no camera calibration.** The target subtends < 1°, so the printed black is a local ruler.
5. **A screen-based sight cannot train sight alignment** — the eye's position does not affect where the camera points.
6. **Phone image stabilisation is the biggest threat**: OIS/EIS cancel exactly the motion SIGHTLINE measures.
7. **AMD-NR/OptiScaler and FidelityFX/FSR offer no reusable code** for this problem; their multi-frame *principles* do.

## Quick start

```bash
pip install -e ".[dev]"          # numpy, opencv-python-headless, pytest
python -m pytest                 # 71 tests
python -m ml.evaluation.e001_localisation_budget --config ml/configs/e001.json --out ml/evaluation/results/E-001
python scripts/generate_synthetic_samples.py
```

Minimal use:

```python
import json, cv2
from app.vision import measure_shot

sid = "data/synthetic/v0.1.0/syn-v0.1.0-000009"          # a SYNTHETIC reference sample
img = cv2.imread(sid + ".png", cv2.IMREAD_GRAYSCALE)
gt = json.load(open(sid + ".json"))["ground_truth"]
bore = (gt["bore_px"][0] - gt["canvas_origin_px"][0], gt["bore_px"][1] - gt["canvas_origin_px"][1])
shot = measure_shot(img, bore, up_direction_px=gt["up_direction_px"])
print(shot.score.decimal, shot.impact_xy_mm)             # 9.2 [-14.106 2.662]  (ground truth: 9.2, [-14.126, 2.662])
```

## Where to read

| Start here | Then |
|---|---|
| `ARCHITECTURE.md` — memory of the project, decision log, progress | `VALIDATION.md` — every claim and its evidence status |
| `PROJECT_SPEC.md`, `REQUIREMENTS.md` | `EXPERIMENT_LOG.md` — E-001 |
| `docs/science/` — geometry, scoring, error budget | `research/` — AMD audits, research log |
| `docs/calibration/`, `docs/computer-vision/`, `docs/ml/` | `docs/hardware/`, `docs/cad/` |
| `DATASET_SPEC.md`, `DATASETS.md` | `SOURCES_AND_LICENSES.md`, `THIRD_PARTY_CODE.md` |

## Repository map

`app/` reference implementation (scoring, calibration, vision; `mobile/` and `analytics/` not started) · `ml/`
synthetic data, provenance, experiments · `data/` manifests and the synthetic reference set · `tests/` · `scripts/` ·
`cad/`, `hardware/` (not started) · `docs/`, `research/`.

## Licence

Undecided (ARCHITECTURE.md D-013). Until decided, all rights reserved. Dependencies: NumPy (BSD-style), OpenCV
(Apache-2.0); no third-party source code is incorporated.
