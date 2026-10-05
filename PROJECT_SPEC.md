# SIGHTLINE™ — Project Specification

## 1. Purpose

Democratise access to high-level ISSF 10 m air-pistol-style training by turning a smartphone, a passive ergonomic
grip, a BLE trigger and a printed ISSF target at ~10 m into a **measurement instrument** that scores dry-fire shots
and quantifies hold and trigger control.

## 2. What SIGHTLINE is not

* **Not a firearm, air gun or launcher.** No component stores energy to propel anything; the grip is a passive phone
  and sensor holder (REQUIREMENTS.md SAF-01, SAF-02).
* **Not an ISSF-approved electronic scoring target** and not for competition scoring.
* **Not "DLSS for shooting".** "DLSS-like computational vision" is an internal analogy only; SIGHTLINE is not
  affiliated with AMD, NVIDIA or their products.

## 3. Users

Athletes and coaches without access to an air pistol, a range or an optoelectronic trainer; clubs and schools in
low-resource settings; researchers studying hold and trigger behaviour.

## 4. Core thesis (master prompt §2)

Determine whether computational reconstruction and learned perception can improve the precision, robustness or
efficiency of smartphone-based shooting-training measurements under realistic camera limitations — judged by
measurement error, never by appearance.

## 5. System overview

```
Printed ISSF target (10 m) ──► phone camera ──► capture layer (stabilisation off, timestamps, intrinsics)
                                                    │
BLE trigger (timestamped events) ──► time sync ─────┤
Phone IMU ──────────────────────────────────────────┤
                                                    ▼
                         target detection ─► sub-pixel aiming-mark geometry ─► rectification
                                                    ▼
                         bore pixel p_b (digital front sight) ─► simulated impact (mm) ─► ISSF score
                                                    ▼
                         temporal trajectory ─► hold / trigger analytics ─► feedback (later: coaching)
```

## 6. MVP (master prompt §26)

The smallest system that proves the thesis: **target detection + calibration + sight geometry + shot geometry +
scoring**, characterised on synthetic data with exact ground truth, then on team-collected data; only then decide
whether reconstruction (temporal or ML) measurably improves it.

## 7. Phases and gates

| Phase | Deliverable | Gate to exit |
|---|---|---|
| 1 Reconnaissance | Verified facts, licence audits, prior art | Key claims classified in VALIDATION.md |
| 2 Foundation | Repository, specifications, ledgers | All foundation documents present and consistent |
| 3 Baseline | Deterministic detection, geometry, calibration maths, impact, scoring | Tests pass; E-001 characterises accuracy |
| 4 Data | Schemas, provenance, synthetic generator, evaluation sets | Synthetic set + first team-collected set with manifests |
| 5 Reconstruction research | RAW vs CLASSICAL vs TEMPORAL vs ML vs HYBRID | Gates G1–G5 (`docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md`) |
| 6 Mobile | On-device pipeline | Golden-output parity with the Python reference; latency/FPS/RAM/thermal measured |
| 7 Hardware | Grip G0–G3, BLE trigger, IMU | CAL-EXP-1..3 and EXP-HW-1 pass on the reference phone |
| 8 Analytics | Deterministic hold/trigger metrics | Metrics validated against reference motion; correlation with outcomes studied |

## 8. Constraints

* On-device inference by default; cloud inference is not assumed acceptable.
* Zero-cost compute preferred: CPU for deterministic work, Kaggle free-tier T4 for any training; AMD MI300X only on
  free credits and only for experiments that need it.
* Every claim carries an evidence status; every external artefact carries a verified licence.

## 9. Principal risks

| Risk | Impact | Mitigation |
|---|---|---|
| Phone stabilisation (OIS/EIS) moves the image relative to the body | Scores and traces corrupted | CAL-EXP-1, device support matrix, Android OIS-sample compensation |
| Trigger-time uncertainty | Decimal-level errors for fast-moving holds | Device timestamps, clock sync, EXP-HW-1 |
| ISP processing (tone mapping, sharpening) | Biased sub-pixel estimates | Minimal-processing capture modes; real-data validation |
| Sight alignment not trained by a video see-through design | Product claim overstated | Stated limitation; eye-tracking research option (D-011) |
| Imitation-firearm regulations | Legal exposure | Non-realistic design; legal check before public use |
