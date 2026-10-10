# SIGHTLINE™ — Architecture (primary source of truth)

This file is the project's memory. A future session must be able to continue from the repository alone.
Last updated: 2026-10-10 (version 0.3.0, Mission 3 G0 CAD — branch `feature/universal-balanced-grip-cad`).
Claim statuses: `VALIDATION.md`. Requirements: `REQUIREMENTS.md`. Experiments: `EXPERIMENT_LOG.md`.

**Where the project stands.** Mission 1 (foundation, deterministic baseline, E-001) and the Mission 2 research report
are complete. Mission 2 experimental validation has produced the experiment harnesses, protocols, a probe app and one
theoretical result (E-005). **No physical experiment has been run**: E-004a, E-004b, E-002, E-003 and CAL-EXP-6 are
PHYSICAL_DATA_REQUIRED. The architecture below is unchanged by Mission 2 so far; a candidate change is recorded in §2a
and will be decided only on evidence.

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

### 2a. Candidate measurement architecture — NOT a decision (D-019, PROPOSED)

The Mission 2 research report recommends splitting the measurement: vision for absolute, target-relative pointing;
the gyroscope — which a stabiliser cannot alter — for hold, tremor and trigger dynamics; deterministic fusion after a
camera–IMU calibration.

```
   CAMERA: target localisation ──► absolute target-relative pointing ──┐
                                                                       ├─► deterministic fusion ─► simulated impact
   CAMERA–IMU CALIBRATION (axes, time offset, f_px) ───────────────────┤        ─► ISSF scoring ─► training analytics
   GYRO: hold / tremor / trigger dynamics ─────────────────────────────┘
```

Promotion to the primary architecture requires evidence: E-004a (does the image follow the body, per camera and
band?), E-002 (real vision precision), CAL-EXP-6 (what the gyroscope actually delivers). If E-004a shows that OIS
materially changes the design, the change is recorded as an Architecture Decision Record in §19 (fields: Date, Status,
Context, Evidence, Decision, Alternatives, Consequences, Open Questions). No such record exists yet because no such
evidence exists yet.

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
| Angular ground truth, expected image motion, f_px from the target | `app/calibration/angular.py` | Implemented, tested (DERIVED geometry) |
| Per-frame target tracker (ellipse, moments, phase correlation, centroid) | `app/vision/motion.py` | Implemented, tested on synthetic sequences |
| Video reading with presentation timestamps and metadata | `app/vision/video.py` | Implemented, tested (ffprobe optional) |
| Image characterisation (edge, halo, noise, blocking) | `app/vision/characterise.py` | Implemented, tested on synthetic frames |
| Time-series analysis (static stats, spectrum, plateaus, step ratios, gyro-referenced gain) | `app/analytics/timeseries.py` | Implemented, tested |
| Gyroscope log loading and raw characterisation | `app/imu/gyro.py` | Implemented, tested on simulated logs |
| Capture manifests (physical recordings) | `ml/datasets/capture.py` | Implemented, tested |
| Synthetic frame sequences; noise-free model image; fixed canvas | `ml/datasets/synthetic_sequence.py`, `synthetic_target.py` 0.1.1 | Implemented; 0.1.1 bit-identical to 0.1.0 |
| Experiment status vocabulary and evidence-class guard | `ml/evaluation/status.py` | Implemented, tested |
| E-004a harness (rotation response, Main vs Ultra Wide) | `ml/evaluation/e004a_ois_transfer.py` | IMPLEMENTED; **PHYSICAL_DATA_REQUIRED** |
| E-004b probe app and analysis | `app/mobile/android-probe/`, `ml/evaluation/e004b_android_probe.py` | App compiled, never run on a device; **PHYSICAL_DATA_REQUIRED** |
| E-002 / E-003 harnesses | `ml/evaluation/e002_static_capture.py`, `e003_domain_gap.py` | IMPLEMENTED; **PHYSICAL_DATA_REQUIRED** |
| E-005 Cramér–Rao bound | `ml/evaluation/crlb.py`, `e005_localisation_limit.py` | Run; results committed (DERIVED / SIMULATED) |
| CAL-EXP-6 gyroscope runner | `ml/evaluation/cal_exp6_gyro.py` | IMPLEMENTED; **PHYSICAL_DATA_REQUIRED** |
| Printable test target | `scripts/make_print_target.py`, `docs/experiments/print/` | Generated; scale checked on the file |
| Mobile training app, temporal fusion, calibration routines (Zhang, gyro self-calibration), sensor fusion, BLE, CAD, hold analytics, ML | — | Not started |

Test suite: 142 tests, all passing (`python -m pytest`).

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
HYBRID, with gates G1–G5. G1 passed (E-001). G2 passed on the synthetic model (E-005): the baseline is 1.5–3.1× above
the Cramér–Rao bound. The ML gate remains closed (plan §6); next is a deterministic model-based fit.

## 7. Calibration

`docs/calibration/CALIBRATION_STRATEGY.md`. Scoring is target-anchored and needs no intrinsics (D-003). Intrinsics
(Zhang; platform metadata; gyro self-calibration) serve angular metrics, display and gyro fusion. Stabilisation
detection (CAL-EXP-1, run as **E-004a**) is the highest-priority device experiment; CAL-EXP-6 characterises the
raw gyroscope before any fusion.

## 8. Mobile deployment

Training app not started. A measurement-only Camera2 probe exists (`app/mobile/android-probe/`, E-004b). Platform
decision PROPOSED: Android-first native Camera2 (D-012, `app/mobile/README.md`). On-device only
(MOB-01). Port the Python core and require golden-output parity (MOB-03).

## 9. Hardware

`docs/hardware/BLE_TRIGGER_AND_IMU.md`: custom GATT trigger with device timestamps, sequence numbers and clock sync
(proposed); LED-in-frame latency experiment EXP-HW-1. Input device only.

## 10. CAD

`docs/cad/GRIP_REQUIREMENTS.md`: revised freeze list and G0–G3 path. Mission 3 implements a dependency-free editable
G0 source in `cad/parametric/`, generated STL/faceted exchange exports in `cad/exports/`, a nominal iPhone 15 adapter,
a placeholder second profile, captive X/Z ballast and a tested mass-property solver. G0 is MODEL OUTPUT only; physical
fit, printer capability, mass/COM/inertia, camera clearance, optical repeatability, ergonomics and final device support
remain open. E-004a gates camera-supported release, not preliminary phone cradle geometry.

## 11. Datasets

`DATASETS.md` (survey: nothing matches the imaging condition), `DATASET_SPEC.md` (categories, record schema, capture
protocol, splits). Committed: `data/synthetic/v0.1.0` (13 SYNTHETIC samples) + manifest.

## 12. Experiment lifecycle

Config in `ml/configs/` → harness in `ml/evaluation/` → results folder with the config copy, the git commit and the
environment → entry in `EXPERIMENT_LOG.md` → claims updated in `VALIDATION.md` → decisions here. Synthetic results are
always labelled SIMULATED. GPU runs record GPU, VRAM, runtime and cost.

Physical experiments add: protocol in `docs/experiments/` → capture manifest per clip in `data/manifests/captures/`
(raw video never committed) → harness. Status words: PLANNED, IMPLEMENTED, PHYSICAL_DATA_REQUIRED, RUNNING, COMPLETE,
FAILED, INVALID, BLOCKED. `ml/evaluation/status.py` derives the evidence class from the data's provenance category,
so a harness run on synthetic input cannot report COMPLETE or EXPERIMENTAL (D-018).

## 13. Validation

`VALIDATION.md` holds 60+ classified claims; none is yet EXPERIMENTAL (measured on physical data). Two claims from the original concept were found to be incorrect (C-012:
0.891°; C-013: 0.2 cm pellet drop).

## 14. Performance targets

MEA-01 image-term p95 ≤ 0.4 mm (EST-grade); MEA-02 integer agreement ≥ 99 %; MEA-03 bias ≤ 0.1 mm; MEA-04 detection
≥ 99.5 %; MEA-05 total shot error p95 ≤ 1.0 mm; TIM-01 ≤ 5 ms timing (1σ); MOB-02 ≤ 1 frame latency at 60 fps.

**Status (SIMULATED, E-001):** MEA-01 met in 14 of 16 preset/condition cells (fails: 1080p wide in dim light, 0.61 mm;
1080p wide with JPEG 60, 0.42 mm). MEA-03 and MEA-04 met everywhere. MEA-02 met in all good-light cells (hybrid).

## 15. Limitations

* All performance evidence is synthetic. Real phone ISPs (tone mapping, sharpening, denoising, codecs) are not modelled.
* The screen sight is an **Alignment Trainer — a simulated visual alignment and hold-training interface**. It does
  not reproduce the optical behaviour of physical ISSF open sights and must not be described as doing so (D-011; E-006 later).
* Sight alignment is not trained by a video see-through design (C-022).
* Stabilisation and trigger timing are unmeasured and may dominate the error (ERROR_BUDGET.md).
* Shot direction relies on gravity and a plumb target; compound tilt without it rotates the plotted direction by
  ≈ yaw·pitch/2 (radial score unaffected).
* Detection assumes tilt ≲ 35° and a standard ISSF print.

## 16. Open questions (owner decisions marked ★)

1. ★ Reference phone for the grip. Test devices for the experiments are the iPhone 15 and one Android phone (owner,
   Mission 2 brief); whether the iPhone 15 is also the CAD reference waits for E-004a.
2. ★ SIGHTLINE's own licence: the owner plans Apache-2.0 (D-013); `LICENSE`/`NOTICE` not yet added.
3. ★ Approve Android-first native (D-012)?
4. Does any target phone allow OIS off, or expose OIS samples, in its video modes? (CAL-EXP-1)
5. Real hold-speed distribution of target users (sets the timing requirement).
6. Is the paper-target "touching scores higher" rule stated as assumed? (C-010)
7. Eye-tracking (front camera) to restore sight-alignment training — worth a feasibility study? (E-006, later)
8. Does the iPhone 15 Main camera follow rotation with stabilisation Off, per frequency band? (E-004a)
9. Can a gyroscope logger run on the iPhone while a camera app records? If not, iPhone gyro–video work needs a
   native build or the second phone as the reference.
10. Does inter-frame compression hide noise or add refresh steps in real iPhone HEVC? (C-054; E-002)

## 17. Technical debt

* Gamma 2.2 hard default; needs per-device tone-curve calibration.
* `find_candidates` thresholds are heuristic; tune on real scenes.
* Synthetic renderer: no rolling shutter, no ISP effects, motion blur as translation, no lens vignetting or chromatic effects.
* Python only; no performance work.
* Estimator selection is manual; E-001 shows the best estimator is condition-dependent.
* The baseline is 1.5–3.1× above the Cramér–Rao bound in simulation (E-005); a model-based fit is not yet written.
* Still-image (HEIF/DNG) capture analysis is not implemented; the harnesses read video only.
* Automatic segmentation of step sequences is heuristic; the operator can give time windows instead.
* Android constant decoding in `e004b_android_probe.py` was written from memory of the Android reference.

## 18. Research findings (summary; details in `research/RESEARCH_LOG.md`)

* ISSF geometry verified (R-001); two concept claims corrected (R-002, R-003).
* AMD-NR/OptiScaler and FidelityFX/FSR: nothing reusable for SIGHTLINE; principles only (R-004, R-005).
* Android exposes the stabilisation controls and metadata SIGHTLINE needs; iOS is less controllable (R-006).
* BLE delivery granularity is 15–30 ms on iOS (R-007) → device-side timestamps are required.
* Trigger-window movement is the strongest single performance correlate in prior art (R-008, n = 1).
* Hand tremor gives multi-frame sub-pixel diversity; gyro self-calibration is practical (R-009).
* Mission 2 research report (repository root): no Apple document says that stabilisation "off" disables the Main
  camera's sensor-shift OIS; the Ultra Wide lists none; Android exposes an explicit OIS control and OIS samples,
  device-dependent. Everything about actual behaviour is to be measured (E-004a/b).

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
| D-011 | 2026-10-05 | MVP does not simulate sight alignment; state it; eye tracking is a research option. 2026-10-06: the feature is kept and named "Alignment Trainer — a simulated visual alignment and hold-training interface" | Video see-through decouples eye position from the score | Claim it anyway; remove the feature | Honest product scope | PROPOSED | C-022; research report Q6 |
| D-012 | 2026-10-05 | Android-first native (Camera2) | Stabilisation control + OIS samples + timing metadata | iOS-first; cross-platform UI | iOS support later and conditional | PROPOSED — owner approval needed | R-006 |
| D-013 | 2026-10-05 | SIGHTLINE licence undecided; assess third-party compatibility as if proprietary. 2026-10-06: the owner states the software is planned as Apache-2.0 unless the dependency audit finds a concrete incompatibility (none found: NumPy, OpenCV, pytest are permissive; research report Q7a). CAD and datasets are licensed separately. No `LICENSE` file has been added in this branch | Conservative until the file exists | Add the licence now | GPL code stays excluded | PLANNED: Apache-2.0 — owner to confirm adding `LICENSE`/`NOTICE` | Mission 2 brief §26 |
| D-014 | 2026-10-05 | Synthetic renderer v0: analytic supersampled ray casting, shot+read noise, γ, JPEG, translation motion blur | Exact ground truth, fast, controllable | Full ISP simulation; 3D engine | Limitations listed in §17 | ACCEPTED | `tests/test_synthetic.py` |
| D-015 | 2026-10-05 | Shot direction from the phone's gravity vector (plumb target); radial score from the ellipse only | Removes compound-tilt rotation (0.29 → 0.01 mm in tests) | Ellipse orientation only | Needs camera–IMU axes per device | PROPOSED | `tests/test_rectify.py`, dev notes |
| D-016 | 2026-10-05 | Moments estimator uses line-aware windows and level corrections (mean with known line area, not median) | The median was biased by blurred ring lines (+1.2 % radius) | Median levels | Assumes the standard ISSF print | ACCEPTED | CHANGELOG 0.1.0 |
| D-017 | 2026-10-06 | Experiment IDs follow the Mission 2 experimental brief (E-002 real capture, E-003 domain gap, E-004a/b stabilisation, E-005 theoretical limit, E-006 screen sight); the Cramér–Rao work moves into E-005, temporal fusion becomes E-007 | The owner's brief is the newer instruction; one numbering avoids confusion | Keep the E-001 "next" numbering | E-001's closing line is historical | ACCEPTED | EXPERIMENT_LOG.md register |
| D-018 | 2026-10-06 | Evidence class is derived from data provenance in one place (`ml/evaluation/status.py`); only TEAM_COLLECTED data can make an experiment COMPLETE / EXPERIMENTAL | Makes "never present simulation as experiment" a property of the code, not of discipline | Label by hand | Every harness writes the same status block | ACCEPTED | `tests/test_capture_and_status.py` |
| D-019 | 2026-10-06 | Candidate: split measurement into vision (absolute pointing) and gyroscope (hold, tremor, trigger), fused deterministically (§2a) | A stabiliser cannot alter the gyroscope; research report recommendation | Vision only (current); gyro only | Needs camera–IMU calibration and a logger that runs with the camera | **PROPOSED — not decided; awaits E-004a, E-002, CAL-EXP-6** | C-063 |
| D-020 | 2026-10-06 | E-004a ground truth: lever geometry for steps/ramps, an independent rigidly co-mounted gyroscope for oscillation; Ultra Wide as control; f_px measured from the target per clip | Steps only test the settled response (C-052); hand motion may excite but never be the ground truth | Turntable (not available); hand motion as truth (rejected) | Test D needs the second phone on the jig | ACCEPTED (experiment design) | E-004a synthetic sanity |
| D-021 | 2026-10-06 | Capture manifests: one validated JSON per clip, raw video never in Git (sha256 only) | Provenance for every physical capture | Commit video; free-text notes | `data/manifests/captures/` | ACCEPTED | `ml/datasets/capture.py` |
| D-022 | 2026-10-10 | Open G0 mechanical CAD before E-004a is complete, while keeping camera-supported release conditional | E-004a decides optical body-motion behaviour, not whether a passive cradle can be fit-checked; separate mechanical P1/P2 from optical P3 | Wait for all camera experiments before any adapter geometry | G0 geometry mule is implemented; G1–G3 remain evidence-gated | ACCEPTED for G0 | `docs/cad/CAD_GATE_AUDIT.md`, `docs/cad/CAD_DESIGN_REPORT.md` |

## 20. Progress tracker (planning estimate)

Phase weights are a planning convention (DESIGN TARGET), used to report readiness consistently.

| Phase | Weight | Completion | Points | Basis |
|---|---|---|---|---|
| 1 Reconnaissance | 10 | 90 % | 9.0 | Mission 2 research report added (camera control, stabilisation, limits, sight geometry, licensing); imitation-firearm law, wider dataset survey open |
| 2 Foundation | 10 | 95 % | 9.5 | All documents present; licence and platform decisions open |
| 3 Baseline | 15 | 70 % | 10.5 | Plus per-frame tracking and the bound (E-005); no real data, no calibration routines, no model-based fit |
| 4 Data | 10 | 55 % | 5.5 | Plus capture manifests, protocols, print target; still no real data |
| 5 Reconstruction | 15 | 15 % | 2.25 | RAW arm characterised; G2 passed on the synthetic model; TEMPORAL arm not started |
| 6 Mobile | 15 | 2 % | 0.3 | Platform proposal; measurement-only probe app (untested on hardware) |
| 7 Hardware | 15 | 18 % | 2.7 | G0 CAD source, two phone-profile pathways, ballast solver and validation harnesses implemented; no physical hardware evidence |
| 8 Analytics | 10 | 3 % | 0.3 | Prior art and metric list |
| **Total** | 100 | | **≈ 39.5** | Remaining ≈ 60.5. Mission 3 adds reproducible G0 mechanics and model-based mass balance; the physical experiments that decide camera support are still to run |
