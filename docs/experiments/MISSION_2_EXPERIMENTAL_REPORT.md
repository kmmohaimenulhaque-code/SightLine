# Mission 2 — Experimental Validation Report

Date: 2026-10-06 · Branch: `mission-2-experimental-validation` · Version 0.2.0
Status words and evidence classes as defined in `ml/evaluation/status.py` and `VALIDATION.md`.

## A. Executive summary — what was actually demonstrated

**No physical experiment was performed.** The working environment has no phone, target or jig. Nothing in this
report is a measurement of an iPhone or an Android device, and none of the five device experiments has a result.

What exists now:

| Item | Kind of evidence |
|---|---|
| Harnesses, capture manifests and step-by-step protocols for E-004a, E-004b, E-002, E-003, CAL-EXP-6 | Software, tested (142 tests) |
| Android probe app, compiled and signed | Software — **never run on a device** |
| True-scale printable target with calibration bars | File checked for scale; a print must still be measured |
| E-004a harness recovers injected behaviour from simulated, H.264-encoded clips (44/44 checks) | SIMULATED — about the harness, not about a phone |
| E-005: Cramér–Rao bound and the baseline's distance from it | DERIVED / SIMULATED |
| Three design findings (C-052, C-053, C-054) | DERIVED / SIMULATED |

The central question of the mission — does "stabilisation Off" stop the iPhone 15 Main camera from cancelling the
motion SIGHTLINE measures? — is **open**. Section M lists what has to be done physically to close it.

## B. E-004a — iPhone 15 Main vs Ultra Wide — PHYSICAL_DATA_REQUIRED

| Condition | Expected motion | Main observed | Ultra Wide observed | Main response ratio | UW response ratio |
|---|---|---|---|---|---|
| — | — | no data | no data | no data | no data |

Implemented: lever-geometry ground truth with uncertainty and pivot parallax; per-frame tracking with four
estimators; f_px measured from the target in each clip; static statistics; step/ramp response ratio with uncertainty
and creep; gain per frequency band against an independent gyroscope; comparison table with fixed rules and an
explicit scope sentence (device, iOS version, camera, configuration).

Planning values (DERIVED from SECONDARY focal-length priors, not used by the analysis): 1 mrad ≈ 2.9 px on Main 1×
at 2160p and ≈ 1.4 px on the Ultra Wide; 0.1 mrad ≈ 0.29 px and 0.14 px.

From the synthetic sanity run (SIMULATED): steps ≥ 1 mrad are recovered within ±0.03 of the injected ratio, 0.5 mrad
within ±0.07; below that the Ultra Wide scale is too coarse to say much. Band gains 0.5–10 Hz within ±0.04.
**Steps and ramps cannot clear the Main camera**: a stabiliser that re-centres has unit response once settled. The
oscillation test against a gyroscope fixed to the same board is the one that decides.

## C. E-004b — Android capability and OIS metadata — PHYSICAL_DATA_REQUIRED

No device has been probed; its model is not even recorded yet. The probe app reports every camera characteristic
(including the keys named in the brief), logs OIS samples with frame and gyroscope timestamps for 10 s with OIS
requested ON and OFF, and logs the gyroscope alone. The analysis decides from the files — not from expectation —
whether OIS OFF is listed and honoured, whether OIS samples arrive, whether the timebases agree, and what scale, sign
and axis pairing relate the reported OIS shift to the gyroscope. The comparison of *observed image displacement*
with reported OIS displacement needs an image recorder that is PLANNED and will be built only if this phone offers
OIS samples.

## D. E-002 — real iPhone target capture — PHYSICAL_DATA_REQUIRED

No capture exists. The harness reports mean, standard deviation, RMS, p95, maximum, drift and spectrum per
configuration, in pixels, milliradians and millimetres at the target, from the measured black diameter and distance.
It measures precision only.

## E. E-003 — synthetic → real gap — PHYSICAL_DATA_REQUIRED

No real observation exists, so the gap table has no real column. The measurements (edge blur, halo, contrast,
temporal noise and its frame-to-frame correlation, blocking, axis ratio) recover the generator's own parameters on
synthetic frames. Importance and generator changes will be decided by sensitivity runs, not by appearance. One item
to watch, from simulation only: inter-frame encoders repeat static content (C-054).

## F. E-005 — theoretical error budget — COMPLETE for the synthetic model (DERIVED / SIMULATED)

| Pixel scale (ASSUMED preset) | Bound, good light (mm RMS) | Bound, dim light | Best baseline, good light | Baseline / bound |
|---|---|---|---|---|
| 6.89 mm/px (≈ Ultra Wide 2160p prior) | 0.074 | 0.235 | 0.138 | 1.9 |
| 3.45 mm/px (≈ Main 1× 2160p prior) | 0.024 | 0.079 | 0.065 | 2.7 |
| 3.28 mm/px | 0.021 | 0.073 | 0.064 | 3.1 |
| 2.31 mm/px | 0.012 | 0.043 | 0.039 | 3.1 |

* Not knowing scale, tilt, levels and blur costs ×1.15–1.26. Per-frame JPEG 90 explains little of the gap (the
  hybrid estimator is still 1.7–3.2× above the bound without it).
* The budget in `docs/science/ERROR_BUDGET.md` §6 keeps precision and accuracy apart and labels every term.
* Under idealised assumptions, sub-pixel target localisation corresponds to a theoretical/derived spatial scale on
  the order of tenths of a millimetre at 10 m. Real-world accuracy remains experimentally unresolved.

## G. Gyroscope — PHYSICAL_DATA_REQUIRED

No log exists. Implemented: sample rate, interval statistics and jitter, gaps, static bias and noise, Allan deviation
(not evaluated beyond a tenth of the record), axis and sign of a deliberate rotation, temperature pass-through. No
filter, no fusion.

## H. Architecture impact

**None yet, by design.** No evidence exists that would justify a change. Recorded: the candidate vision + gyroscope
split (D-019, PROPOSED), the experiment design (D-020), the evidence-class guard (D-018), capture manifests (D-021),
the numbering (D-017). An Architecture Decision Record will be written when E-004a gives a result.

## I. ML gate — closed

No training was started. E-005 meets one half of gate G4 in simulation (baseline ≥ 1.5× above the bound); the other
half — that image localisation dominates the remaining error — is unknown while stabilisation, timing and ISP are
unmeasured, and a deterministic model-based fit must be tried first. No ML component is justified today
(`docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md` §6 holds the table of candidates with baseline, metric, budgets).

## J. CAD gate — closed

Known: iPhone 15 body dimensions and mass (specification), camera keep-out cones and the no-magnetic-material areas
(Apple drawing, as quoted in the research report). Unknown: measured dimensions of the actual phone; which lens is
where; which camera the grip must serve (depends on E-004a); re-seating repeatability; the Android phone's model
and geometry; eye-to-screen distance; gyroscope axis convention. Full table: `docs/cad/GRIP_REQUIREMENTS.md` §4.

## K. Scientific status of every major conclusion

| Conclusion | Status |
|---|---|
| iPhone 15 Main camera follows rotation with stabilisation Off | UNVERIFIED |
| Ultra Wide is an OIS-free control | VERIFIED as a specification listing; behaviour UNVERIFIED |
| Android phone can switch OIS off / report OIS samples | UNVERIFIED |
| Real static repeatability of the measured centre | UNVERIFIED |
| Real synthetic → real differences | UNVERIFIED |
| Gyroscope rate, jitter, bias, noise | UNVERIFIED |
| Step/ramp tests see only the settled response | DERIVED + SIMULATED |
| Pivot parallax factor (1 + ρ/L) | DERIVED |
| Inter-frame encoders can hide static noise | SIMULATED (software encoders) |
| Bound on impact precision 0.012–0.235 mm RMS | DERIVED from ASSUMED inputs |
| Baseline 1.5–3.1× above the bound | SIMULATED |
| "Tenths of a millimetre" localisation scale | DERIVED (precision, idealised) — not an accuracy claim |
| Vision + gyroscope split is the right architecture | UNVERIFIED (candidate) |
| ML would improve the measurement | UNVERIFIED |
| Probe app works on a device | UNVERIFIED |
| Nothing was REFUTED or made EXPERIMENTAL in this mission | — |

## L. Top 3 next experiments

1. **E-004a including test D** — the only experiment that answers the mission's question. It needs the 10-minute
   E-004b probe run first (the Android phone is the gyroscope reference on the jig).
2. **E-002 / E-003 static captures** — tripod only, no jig: the first real precision numbers, the real f_px, and
   whether the iPhone's video encoder freezes static noise.
3. **CAL-EXP-6 gyroscope logs**, including whether any logger keeps running on the iPhone while a camera app
   records — this decides whether a gyroscope-based hold measurement is possible on iOS without a native app.

## M. What has to be done physically

1. Print `docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf` at 100 %. Measure the black's diameter and both bars.
2. Android phone: install the probe APK; buttons 1 → save, 3 → save, 4 → save (`E-004B_PROTOCOL.md`). Send the three
   JSON files. Record a 10-minute static gyro log (button 6).
3. iPhone 15 on a tripod, target at a measured 10 m: static clips for Main 1×, Main 2×, Ultra Wide
   (`E-002_E-003_PROTOCOL.md`).
4. Build the lever jig; record tests A, B, C for Main and Ultra Wide (`E-004A_PROTOCOL.md`).
5. Tape the Android phone to the jig; record test D for Main and Ultra Wide.
6. For every clip: a capture manifest with the measured numbers. Then run the analysis commands in the protocols.

Until those files exist, every device experiment stays PHYSICAL_DATA_REQUIRED.
