# SIGHTLINE™ — Architecture (primary source of truth)

This file is the project's memory. A future session must be able to continue from the repository alone.
Last updated: 2026-10-05 (version 0.1.0). Claim statuses: `VALIDATION.md`. Requirements: `REQUIREMENTS.md`.

## 1. Purpose

A non-functional, smartphone-based training instrument for ISSF 10 m air-pistol-style shooting: phone + passive grip
+ BLE trigger + printed ISSF target at ~10 m. Computer vision measures where a simulated bore axis points relative to
the target, scores dry-fire shots and (later) quantifies hold and trigger control. It contains no launching mechanism
of any kind (SAF-01). Scientific objective: determine whether computational reconstruction and learned perception
measurably improve such smartphone measurements — judged by measurement error, never by appearance.

## 2. System architecture

```
                 ┌──────────────────────────── phone ────────────────────────────┐
printed target ──► camera ──► capture layer ──► vision ──► calibration ──► scoring ──► UI / analytics
  (10 m)           │          (stabilisation    (detect,   (rectify,       (ISSF       (Phase 8)
                   │           off, timestamps,  sub-pixel  bore pixel p_b,  decimal,
                   │           intrinsics)       black)     gravity "up")    inner ten)
BLE trigger ───────┼──► time sync ─────────────────────────────┐
phone IMU ─────────┘                                            ▼
                                                     temporal trajectory (Phase 5)
```

Reference implementation in Python (`app/`), the numerical ground truth for future mobile ports (D-001).

## 3. Current implementation (v0.1.0)

| Area | Module | State |
|---|---|---|
| ISSF geometry and scoring | `app/scoring/issf.py` | Implemented, tested (VERIFIED constants; DERIVED scoring zones) |
| Pellet-drop analysis | `app/scoring/ballistics.py` | Implemented, tested; documents D-005 |
| Camera model (pinhole + radial k1, k2) | `app/calibration/camera.py` | Implemented, tested |
| Target pose, bore axis, simulated impact | `app/calibration/pose.py` | Implemented, tested |
| Ellipse fitting | `app/calibration/ellipse.py` | Implemented, tested |
| Target-anchored rectification (+ gravity "up") | `app/calibration/rectify.py` | Implemented, tested |
| Display maths (unity magnification) | `app/calibration/display.py` | Implemented, tested |
| Aiming-mark detection + moments/edges/hybrid estimators | `app/vision/aiming_mark.py` | Implemented, tested on synthetic data; characterised by E-001 |
| Synthetic renderer | `ml/datasets/synthetic_target.py` | Implemented, tested |
| Provenance records | `ml/datasets/provenance.py` | Implemented, tested |
| Experiment E-001 | `ml/evaluation/e001_localisation_budget.py` | Run; results committed |
| Mobile app, temporal tracking, calibration routines (Zhang, gyro), BLE, IMU, CAD, analytics, ML | — | Not started |

Test suite: 71 tests, all passing (`python -m pytest`).

## 4. Data flow (single shot, as implemented)

1. Frame (uint8, gamma-encoded) → `linearize` (γ = 2.2, ASSUMPTION).
2. `find_candidates` → best black-on-white disc candidate.
3. `refine_moments` (pattern-aware levels, flux radius, second moments) → `refine_edges` (radial 50 % crossings,
   direct ellipse fit) → estimator ellipse (moments / edges / hybrid).
4. `ellipse_to_target_affine` (symmetric un-stretch; orientation from gravity "up" or roll) → bore pixel p_b → impact
   (x, y) in target mm.
5. `score_shot` → decimal, integer, inner ten.

## 5. Computer-vision pipeline

See `docs/computer-vision/BASELINE_PIPELINE.md`. Key choices: measure the black as a whole (rings are sub-pixel at
10 m, D-004); scale-free detection; pattern-aware photometric corrections; three estimators compared rather than one
assumed.

## 6. ML pipeline

None (MODEL_CARD.md). Gated plan in `docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md`: RAW → CLASSICAL → TEMPORAL → ML →
HYBRID, with gates G1–G5. G1 passed (E-001). Next: G2 (Cramér–Rao bound) and the TEMPORAL arm.

## 7. Calibration

`docs/calibration/CALIBRATION_STRATEGY.md`. Scoring is target-anchored and needs no intrinsics (D-003). Intrinsics
(Zhang; platform metadata; gyro self-calibration) serve angular metrics, display and gyro fusion. Stabilisation
detection (CAL-EXP-1) is the highest-priority device experiment.

## 8. Mobile deployment

Not started. Platform decision PROPOSED: Android-first native Camera2 (D-012, `app/mobile/README.md`). On-device only
(MOB-01). Port the Python core and require golden-output parity (MOB-03).

## 9. Hardware

`docs/hardware/BLE_TRIGGER_AND_IMU.md`: custom GATT trigger with device timestamps, sequence numbers and clock sync
(proposed); LED-in-frame latency experiment EXP-HW-1. Input device only.

## 10. CAD

`docs/cad/GRIP_REQUIREMENTS.md`: freeze list (15 items, mostly OPEN — phone model is the blocking owner decision),
mass ≤ 1500 g (ISSF), non-realistic appearance, G0–G3 path. No CAD yet; parametric CAD will be the source of truth.

## 11. Datasets

`DATASETS.md` (survey: nothing matches the imaging condition), `DATASET_SPEC.md` (categories, record schema, capture
protocol, splits). Committed: `data/synthetic/v0.1.0` (13 SYNTHETIC samples) + manifest.

## 12. Experiment lifecycle

Config in `ml/configs/` → harness in `ml/evaluation/` → results folder with the config copy, the git commit and the
environment → entry in `EXPERIMENT_LOG.md` → claims updated in `VALIDATION.md` → decisions here. Synthetic results are
always labelled SIMULATED. GPU runs record GPU, VRAM, runtime and cost.

## 13. Validation

`VALIDATION.md` holds 40+ classified claims. Two claims from the original concept were found to be incorrect (C-012:
0.891°; C-013: 0.2 cm pellet drop).

## 14. Performance targets

MEA-01 image-term p95 ≤ 0.4 mm (EST-grade); MEA-02 integer agreement ≥ 99 %; MEA-03 bias ≤ 0.1 mm; MEA-04 detection
≥ 99.5 %; MEA-05 total shot error p95 ≤ 1.0 mm; TIM-01 ≤ 5 ms timing (1σ); MOB-02 ≤ 1 frame latency at 60 fps.

**Status (SIMULATED, E-001):** MEA-01 met in 14 of 16 preset/condition cells (fails: 1080p wide in dim light, 0.61 mm;
1080p wide with JPEG 60, 0.42 mm). MEA-03 and MEA-04 met everywhere. MEA-02 met in all good-light cells (hybrid).

## 15. Limitations

* All performance evidence is synthetic. Real phone ISPs (tone mapping, sharpening, denoising, codecs) are not modelled.
* Sight alignment is not trained by a video see-through design (C-022).
* Stabilisation and trigger timing are unmeasured and may dominate the error (ERROR_BUDGET.md).
* Shot direction relies on gravity and a plumb target; compound tilt without it rotates the plotted direction by
  ≈ yaw·pitch/2 (radial score unaffected).
* Detection assumes tilt ≲ 35° and a standard ISSF print.

## 16. Open questions (owner decisions marked ★)

1. ★ Reference phone model(s) for the first prototype (blocks CAD and device experiments).
2. ★ SIGHTLINE's own licence (proprietary vs. open source) — D-013.
3. ★ Approve Android-first native (D-012)?
4. Does any target phone allow OIS off, or expose OIS samples, in its video modes? (CAL-EXP-1)
5. Real hold-speed distribution of target users (sets the timing requirement).
6. Is the paper-target "touching scores higher" rule stated as assumed? (C-010)
7. Eye-tracking (front camera) to restore sight-alignment training — worth a feasibility study?

## 17. Technical debt

* Gamma 2.2 hard default; needs per-device tone-curve calibration.
* `find_candidates` thresholds are heuristic; tune on real scenes.
* Synthetic renderer: no rolling shutter, no ISP effects, motion blur as translation, no lens vignetting or chromatic effects.
* Python only; no performance work.
* Estimator selection is manual; E-001 shows the best estimator is condition-dependent.

## 18. Research findings (summary; details in `research/RESEARCH_LOG.md`)

* ISSF geometry verified (R-001); two concept claims corrected (R-002, R-003).
* AMD-NR/OptiScaler and FidelityFX/FSR: nothing reusable for SIGHTLINE; principles only (R-004, R-005).
* Android exposes the stabilisation controls and metadata SIGHTLINE needs; iOS is less controllable (R-006).
* BLE delivery granularity is 15–30 ms on iOS (R-007) → device-side timestamps are required.
* Trigger-window movement is the strongest single performance correlate in prior art (R-008, n = 1).
* Hand tremor gives multi-frame sub-pixel diversity; gyro self-calibration is practical (R-009).

## 19. Decision log

| ID | Date | Decision | Rationale | Alternatives | Consequences | Status | Evidence |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-10-05 | Python reference implementation is the numerical ground truth; mobile ports must match its golden outputs | Fast iteration, testable maths, platform-neutral | Write mobile code first | Two implementations to keep in sync (golden files) | ACCEPTED | — |
| D-002 | 2026-10-05 | Simulated bore = ray through the camera centre and bore pixel p_b; front sight drawn at S(p_b) | No parallax, distance-independent, reproducible | Physical barrel axis offset from the camera (30 mm offset = 30 mm error) | Zeroing = choosing p_b | ACCEPTED | Geometry doc §2–3 |
| D-003 | 2026-10-05 | Scoring is target-anchored: local affine map from the imaged black; no intrinsics needed | Target subtends < 1°; weak perspective + local distortion are affine | Full calibrated pose (PnP) | Calibration only for angles/display | ACCEPTED | C-019, C-021, E-001 |
| D-004 | 2026-10-05 | Rings are rendered from the ISSF spec anchored on the black, never "detected" | Ring lines are 0.02–0.09 px wide at 10 m | Hough-circle ring detection (concept doc) | UI overlay is computed | ACCEPTED | C-018 |
| D-005 | 2026-10-05 | No ballistic drop term in the simulated impact | Net drop is zero at the zero distance; < 0.1 mm within range tolerance; the concept's 0.2 cm figure is wrong | Add a drop term | Simpler, deterministic | ACCEPTED | C-013, C-014 |
| D-006 | 2026-10-05 | Synthetic + first-party data; no external dataset for the core task | None matches the imaging condition | Train on bullet-hole datasets | Capture campaign needed | ACCEPTED | R-010 |
| D-007 | 2026-10-05 | Incorporate nothing from AMD-NR/OptiScaler or FidelityFX/FSR | Licence conflicts/ambiguity and technical mismatch | Port FSR shaders | Concepts only | ACCEPTED | Both research reports |
| D-008 | 2026-10-05 | No ML until the baseline is characterised against the CRLB and the error budget | ML must earn its place | Start with a CNN | Gates G1–G5 | ACCEPTED (pending evidence) | Plan doc |
| D-009 | 2026-10-05 | Temporal fusion in the parameter domain (static shape pooled, dynamic centre filtered), not image accumulation | Motion is the signal | FSR-style image accumulation | New E-003 | PROPOSED | R-005, R-009 |
| D-010 | 2026-10-05 | EIS off; OIS off or compensated with OIS samples; devices failing CAL-EXP-1 unsupported | Stabilisers cancel exactly the motion we measure | Ignore | Device support matrix | ACCEPTED as requirement | C-024, C-025 |
| D-011 | 2026-10-05 | MVP does not simulate sight alignment; state it; eye tracking is a research option | Video see-through decouples eye position from the score | Claim it anyway | Honest product scope | PROPOSED | C-022 |
| D-012 | 2026-10-05 | Android-first native (Camera2) | Stabilisation control + OIS samples + timing metadata | iOS-first; cross-platform UI | iOS support later and conditional | PROPOSED — owner approval needed | R-006 |
| D-013 | 2026-10-05 | SIGHTLINE licence undecided; assess third-party compatibility as if proprietary | Conservative | Decide now | GPL code excluded meanwhile | OPEN | — |
| D-014 | 2026-10-05 | Synthetic renderer v0: analytic supersampled ray casting, shot+read noise, γ, JPEG, translation motion blur | Exact ground truth, fast, controllable | Full ISP simulation; 3D engine | Limitations listed in §17 | ACCEPTED | `tests/test_synthetic.py` |
| D-015 | 2026-10-05 | Shot direction from the phone's gravity vector (plumb target); radial score from the ellipse only | Removes compound-tilt rotation (0.29 → 0.01 mm in tests) | Ellipse orientation only | Needs camera–IMU axes per device | PROPOSED | `tests/test_rectify.py`, dev notes |
| D-016 | 2026-10-05 | Moments estimator uses line-aware windows and level corrections (mean with known line area, not median) | The median was biased by blurred ring lines (+1.2 % radius) | Median levels | Assumes the standard ISSF print | ACCEPTED | CHANGELOG 0.1.0 |

## 20. Progress tracker (planning estimate)

Phase weights are a planning convention (DESIGN TARGET), used to report readiness consistently.

| Phase | Weight | Completion | Points | Basis |
|---|---|---|---|---|
| 1 Reconnaissance | 10 | 85 % | 8.5 | Core claims, both AMD audits, APIs, prior art done; annex, iOS OIS, imitation-firearm law, wider dataset survey open |
| 2 Foundation | 10 | 95 % | 9.5 | All documents present; licence and platform decisions open |
| 3 Baseline | 15 | 65 % | 9.75 | Implemented and characterised on synthetic data; no real data, no calibration routines, no tracking |
| 4 Data | 10 | 50 % | 5.0 | Schemas, provenance, generator, reference set; no real or evaluation datasets |
| 5 Reconstruction | 15 | 10 % | 1.5 | RAW arm characterised; plan and gates |
| 6 Mobile | 15 | 0 % | 0 | Platform proposal only |
| 7 Hardware | 15 | 5 % | 0.75 | Requirements and experiments designed |
| 8 Analytics | 10 | 3 % | 0.3 | Prior art and metric list |
| **Total** | 100 | | **≈ 35** | Remaining ≈ 65 |
