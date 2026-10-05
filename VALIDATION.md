# Validation Register

Every important technical or scientific statement is classified here (master prompt §4). Statuses: **VERIFIED**
(checked against an authoritative source), **UNVERIFIED**, **ASSUMPTION**, **EXPERIMENTAL** (needs an experiment that
is planned), **DERIVED** (follows mathematically from verified inputs), **SIMULATED** (measured on synthetic data),
**MODEL OUTPUT**, **DESIGN TARGET** (a goal; listed in REQUIREMENTS.md). Source ids → `SOURCES_AND_LICENSES.md`.
Never upgrade a status without new evidence; record the change in `CHANGELOG.md`.

Last full review: 2026-10-05.

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
| C-010 | Pellet-centre scoring zones = ring radius + 2.25 mm (a hit touching a line scores higher) | DERIVED; touching convention UNVERIFIED in primary source | C-001, C-005; convention widely used | Retrieve ISSF "Rules for Paper Target Scoring" annex | High | Fetch the annex and cite the exact rule |
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
