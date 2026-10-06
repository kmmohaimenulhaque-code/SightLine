# Dataset Specification

Implementation: `ml/datasets/provenance.py` (records and validation), `ml/datasets/synthetic_target.py` (generator),
`data/manifests/schema/sample_record.schema.json` (schema document).

## 1. Data categories (never mixed without provenance)

| Category | Meaning | Location | Rules |
|---|---|---|---|
| `EXTERNAL` | Third-party data | `data/raw/external/<dataset>/` | Licence recorded and verified first (`DATASETS.md` §3) |
| `TEAM_COLLECTED` | Captured by the SIGHTLINE team | `data/raw/team/<session>/` | Immutable once added; capture metadata mandatory (§4) |
| `SYNTHETIC` | Generated with known ground truth | `data/synthetic/<version>/` | Generator name, version, git commit, seed and all parameters recorded; **never presented as real measurement** |
| `DERIVED` | Transformed from other samples | `data/interim/`, `data/processed/` | `parents` lists every source sample id |
| `MODEL_OUTPUT` | Produced by an ML model | alongside the experiment | Model id/version recorded |
| `SIMULATION_OUTPUT` | Outputs of simulations (e.g. computed trajectories) | alongside the experiment | Simulator + parameters recorded |

## 2. Sample record (one JSON object per line in `data/manifests/*.jsonl`)

| Field | Required | Meaning |
|---|---|---|
| `sample_id` | yes | Unique, stable id (`syn-v0-000001`, `team-20261020-a-000123`) |
| `category` | yes | One of the six categories above |
| `created_utc` | yes | ISO-8601 UTC timestamp |
| `source` | yes | Generator `{name, version, git_commit}` or device/capture session, or external dataset reference |
| `files` | yes | List of `{path, sha256, media_type}` |
| `licence` | yes | Licence of the sample (`"SIGHTLINE-internal"` for team and synthetic data until D-013 is decided) |
| `parents` | yes | List of parent sample ids (empty for originals) |
| `parameters` | yes | Everything needed to regenerate or interpret the sample (camera, pose, degradation, capture settings) |
| `ground_truth` | no | Ground-truth geometry when known (synthetic, or reference-rig captures) |
| `notes` | no | Free text |

### 2a. Capture manifests for physical recordings (implemented 2026-10-06)

One JSON file per clip in `data/manifests/captures/`, validated by `ml/datasets/capture.py`. It is a sample record of
category `TEAM_COLLECTED` whose `parameters` must contain: capture id, experiment, test, operator, local time,
device, OS version, camera, zoom readout, capture app, resolution, frame rate, codec, file format, stabilisation
mode, HDR state, focus, exposure, ISO, white balance, lighting, orientation, distance `{value, sigma}`, target
(print id, **measured** black diameter `{value, sigma}`, card size, printer, paper), physical setup and processing
version; the file checksum sits in `files`. E-004a adds the jig geometry (steps) or the gyroscope log (oscillation).
`null` never validates; `"UNKNOWN"` is accepted only for fields that genuinely cannot always be known. Raw video,
stills and sensor logs are not committed — manifests and checksums are (`.gitignore`).

Provenance classes are the six categories of §1. The evidence class of any result is derived from them
(`ml/evaluation/status.py`): only `TEAM_COLLECTED` can be EXPERIMENTAL.

## 3. Synthetic sample content (implemented, generator v0.1.1 — output bit-identical to v0.1.0)

* **Image:** 8-bit grayscale, gamma-encoded (power 1/2.2), optionally JPEG-compressed; either the full frame or a
  region of interest (ROI) around the target with its origin recorded.
* **Ground truth:** projected target centre (px), bore pixel (px) = simulated sight position, simulated impact
  (target mm) and its ISSF score, local mm-per-pixel scale, ellipse parameters of every ring and the black edge in
  image coordinates, ROI origin.
* **Parameters:** camera (size, fx, fy, cx, cy, k1, k2), pose (distance, yaw, pitch, roll), appearance
  (reflectances, ring-line thickness, card size), degradation (PSF σ, motion blur length/angle, electrons per unit
  reflectance, read noise, ADC bits, gamma, JPEG quality), seed.

## 4. Team-collected capture protocol (to be executed — Phase 4/5)

First executions are specified step by step in `docs/experiments/` (E-004a, E-004b, E-002/E-003, CAL-EXP-6); the
general plan below remains the target for the full dataset.

**Devices:** ≥ 3 phone models (≥ 1 Android passing CAL-EXP-1, ≥ 1 iPhone), every usable camera (wide, tele) and
mode (1080p/2160p video, still).

**Scene variables:** illuminance at the target (measured with a lux meter: ~100, ~300, ~1000 lx), backgrounds
(plain wall, cluttered), target distance 9.5 / 10.0 / 10.5 m (measured with a tape or laser meter), target tilt
(0°, ±10°), print type (laser, inkjet, two print-scale settings, measured), partial occlusion (hand, object).

**Motion conditions:**
1. Tripod, static — localisation noise floor.
2. Tripod + rotation stage or micrometer tilt table — commanded angular steps = **ground-truth motion**.
3. Hand-held hold with the grip — robustness and real hold statistics (no sub-mm ground truth).

**Metadata per clip:** device, OS, camera id, resolution, fps, exposure time, ISO/gain, focus mode/distance,
OIS/EIS state, timestamp source, per-frame timestamps, IMU log, BLE trigger log, lux, distance, print id, operator.

**Privacy:** do not capture people; if a person appears, obtain consent or discard; strip location metadata.

## 5. Splits

Split by **device model and session**, never by frame (adjacent frames are near-duplicates). Keep one device model
entirely held out. Synthetic test sets use seeds disjoint from development seeds.
