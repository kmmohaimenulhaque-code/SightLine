# Requirements

Status: **DT** = DESIGN TARGET (a goal we chose), **V** = verified external constraint, **OPEN** = undecided.
"Verification" says how the requirement will be shown to be met. Requirement ids are stable; never reuse an id.

## Safety and scope (SAF)

| ID | Requirement | Status | Verification |
|---|---|---|---|
| SAF-01 | No part of SIGHTLINE may store energy to propel, or be adaptable to propel, any projectile. The trigger is a switch that reports events. | DT (non-negotiable) | Design review of every hardware revision |
| SAF-02 | The grip must not look like a realistic firearm (colour, no barrel/muzzle features, "TRAINING INSTRUMENT — NOT A FIREARM" marking). | DT | Design review; legal check per country (OPEN) |
| SAF-03 | User-facing material states what is and is not trained (sight alignment is not, D-011). | DT | Content review |

## Measurement (MEA) — evaluated on synthetic data first (SIMULATED), then real data

| ID | Requirement | Status | Verification |
|---|---|---|---|
| MEA-01 | Image-term impact error p95 ≤ 0.4 mm at the target ("EST-grade": half a decimal ring, from ISSF GTR 6.3.2.2) in supported camera modes under good light | DT | E-001 and successors |
| MEA-02 | Integer-score agreement with ground truth ≥ 99 % in supported modes | DT | E-001 |
| MEA-03 | Systematic impact bias ≤ 0.1 mm in each axis | DT | E-001 (mean error vector) |
| MEA-04 | Aiming-mark detection rate ≥ 99.5 % on frames where the full card is visible | DT | E-001; team-collected data |
| MEA-05 | Total shot error budget (image + timing + stabilisation) p95 ≤ 1.0 mm for a steady hold | DT | Reference-rig experiments (Phase 5) |

## Functional (FUN)

| ID | Requirement | Status | Verification |
|---|---|---|---|
| FUN-01 | Score each shot with ISSF ring geometry (GTR 6.3.4.6), decimal and integer, plus inner ten | V (geometry) / DT | `tests/test_scoring.py` |
| FUN-02 | Rings are rendered from the ISSF specification anchored on the detected black; they are never claimed to be detected | DT | Code review; D-004 |
| FUN-03 | Simulated impact = intersection of the bore ray through p_b with the target plane; no ballistic drop term | DT | `tests/test_geometry.py`, `tests/test_rectify.py`; D-005 |
| FUN-04 | Front-sight overlay drawn at S(p_b) with error < 0.5 screen px | DT | Device test |
| FUN-05 | Shot direction (high/low/left/right) corrected for phone roll using gravity | DT | Device test (D-015) |

## Camera and timing (CAM, TIM)

| ID | Requirement | Status | Verification |
|---|---|---|---|
| CAM-01 | EIS disabled; OIS disabled or compensated with per-frame OIS samples; devices failing CAL-EXP-1 are unsupported | DT | CAL-EXP-1 per device |
| CAM-02 | Focus locked near infinity; exposure and gain locked during a shot sequence | DT | Capture logs |
| CAM-03 | Exposure time short enough that hold-motion blur stays < 0.5 px (≤ 1/60 s as a starting assumption) | DT (value ASSUMPTION) | Blur budget in E-001 successors |
| TIM-01 | Trigger-to-frame-time alignment uncertainty ≤ 5 ms (1σ) | DT | EXP-HW-1 |
| TIM-02 | Frame timestamps refer to mid-exposure of the target's rows (rolling-shutter corrected) | DT | CAL-EXP-2 |

## Calibration (CAL)

| ID | Requirement | Status | Verification |
|---|---|---|---|
| CAL-01 | Scoring must not depend on intrinsic calibration (target-anchored rectification) | DT | `tests/test_rectify.py` with distortion and unknown focal length |
| CAL-02 | Per-device profile stored with the schema in `docs/calibration/CALIBRATION_STRATEGY.md` §3 | DT | Profile validator (Phase 6) |
| CAL-03 | Gyro–camera self-calibration available for angular metrics | DT | CAL-EXP-2 |
| CAL-04 | Print scale checked; prints outside 59.5 ± 0.5 mm black diameter are flagged | V (tolerance) / DT | Protocol |

## Data and governance (DAT, GOV)

| ID | Requirement | Status | Verification |
|---|---|---|---|
| DAT-01 | Every sample has a manifest record with category, source, hashes, licence, parents, parameters | DT | `tests/test_provenance.py` |
| DAT-02 | Synthetic data is labelled SYNTHETIC wherever it appears and never reported as real measurement | DT | Review; manifest category |
| GOV-01 | No third-party code without a verified compatible licence recorded in THIRD_PARTY_CODE.md | DT | Review |
| GOV-02 | Every important claim is classified in VALIDATION.md | DT | Review |

## Mobile (MOB) — Phase 6

| ID | Requirement | Status | Verification |
|---|---|---|---|
| MOB-01 | On-device processing; no cloud dependency for scoring | DT | Architecture review |
| MOB-02 | Per-frame tracking latency ≤ 1 frame period at 60 fps on a mid-range reference phone | DT (value ASSUMPTION) | Device benchmark |
| MOB-03 | Measurement core reproduces Python golden outputs within 0.01 px / 0.01 mm | DT | Golden-file tests |

## Analytics (ANA) — Phase 8

| ID | Requirement | Status | Verification |
|---|---|---|---|
| ANA-01 | Deterministic hold/trigger metrics (time-in-zone, trace speed in the final 1 s and 250 ms, pre/post-trigger displacement, grouping) | DT | Reference-rig motion |
| ANA-02 | No AI coaching until metrics are validated and data supports it | DT | Gate review |

## Mechanical CAD (CAD) — Mission 3 G0

| ID | Requirement | Status | Verification |
|---|---|---|---|
| CAD-01 | One common passive chassis/grip shall accept replaceable phone-adapter modules without redesigning the shared grip for each supported profile | DT | Source review; regenerate iPhone and dimensionally different placeholder configurations |
| CAD-02 | Each phone profile shall identify body/case dimensions, mass evidence, camera/clearance evidence, adapter ID, phone-to-chassis transform and calibration metadata, with unknowns explicit | DT | JSON profile review and configuration tests |
| CAD-03 | Phone retainers shall preload hard datums and shall not use uncontrolled friction or soft-pad compression as the only positioning method | DT | Geometry review; physical fit/reseat test at G0 |
| CAD-04 | Ballast shall be captive, lockable and position-searchable in longitudinal X and vertical Z; loose hand-placed weights are not an accepted adjustment | DT | CAD capture checks; slider/lock physical test |
| CAD-05 | The mass-property calculator shall report total mass, weighted COM, transformed inertia where supplied, attainable ranges, feasible/infeasible targets and evidence provenance | DT | `tests/test_cad_mass_properties.py`; generated example reports |
| CAD-06 | Mechanical pose repeatability and observed optical repeatability shall be recorded as separate metrics; CAD shall not be used to claim the 0.05 px optical aspiration | DT | `docs/cad/MECHANICAL_TOLERANCE_BUDGET.md`; physical reseating protocol |
