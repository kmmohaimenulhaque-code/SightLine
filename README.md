# SIGHTLINE™

A **non-functional, smartphone-based training instrument** for ISSF 10 m air-pistol-style shooting. A phone on a
passive grip, a BLE trigger and a printed ISSF target at 10 m; computer vision scores dry-fire shots and will
quantify hold and trigger control. Nothing in SIGHTLINE launches, or can be adapted to launch, anything.

SIGHTLINE is not affiliated with AMD, NVIDIA, ISSF or any manufacturer, and is not an ISSF-approved scoring target.

## Status — v0.2.0 (2026-10-06): Mission 2 experimental validation — harnesses ready, physical data required

Project readiness ≈ **38 %** (planning estimate; see `ARCHITECTURE.md` §20).

* Mission 1: deterministic pipeline, synthetic generator, provenance, experiment E-001 (SIMULATED).
* Mission 2 research: report in the repository root. Principal risk: **iPhone "stabilisation Off" must not be assumed
  to disable the Main camera's sensor-shift OIS.**
* Mission 2 experimental validation (branch `mission-2-experimental-validation`): harnesses, protocols, a Camera2
  probe app and a printable target for E-004a, E-004b, E-002, E-003 and the gyroscope experiment. 142 tests pass.
* **No physical experiment has been run.** Every device experiment is PHYSICAL_DATA_REQUIRED
  (`docs/experiments/MISSION_2_EXPERIMENTAL_REPORT.md` says exactly what has to be done physically).
* E-005 (DERIVED / SIMULATED): Cramér–Rao bound on the impact 0.012–0.235 mm RMS in the synthetic model; the
  baseline is 1.5–3.1× above it. Under idealised assumptions, sub-pixel target localisation corresponds to a
  theoretical/derived spatial scale on the order of tenths of a millimetre at 10 m. Real-world accuracy remains
  experimentally unresolved.
* No mobile training app, hardware, sensor fusion or ML yet.

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
python -m pytest                 # 142 tests
python -m ml.evaluation.e001_localisation_budget --config ml/configs/e001.json --out ml/evaluation/results/E-001
python -m ml.evaluation.e005_localisation_limit          # Cramér–Rao bound (DERIVED / SIMULATED)
python -m ml.evaluation.e004a_ois_transfer expected      # planning table (DERIVED)
python -m ml.evaluation.e004a_ois_transfer synthetic-sanity   # harness check on simulated frames (several minutes)
python scripts/generate_synthetic_samples.py
```

Physical experiments (after recording, see `docs/experiments/`):

```bash
python -m ml.datasets.capture new --experiment E-004a --test B_step --video clip.mov   # then fill in and validate
python -m ml.evaluation.e004a_ois_transfer analyse --capture <manifest.json> --video clip.mov
python -m ml.evaluation.e002_static_capture analyse --capture <manifest.json> --video clip.mov
python -m ml.evaluation.e004b_android_probe capabilities sightline_probe_<model>.json
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
| `PROJECT_SPEC.md`, `REQUIREMENTS.md` | `EXPERIMENT_LOG.md` — register and every experiment |
| `docs/experiments/` — Mission 2 experimental report and physical protocols | Mission 2 research report (repository root) |
| `docs/science/` — geometry, scoring, error budget | `research/` — AMD audits, research log |
| `docs/calibration/`, `docs/computer-vision/`, `docs/ml/` | `docs/hardware/`, `docs/cad/` |
| `DATASET_SPEC.md`, `DATASETS.md` | `SOURCES_AND_LICENSES.md`, `THIRD_PARTY_CODE.md` |

## Repository map

`app/` reference implementation (scoring, calibration, vision, time-series analysis, gyroscope characterisation;
`mobile/android-probe/` measurement-only probe) · `ml/` synthetic data, provenance, capture manifests, experiments · `data/` manifests and the synthetic reference set · `tests/` · `scripts/` ·
`cad/`, `hardware/` (not started) · `docs/`, `research/`.

## Licence

Planned: Apache-2.0 for the software (owner's stated intent, ARCHITECTURE.md D-013); CAD and datasets to be licensed
separately. No `LICENSE` file has been added yet — until it is, all rights reserved. Dependencies: NumPy (BSD-style), OpenCV
(Apache-2.0); no third-party source code is incorporated.
