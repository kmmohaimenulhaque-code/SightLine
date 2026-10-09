# Validation Register

Every important technical or scientific statement is classified here (master prompt §4). Statuses: **VERIFIED**
(checked against an authoritative source), **UNVERIFIED**, **ASSUMPTION**, **EXPERIMENTAL** (needs an experiment that
is planned), **DERIVED** (follows mathematically from verified inputs), **SIMULATED** (measured on synthetic data),
**MODEL OUTPUT**, **DESIGN TARGET** (a goal; listed in REQUIREMENTS.md). Source ids → `SOURCES_AND_LICENSES.md`.
Never upgrade a status without new evidence; record the change in `CHANGELOG.md`.

Last full review: 2026-10-05. Mission 2 experimental additions: 2026-10-06 (section H).

From Mission 2 on, every claim carries exactly one of: **VERIFIED · EXPERIMENTAL · SIMULATED · DERIVED · ASSUMED ·
UNVERIFIED · REFUTED** (`ml/evaluation/status.py`). **EXPERIMENTAL** now means *measured on team-collected physical
data*; in sections A–G below, written before this convention, "EXPERIMENTAL" still reads "needs a planned
experiment" and "ASSUMPTION" reads ASSUMED. No claim in this register is EXPERIMENTAL in the new sense yet: no
physical experiment has been run.

## A. ISSF rules and target

| ID | Claim | Status | Evidence | Method | Confidence | Next validation |
|---|---|---|---|---|---|---|
| C-001 | Ring diameters 11.5 … 155.5 mm with tolerances ±0.1/0.1/0.2/±0.5 | VERIFIED | S-01 GTR 6.3.4.6 | Rule text read | High | Re-check when ISSF publishes a new edition |
| C-002 | Black aiming mark = rings 7–10 = 59.5 mm | VERIFIED | S-01 6.3.4.6 | Rule text | High | — |
| C-003 | Inner ten 5.0 mm | VERIFIED | S-01 6.3.4.6 | Rule text | High | — |
| C-004 | Ring lines 0.1–0.2 mm; card ≥ 170 × 170 mm | VERIFIED | S-01 6.3.4.6 | Rule text | High | — |
| C-005 | Air-pistol calibre 4.5 mm | VERIFIED | S-02 8.4.3.5, 8.4.4 | Rule text | High | — |
| C-006 | Range 10 m ± 0.05 m, firing line to target face; athlete's foot behind the firing line | VERIFIED | S-01 6.4.5.1–6.4.5.4 | Rule text | High | — |
| C-007 | Decimal scores divide each ring's scoring area into ten equal rings | VERIFIED | S-01 6.3.3.1 | Rule text | High | — |
| C-008 | EST must score to ≥ ½ decimal ring; = 0.4 mm for air pistol | VERIFIED (rule) / DERIVED (0.4 mm) | S-01 6.3.2.2 + C-009 | Rule text + arithmetic | High | — |
| C-009 | Ring pitch 8.0 mm; decimal step 0.8 mm | DERIVED | C-001 | Arithmetic; `tests/test_scoring.py` | High | — |
| C-010 | Pellet-centre scoring zones = ring radius + 2.25 mm (a hit touching a line scores higher) | DERIVED; touching convention VERIFIED for the 2022 edition of the ISSF "Rules for Paper Target Scoring" as quoted in the Mission 2 research report (Q7c); current edition not located | C-001, C-005; research report Q7c | Rule text quoted in the report | High | Locate the current edition and re-read the clause |
| C-016 | 10 m air pistol ≤ 1500 g, trigger ≥ 500 g, measuring box 420 × 200 × 50 mm | VERIFIED | S-02 8.12 | Table read | High | — |

## B. Concept-document claims and derived geometry

| ID | Claim | Status | Evidence | Method | Confidence | Next validation |
|---|---|---|---|---|---|---|
| C-011 | The black subtends 0.341° (5.95 mrad) at 10 m | DERIVED | C-002 | Trigonometry; `tests/test_scoring.py` | High | — |
| C-012 | Concept: "black ↔ 0.891°" — **incorrect**; 0.891° is the 1-ring (155.5 mm) | DERIVED | C-001 | Trigonometry; test | High | — |
| C-013 | Concept: "pellet drop ≈ 0.2 cm at 10 m" — **incorrect**: ≥ 16 mm below the bore line for any speed ≤ 175 m/s; 2 mm needs ≈ 495 m/s | DERIVED | Kinematics (no drag = lower bound) | `tests/test_ballistics.py` | High | — |
| C-014 | Relative to sights zeroed at 10 m the net drop is 0 at 10 m and < 0.1 mm within ±0.05 m | DERIVED | Kinematics | Test | High | — |
| C-015 | Match air-pistol muzzle velocity ≈ 160 m/s | UNVERIFIED | S-10 (secondary) | — | Medium | Manufacturer specification or chronograph data; conclusion C-013 does not depend on it |
| C-017 | Pixel budget (f_px, mm/px at 10 m) for the presets in `docs/science/TARGET_GEOMETRY_AND_SCORING.md` §4 | DERIVED from ASSUMPTION (C-045) | Formula | — | Medium | Per-device calibration (CAL-EXP-5) |
| C-018 | Ring lines are 0.02–0.09 px wide at 10 m in all presets → rings cannot be detected; render them from the black | DERIVED | C-004, C-017 | Arithmetic | High | Real captures |
| C-019 | Local-affine rectification error < 0.05 mm (offsets ≤ 40 mm, tilt ≤ 20°, k1 = −0.1, bore near centre) | SIMULATED | `tests/test_rectify.py` (600 random poses) | Exact projection + ellipse fit | High | — |
| C-020 | Perspective bias of the ellipse centre < 0.01 px at 10 m | SIMULATED | `tests/test_rectify.py` | Exact projection | High | — |
| C-021 | Scoring needs no intrinsic calibration (target-anchored) | DERIVED + SIMULATED | Geometry doc §6; E-001 measures without intrinsics | — | High (synthetic) | Real captures on ≥ 3 devices |
| C-022 | A video see-through sight cannot train sight *alignment* (eye position does not affect the score) | DERIVED | Geometry doc §4 | Geometric argument | High | Optional demonstration with a rear-sight offset experiment |
| C-023 | Unity magnification s = D_eye·ppi / (25.4·f_px); target-anchored form needs no f_px | DERIVED | Geometry doc §5 | `tests/test_geometry.py` | High | User test of perceived size |

## C. Platforms, timing and hardware

| ID | Claim | Status | Evidence | Method | Confidence | Next validation |
|---|---|---|---|---|---|---|
| C-024 | OIS/EIS can move the image relative to the phone body and corrupt pointing measurements | DERIVED (mechanism); magnitude EXPERIMENTAL | Purpose of stabilisers | — | High (mechanism) | CAL-EXP-1 |
| C-025 | Android Camera2 exposes OIS/EIS control, OIS samples (API 28+), timestamp source, rolling-shutter skew, intrinsics keys | VERIFIED (API existence) | S-03 (raw pages) | — | High; per-device support UNVERIFIED | Device survey |
| C-026 | iOS: video stabilisation defaults to off; per-frame intrinsic matrix (iOS 11+); no public OIS-disable control found | VERIFIED / UNVERIFIED (last part) | S-04 | — | Medium | CAL-EXP-1 on iPhones |
| C-027 | Apple BLE accessory rules: Interval Min ≥ 15 ms (HID down to 11.25 ms) | VERIFIED (archived doc) | S-05 | — | Medium | EXP-HW-1 |
| C-028 | Trigger-timing error 0.02–0.43 mm (1σ) for 5–50 mm/s aim speeds | DERIVED from ASSUMPTION | C-027 + assumed speeds | — | Low–Medium | EXP-HW-1 + measured hold speeds |

## D. Baseline performance (synthetic)

| ID | Claim | Status | Evidence | Method | Confidence | Next validation |
|---|---|---|---|---|---|---|
| C-029 | Single-frame impact error p95 is 0.07–0.23 mm in good light across all four presets (best estimator) | SIMULATED | E-001 | 150 frames per cell | Medium (synthetic ISP) | Tripod captures with commanded motion |
| C-030 | In dim light, 1080p wide misses the 0.4 mm target (p95 0.61 mm); 2160p / 12 MP / tele pass (≤ 0.22 mm) | SIMULATED | E-001 | — | Medium | Real low-light captures; E-003 temporal fusion |
| C-031 | Detection rate 100 % on synthetic ROIs | SIMULATED | E-001 (2 400 frames) | — | Medium; real-scene detection UNVERIFIED | Cluttered real scenes |
| C-032 | Baseline systematic bias ≤ 0.031 mm | SIMULATED | E-001 | — | Medium | Real captures |
| C-046 | No single estimator is best in all conditions (hybrid in good light; edges in dim light/heavy JPEG at ≥ 2160p) | SIMULATED | E-001 | — | Medium | E-002 (CRLB) |

## E. Reconstruction, ML and literature

| ID | Claim | Status | Evidence | Method | Confidence | Next validation |
|---|---|---|---|---|---|---|
| C-033 | Single-frame processing cannot add information about target position | DERIVED | Data-processing inequality | Theory | High | — |
| C-034 | Hand tremor supplies sub-pixel diversity for multi-frame super-resolution on phones | VERIFIED (literature) | S-06 | Summary from knowledge, venue confirmed | Medium | Re-read paper; E-003 |
| C-035 | Gyro + ~10 s video recovers focal length, readout time, gyro delay and drift (~1 px) | VERIFIED (literature) | S-07 | Paper read | High | CAL-EXP-2 |
| C-036 | Trigger-window hold measures correlated most with score (r ≈ −0.42 to −0.45) in one elite air-pistol athlete | VERIFIED for that study | S-08 | Fetched summary | Medium (n = 1) | Re-check full text; own data |
| C-037 | ML improves on the deterministic baseline | UNVERIFIED | No model exists | Gated (`docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md`) | — | Gates G2–G4 |
| C-040 | FSR SDK 2.3.0: all 845 public files listed under MIT; FSR 4 ships only as a signed DLL | VERIFIED | S-11 | Repository inspection | High | — |
| C-041 | AMD-NR: GPL-3.0 + additional terms; network weights stated to belong to NVIDIA; launcher all rights reserved | VERIFIED | S-12 | Repository inspection | High | — |
| C-042 | No public dataset matches SIGHTLINE's imaging condition | UNVERIFIED (limited survey) | `DATASETS.md` | Search | Medium | Wider survey before Phase 5 training |

## F. Open assumptions (must be replaced by measurements)

| ID | Assumption | Used in | Replace with |
|---|---|---|---|
| C-043 | Phone output ≈ power law γ = 2.2 | `app/vision` linearisation; generator | Measured tone curve per device/mode |
| C-044 | Electron counts 300–3 000 e⁻ per unit reflectance; read noise 2–3 e⁻; PSF σ 0.7 px; JPEG 60–90 | E-001 | Noise calibration from real captures (SIDD-style) |
| C-045 | HFOV 67° (wide) and 25° (3× tele) | E-001, pixel budget | Per-device intrinsic calibration |
| C-047 | Eye-to-screen distance ≈ 700 mm, screen ≈ 460 ppi (display examples) | Display maths examples | Grip geometry and device specs |
| C-048 | Hold speeds 5–50 mm/s (steady), 300 mm/s (jerk) | Error budget, E-001 motion condition | First-party hold data |

## G. Not yet validated at all

Real-world accuracy of anything (C-039), mobile latency/FPS/RAM/thermal (C-038), BLE latency, OIS behaviour per
device, print-scale tolerance in practice, ergonomic claims about the grip. All are UNVERIFIED and must not be
claimed.

## H. Mission 2 — experimental validation (2026-10-06)

| ID | Claim | Status | Evidence | Method | Confidence | Next validation |
|---|---|---|---|---|---|---|
| C-049 | With stabilisation "Off", the iPhone 15 Main camera's image follows the phone's rotation (no OIS/EIS suppression) | **UNVERIFIED** | None. Apple does not document what "off" does to sensor-shift OIS (research report Q2a) | — | — | E-004a, test D decisive |
| C-050 | The iPhone 15 Ultra Wide has no OIS and can serve as the control camera | VERIFIED that Apple lists OIS for the Main camera only (research report Q1); behaviour of the Ultra Wide UNVERIFIED | Apple tech specs as quoted in the report | Specification reading | Medium | E-004a: Ultra Wide response ≈ 1 in every condition |
| C-051 | The E-004a harness recovers an injected response: settled step ratio within ±0.03 for steps ≥ 1 mrad (±0.07 at 0.5 mrad), band gains within ±0.04 for 0.5–10 Hz, through an H.264 encode | SIMULATED | `ml/evaluation/results/E-004a/synthetic_sanity/` | Rendered sequences with invented stabilisers | High for the harness; says nothing about a phone | Real clips |
| C-052 | Step and ramp tests measure the settled response only: a stabiliser that cancels motion and then re-centres yields a settled ratio ≈ 1, like no stabiliser | DERIVED (a re-centring stabiliser has unit gain at zero frequency) + SIMULATED | Same folder (recentring rows) | — | High | — |
| C-053 | A camera whose pupil is ρ ahead of the rotation pivot shows image motion × (1 + ρ/L); 300 mm at 5 m = +6 % | DERIVED | `tests/test_angular.py` (explicit geometry) | Trigonometry | High | — |
| C-054 | Inter-frame video compression repeats picture content in static scenes, so static scatter measured from compressed video understates sensor noise (repeated-position share 1 % raw, 25 % x264 crf 18, 57 % x265 crf 20, 99.7 % x264 crf 28) | SIMULATED (software encoders); iPhone hardware encoder UNVERIFIED | E-004a sanity run and the codec comparison recorded in EXPERIMENT_LOG.md | Same frames through different encoders | Medium | E-002: repeated-position share on real HEVC |
| C-055 | Cramér–Rao bound on the simulated impact: 0.012–0.235 mm RMS (0.005–0.034 px) over the E-001 presets and conditions | DERIVED from ASSUMED inputs (C-044, C-045) | E-005 | Fisher information of the synthetic model | High for the model; the model is unvalidated | Redo with measured noise/blur (E-002, E-003) |
| C-056 | The deterministic baseline is 1.5–3.1× above that bound in every cell, and per-frame JPEG 90 explains little of the gap (1.7–3.2× without it) | SIMULATED | E-005 | E-001 trials vs bound; with/without JPEG on the same scenes | Medium | Model-based fit; real data |
| C-057 | Sub-pixel target localisation corresponds to a theoretical/derived spatial scale on the order of tenths of a millimetre at 10 m ("≈0.07–0.35 mm" in the research report) | DERIVED — a precision scale under idealised assumptions, **not** an accuracy claim | Research report Q5a; E-001; E-005 | Literature px figures × mm/px; simulation; bound | Medium | E-002 (precision), E-004a steps (accuracy) |
| C-058 | Real-world static repeatability of the measured centre on the iPhone 15 (any camera) | **UNVERIFIED** | None | — | — | E-002 |
| C-059 | Capabilities of the Android test phone (OIS OFF, OIS samples, timestamp source, intrinsics …) | **UNVERIFIED** | None; the phone has not been probed | — | — | E-004b |
| C-060 | Gyroscope sample rate, jitter, bias and noise of either test phone | **UNVERIFIED** | None | — | — | CAL-EXP-6 |
| C-061 | The print file SL-T1-A4 is at true scale (black 59.5 mm, bars 150 / 100 mm) | VERIFIED for the PDF (rasterised at 300 dpi: 59.48, 150.1, 100.2 mm including line width); any actual print UNVERIFIED until measured | `scripts/make_print_target.py`, `tests/test_print_target.py` | Raster measurement | High (file) | Ruler on the printed sheet, every print |
| C-062 | Synthetic renderer 0.1.1 produces bit-identical images and ground truth to 0.1.0 for the same inputs | VERIFIED | 37 renders hashed before and after the refactor (CHANGELOG 0.2.0) | SHA-256 comparison | High | — |
| C-063 | A vision (absolute pointing) + gyroscope (hold, tremor, trigger dynamics) split is the right measurement architecture | **UNVERIFIED** — candidate only | Research report recommendation | — | — | Decide after E-004a / E-002 / CAL-EXP-6 (ADR then) |
| C-064 | The probe app works on a real Android device | **UNVERIFIED** (compiles, signs, verifies; never executed) | Build log | — | — | First run on the owner's phone |

Nothing in section H upgrades section G: real-world accuracy of anything remains unvalidated.
