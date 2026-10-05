# Measurement Error Budget

The core scientific question is whether SIGHTLINE produces measurably useful information. That depends on the
**largest** error in the chain, not on the one that is easiest to improve with ML. This document lists every term,
its model, its size, its status and how it will be validated. Numbers in millimetres are at the target (10 m).

## 1. Measurement chain

```
trigger press ──► BLE event ──► app clock ─┐
                                           ├─► choose frame(s) / interpolate ─► target ellipse in image ─► rectify ─► impact (mm) ─► score
camera exposure ─► ISP (OIS/EIS, tone map, ─┘                                   ▲
                    denoise, compression)                                       bore pixel p_b (must be fixed in the phone body)
```

## 2. Terms

| # | Term | Model | Typical magnitude | Status | Mitigation | Validation |
|---|---|---|---|---|---|---|
| E1 | Target-centre localisation (noise, PSF, compression, ring lines) | Estimator variance + bias on a disc of 4–27 px radius | See E-001 (§3) | SIMULATED | Moments/edge/hybrid estimators; ROI tracking | E-001; real captures |
| E2 | Scale (mm/px) from the black | Relative scale error ε → ε·\|offset\| | ε = 1 % → 0.08 mm at d = 8 mm | SIMULATED | Blur-invariant flux radius; pool shape over frames | E-001 |
| E3 | Weak-perspective (affine) model error | Perspective curvature over < 1° | Negligible | DERIVED | — | `tests/test_rectify.py` |
| E4 | Lens distortion | Locally affine near the target | Negligible for offsets of tens of px | DERIVED | Calibrate if offsets get large | `tests/test_rectify.py` |
| E5 | Overlay drawn away from S(p_b) | Constant bias = sight misadjustment | 1 screen px at unity magnification ≈ 0.11 camera px ≈ 0.8 mm (1080p wide) | DERIVED | Exact preview-transform bookkeeping; zeroing UI | Device test (render + screenshot) |
| E6 | **OIS / EIS move the image relative to the phone body** | p_b effectively wanders with the stabiliser's correction | Potentially tens of mm (stabilisers exist to cancel hand shake, i.e. exactly SIGHTLINE's signal) | DERIVED (mechanism); magnitude UNVERIFIED | EIS off; OIS off where controllable; else compensate with Android OIS samples; unsupported otherwise | CAL-EXP-1 (gyro vs. image motion) |
| E7 | **Trigger timing** | v_aim × σ_t (+ bias v_aim × latency if uncompensated) | σ_t ≈ 4–9 ms (one 15–30 ms BLE interval, uniform); v = 5–50 mm/s → 0.02–0.43 mm (1σ); bias up to ~1 mm | DERIVED from ASSUMED speeds | Device-side timestamps, clock-offset estimation, latency calibration | EXP-HW-1 (LED-in-frame method) |
| E8 | Interpolation between frames | ≈ a·Δt²/8 for acceleration a | a = 0.5 m/s² (ASSUMPTION): 0.07 mm at 30 fps, 0.02 mm at 60 fps | DERIVED | Higher frame rate; spline over several frames | Synthetic trajectories |
| E9 | Rolling shutter | Target rows are exposed later than row 0 | Within the target: < 1 ms skew (negligible); target row time vs. frame timestamp: up to the readout time (~10–30 ms) | DERIVED | Use row-corrected timestamps (Android `SENSOR_ROLLING_SHUTTER_SKEW`) | CAL-EXP-2 |
| E10 | Motion blur during exposure | Symmetric smear → centroid at mid-exposure | Bias only if the timestamp is not mid-exposure | DERIVED | Timestamp = exposure start + exposure/2 (+ row offset) | E-001 motion conditions |
| E11 | ISP non-linearity (tone mapping, sharpening, local HDR, denoise) | Breaks flux conservation; can shift edges | UNVERIFIED | UNVERIFIED | Fixed exposure, minimal processing modes; raw/YUV capture where available | Real captures vs. ground truth |
| E12 | Print scale, target distance | Score invariant (target-anchored) except the pellet-radius term; angular metrics scale with distance | Print scale 0.97 → pellet-term error ≈ 0.07 mm | DERIVED | Print check (ruler); distance 10 m ± 0.05 m | Protocol |

**Velocities are an ASSUMPTION.** No measured hold-velocity distribution for air-pistol shooters was retrieved this
session. First-party data must establish it (Phase 8, `DATASET_SPEC.md`).

## 3. What E-001 contributes

E-001 measures **E1 + E2 (+E3, E4, E10)** for the single-frame image term on synthetic data with known ground truth.
Results and their interpretation are recorded in `EXPERIMENT_LOG.md` (E-001) and summarised in §4 below.

## 4. Current reading of the budget (after E-001, 2026-10-05)

| Term | Current estimate (p95 at the target) | Evidence |
|---|---|---|
| E1 + E2 (+E3, E4, E10), single frame, good light | 0.07–0.23 mm depending on camera mode | E-001 (SIMULATED) |
| Same, dim light | 0.11–0.61 mm; 1080p wide fails the 0.4 mm target | E-001 (SIMULATED) |
| E3 + E4 model error (offsets ≤ 40 mm, tilt ≤ 20°, k1 = −0.1) | < 0.05 mm | `tests/test_rectify.py` (DERIVED/SIMULATED) |
| E6 stabilisation | Unknown — potentially tens of mm | Not yet measured (CAL-EXP-1) |
| E7 trigger timing | 0.02–0.43 mm (1σ) for 5–50 mm/s holds, plus bias if uncompensated | DERIVED from ASSUMED speeds; EXP-HW-1 pending |
| E11 ISP | Unknown | Real captures pending |

Reading: in good light the image term is already inside the EST-grade target; the unknown terms (E6, E7, E11) now
dominate the uncertainty. The plan follows from that (§5).

## 5. Consequence for the research plan

1. Measurement integrity first: E6 (stabilisation) and E7 (timing) can each exceed the whole EST-grade budget.
   Both are hardware/OS problems that no image model can fix.
2. Image-domain ML reconstruction is justified only where E1 dominates **and** the deterministic estimator is far
   from the Cramér–Rao bound for that condition (`docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md`, gate G2).
3. Temporal estimation (multi-frame) attacks E1, E7 and E8 together, so it is the first "reconstruction" arm to build.
