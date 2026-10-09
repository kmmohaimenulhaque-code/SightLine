# Experiment Log

Every experiment that produces evidence gets an entry. Entries up to E-001 use the original field set; entries from
Mission 2 (experimental validation) use the template of the Mission 2 experimental brief §22: Experiment ID, Date,
Status, Hypothesis, Objective, Hardware, Software, Camera, Configuration, Ground Truth, Method, Parameters, Dataset,
Results, Error, Uncertainty, Failure Modes, Limitations, Conclusion, Next Action. GPU experiments must also record
the GPU model, VRAM used and credits/cost.

**Status vocabulary** (enforced in `ml/evaluation/status.py`): PLANNED · IMPLEMENTED · PHYSICAL_DATA_REQUIRED ·
RUNNING · COMPLETE · FAILED · INVALID · BLOCKED. A planned experiment is never reported as a result; simulation
output is never experimental evidence; physical measurements are never manufactured.

## Register

| ID | Title | Status | Evidence so far |
|---|---|---|---|
| E-001 | Single-frame localisation and scoring error of the baseline | COMPLETE | SIMULATED |
| E-004a | iPhone 15 OIS/EIS transfer function (Main vs Ultra Wide) | **PHYSICAL_DATA_REQUIRED** | none (harness IMPLEMENTED; synthetic sanity SIMULATED) |
| E-004b | Android Camera2 capability probe and OIS-sample validation | **PHYSICAL_DATA_REQUIRED** | none (probe app compiled, never run on a device) |
| E-002 | Real iPhone 15 target capture — static repeatability | **PHYSICAL_DATA_REQUIRED** | none (harness IMPLEMENTED) |
| E-003 | Synthetic → real domain gap | **PHYSICAL_DATA_REQUIRED** | none (harness IMPLEMENTED; depends on E-002 clips) |
| E-005 | Theoretical localisation limit (Cramér–Rao bound, error budget) | COMPLETE (synthetic model); refinement with measured values PHYSICAL_DATA_REQUIRED | DERIVED / SIMULATED |
| CAL-EXP-6 | Raw gyroscope characterisation | **PHYSICAL_DATA_REQUIRED** | none (analysis IMPLEMENTED) |
| E-006 | Screen-sight (Alignment Trainer) geometry and eye position | PLANNED (later) | — |
| E-007 | Temporal fusion of N frames (TEMPORAL arm) | PLANNED | — |

**Numbering change (2026-10-06).** The E-001 entry below ends with "Next: E-002 CRLB, E-003 temporal fusion". The
Mission 2 experimental brief (owner) assigns E-002 to the real capture, E-003 to the domain gap, E-004a/b to the
stabilisation experiments, E-005 to the theoretical limit and E-006 to the screen sight. The owner's numbering is
used from here on: the Cramér–Rao work is part of **E-005**, temporal fusion becomes **E-007**. The E-001 text is
left as written (history). CAL-EXP-1 of `docs/calibration/CALIBRATION_STRATEGY.md` is the same experiment as E-004a.

The result files of E-004a (synthetic sanity) and E-005 were produced from the working tree before it was committed;
their `git_commit` field therefore names the parent commit on `main` (`03ce07e`). The code that produced them is the
first set of commits on `mission-2-experimental-validation`.

---

## E-001 — Single-frame localisation and scoring error of the deterministic baseline

| Field | Value |
|---|---|
| Date | 2026-10-05 |
| Status label | **SIMULATED** — synthetic frames with exact ground truth; not real-world measurement |
| Code | commit `1a3418c46fc9e5fed34092aa716b03e5a1fd3d88`; `ml/evaluation/e001_localisation_budget.py`; config `ml/configs/e001.json` |
| Data | Category SYNTHETIC, generated on the fly by `ml/datasets/synthetic_target.py` v0.1.0; master seed 20261005; per-cell seeds derived by hash (reproducible) |
| Compute | CPU only (2-core cloud workspace, x86_64); **no GPU**; runtime 60.3 s for 2 400 frames; cost: none |
| Environment | Python 3.13.16, NumPy 2.5.3, OpenCV 5.0.0 |
| Artefacts | `ml/evaluation/results/E-001/` — `trials.csv` (7 200 rows: frame × method), `summary.json`, `summary.md`, `config.json` |

**Question.** How accurately does the deterministic baseline measure a single shot from one frame — target-centre
localisation, scale, and the resulting impact position and score — across plausible phone camera modes and
conditions? Does the image term alone meet the EST-grade design target (MEA-01: p95 ≤ 0.4 mm)?

**Hypothesis.** The black aiming mark (8.6–25.8 px across) can be localised to well under 0.1 px in good light,
giving sub-0.4 mm impact error even at 1080p; dim light and heavy compression degrade low-resolution modes first.

**Design.** 4 camera presets (HFOV and resolution are ASSUMPTIONS: wide 67° at 1080p / 2160p / 12 MP; tele 25° at
1080p) × 4 conditions × 150 frames. Conditions: *good light* (3 000 e⁻ per unit reflectance, read noise 2 e⁻, PSF σ
0.7 px, JPEG 90), *dim light* (300 e⁻, 3 e⁻), *good light + motion* (aim moving at 300 mm/s during a 1/60 s
exposure — a trigger-jerk-like speed: 0.7–2.2 px blur), *good light + JPEG 60*. Per frame: impact uniform in a 20 mm
disc, range 9.95–10.05 m, yaw and pitch ±10°, roll ±3°. Estimators: moments, edges, hybrid
(`docs/computer-vision/BASELINE_PIPELINE.md`). Orientation from an ideal gravity reference (ground truth "up"
direction); radial error is reported separately because it is orientation-free and is what the score depends on.

**Results (p95 vector impact error in mm; best estimator per cell, hybrid in brackets).**

| Preset | Good light | Dim light | Good + motion | Good + JPEG 60 |
|---|---|---|---|---|
| Wide 1080p (6.9 mm/px) | **0.227** hybrid | **0.612** hybrid — fails MEA-01 | 0.234 hybrid | **0.418** hybrid — fails narrowly |
| Wide 2160p (3.4 mm/px) | 0.108 hybrid | 0.221 edges (0.323) | 0.126 hybrid | 0.173 edges (0.207) |
| Wide 12 MP (3.3 mm/px) | 0.113 hybrid | 0.198 edges (0.274) | 0.098 hybrid | 0.131 edges (0.171) |
| Tele 3× 1080p (2.3 mm/px) | 0.067 edges (0.070) | 0.110 edges (0.184) | 0.072 hybrid | 0.080 edges (0.120) |

Other measurements (all 48 preset × condition × estimator cells):

* Detection rate **100 %** in every cell (MEA-04 pass).
* Systematic bias: largest mean error component **0.031 mm** (MEA-03 pass everywhere).
* Integer-score agreement 96.0–100 %; ≥ 99 % (MEA-02) in all good-light cells for the hybrid estimator, but not in
  most dim-light and JPEG-60 cells (shots near ring boundaries flip).
* Decimal score exactly right in 58.7–98.7 % of frames (decimal steps are 0.8 mm, so sub-0.4 mm errors still flip
  scores that sit near a boundary; "exact decimal" is not a sensible requirement, MEA-01 is).
* Target-centre error p95: 0.016–0.084 px. Scale error p95: 0.12–2.6 % (edges estimator worst on small discs: inward
  blur bias).
* Measurement time (Python, ROI already cropped, 2-core cloud CPU): 2.9 ms (wide 1080p) to 8.1 ms (tele 1080p) per
  frame. Not representative of a phone.

**Conclusions.**

1. **The single-frame image term meets EST-grade accuracy in good light in every mode tested, including 1080p video**
   (p95 0.23 mm). The original concept's worry — that the target is too small at 10 m — is not the binding constraint
   in good light, *provided* the target is measured as a whole (centroid / ellipse), not by detecting rings.
2. **Dim light at low resolution is where the image term fails** (1080p wide: 0.61 mm). Higher resolution or a
   telephoto camera fixes it in simulation (≤ 0.22 mm). Multi-frame (temporal) fusion is the other candidate and is
   now the first Phase 5 experiment.
3. **No estimator wins everywhere.** Hybrid is best in good light; edges is best in dim light and heavy compression at
   ≥ 2160p. That gap means the baseline is not yet efficient — before any ML, compute the Cramér–Rao bound (gate G2)
   and try a model-based (least-squares blurred-disc) fit.
4. The image term (≈0.1–0.2 mm in good light) is now likely smaller than the unmeasured stabilisation (E6) and timing
   (E7) terms. Those are the priority for real-device work.

**Caveats (why this is SIMULATED, not VERIFIED).** The noise model, PSF, gamma 2.2 and JPEG are stand-ins for a real
ISP (no tone mapping, sharpening, temporal denoising or video codec); no rolling shutter; motion blur is modelled as a
uniform image translation; target print is perfect; the gravity reference is ideal; HFOVs are assumed. Real captures
(DATASET_SPEC.md §4) must confirm or refute these numbers.

**Next.** E-002: CRLB per preset/condition vs. the three estimators (gate G2). E-003: temporal fusion of N frames on
synthetic trajectories (TEMPORAL arm). First team-collected tripod dataset with commanded motion.

---

## E-004a — iPhone 15 OIS/EIS transfer function (Main vs Ultra Wide)

| Field | Value |
|---|---|
| Experiment ID | E-004a (= CAL-EXP-1) |
| Date | 2026-10-06 (harness and protocol); physical execution: not yet |
| Status | **PHYSICAL_DATA_REQUIRED** (harness IMPLEMENTED) |
| Hypothesis | The Main camera's sensor-shift OIS and/or electronic stabilisation may suppress the image motion caused by small rotations even with stabilisation "Off"; the Ultra Wide (no OIS listed) should not |
| Objective | Measure physical angular motion → expected image displacement → observed image displacement, for both cameras; obtain H(f) = observed / expected |
| Hardware | iPhone 15; printed target SL-T1-A4; lever jig (board on two rods, shims); for test D an independent gyroscope rigidly on the same board (Android phone + probe app). None of it has been built or used yet |
| Software | `ml/evaluation/e004a_ois_transfer.py`, `app/vision/motion.py`, `app/analytics/timeseries.py`, `app/calibration/angular.py`, `ml/datasets/capture.py`; config `ml/configs/e004a.json` |
| Camera | Main 1×, Ultra Wide; Main 2× as a separate condition (readout UNKNOWN until measured) |
| Configuration | Stabilisation Off, HDR off, focus/exposure/white balance locked, 2160p30 (60 fps for test D), HEVC — `docs/experiments/E-004A_PROTOCOL.md` |
| Ground Truth | Tests B/C: lever geometry θ = atan(d/r) with propagated uncertainty and the pivot-parallax factor (1 + ρ/L). Test D: gyroscope. Uncontrolled hand motion is never the ground truth |
| Method | Per-frame target centre (ellipse fit primary; moments, phase correlation and raw centroid recorded alongside); f_px measured from the printed target in each clip (never the marketing focal length); A: static statistics; B/C: still-interval segmentation, response ratio with uncertainty, in-plateau creep; D: gain per frequency band against the gyro (clock offset estimated, exposure averaging modelled) |
| Parameters | Target angles 0.1–2 mrad (only if the jig reaches them); decision thresholds in the config (ASSUMED) |
| Dataset | None yet. Capture manifests go to `data/manifests/captures/` (TEAM_COLLECTED); raw video is not committed |
| Results | **None.** No physical measurement exists |
| Error / Uncertainty | To be reported per step (lever, f_px and frame-scatter terms are propagated) |
| Failure Modes | Plateau count ≠ manifest → INVALID; > 5 % unusable frames → INVALID; HDR file or checksum mismatch → INVALID; Ultra Wide control not tracking → comparison INVALID |
| Limitations | Steps and ramps measure the settled response only (see below); roll about the optical axis gives no image translation; one phone, one iOS version |
| Conclusion | None yet |
| Next Action | Owner builds the jig and records the clips (protocol §2–§4) |

**Derived expectations** (`ml/evaluation/results/E-004a/expected_displacements.md`, DERIVED — planning values from
SECONDARY focal-length priors, not used by the analysis): 1 mrad ≈ 2.9 px (Main 1×, 2160p), ≈ 1.4 px (Ultra Wide).

**Synthetic sanity check of the harness** (`ml/evaluation/results/E-004a/synthetic_sanity/`, **SIMULATED — not a
measurement of any phone**; invented stabiliser behaviours injected into rendered frames, encoded with libx264 and
read back through the normal video path; seed 20261006): 44 of 44 harness checks passed.

* Steps ≥ 1 mrad: injected settled ratio recovered within ±0.03 at both pixel scales; at 0.5 mrad within ±0.07. At
  0.1 mrad the Ultra Wide-scale step is 0.15 px and the ratio is only known to about ±0.4 — at that scale steps
  below ≈ 0.5 mrad say little.
* Oscillation against a simulated gyroscope: band gains recovered within ±0.04 (0.5–10 Hz), clock offset found.
* **A stabiliser that cancels motion and then re-centres gives a settled step ratio of ≈ 1.0, the same as no
  stabiliser.** Only the creep indicator differed (0.09–0.28 px against ≤ 0.014 px), and that depends on how soon
  after the step the still interval begins. Consequence: tests B/C cannot clear the Main camera; test D decides.
* Inter-frame compression repeats picture content in static scenes: the share of frame-to-frame position changes
  below 0.001 px was 1 % for uncompressed frames, 25 % (libx264 crf 18), 57 % (libx265 crf 20) and 99.7 % (libx264
  crf 28), with the measured static scatter falling from 0.008 to 0.006 px in the last case. Software encoders only;
  the iPhone's encoder is UNVERIFIED. The harness reports this share for every static clip.

---

## E-004b — Android Camera2 capability probe and OIS-sample validation

| Field | Value |
|---|---|
| Experiment ID | E-004b |
| Date | 2026-10-06 (app and analysis); physical execution: not yet |
| Status | **PHYSICAL_DATA_REQUIRED** |
| Hypothesis | None about the device: nothing is assumed before the phone has been asked |
| Objective | Report per camera: id, facing, focal lengths, sensor size, active/pixel array, OIS modes, video-stabilisation modes, OIS data modes, timestamp source, rolling-shutter skew, exposure/focus controls, distortion, intrinsics, hardware level. If OIS samples exist: check timebases and compare OIS shift with the gyroscope |
| Hardware | The owner's Android phone (model not yet recorded) |
| Software | `app/mobile/android-probe/` (Java, no libraries; APK compiled with build-tools 34.0.0, **never run on a device**); `ml/evaluation/e004b_android_probe.py` |
| Camera | Every camera id the device reports |
| Configuration | OIS log: `TEMPLATE_RECORD`, EIS OFF, OIS ON or OFF as requested, OIS data mode ON where listed; 10 s; images discarded |
| Ground Truth | The phone's own gyroscope (for the OIS-shift comparison) |
| Method | Capability dump of all characteristics; OIS log analysis: sample delivery and rate, frame/OIS/gyro timestamps against `elapsedRealtimeNanos`, least-squares fit of OIS shift on integrated gyro angle (scale px/rad, sign and axis pairing measured, not assumed), OIS-OFF judged from sample scatter |
| Parameters | Thresholds in the script (ASSUMED): gyro RMS ≥ 0.02 rad/s to attempt the fit; OIS scatter < 0.05 px counts as still |
| Dataset | None yet |
| Results | **None.** The analysis was exercised on fabricated files only (`tests/test_e004b.py`, SYNTHETIC) |
| Error / Uncertainty | — |
| Failure Modes | App untested on hardware; OEM may list modes it does not honour; samples may be absent |
| Limitations | Metadata only: observed image displacement vs reported OIS displacement needs an image recorder, PLANNED and gated on this phone offering OIS samples |
| Conclusion | None yet |
| Next Action | Owner installs the APK and saves three files (`docs/experiments/E-004B_PROTOCOL.md`) |

---

## E-002 — Real iPhone 15 target capture: static repeatability

| Field | Value |
|---|---|
| Experiment ID | E-002 |
| Date | 2026-10-06 (harness); physical execution: not yet |
| Status | **PHYSICAL_DATA_REQUIRED** |
| Hypothesis | With phone and target fixed, the measured centre repeats to a few hundredths of a pixel, as E-001 predicts — to be tested, not assumed |
| Objective | First real-world camera baseline: mean, standard deviation, RMS, p95, maximum, drift and spectrum of the measured centre, separately for Main 1×, Main 2×, Ultra Wide and the Android configuration |
| Hardware | iPhone 15, Android phone, tripod/fixed mount, printed target at a measured 10 m |
| Software | `ml/evaluation/e002_static_capture.py` (shares `static_analysis` with E-004a test A) |
| Camera / Configuration | `docs/experiments/E-002_E-003_PROTOCOL.md` |
| Ground Truth | None for position (static). Scale from the **measured** black diameter and distance |
| Method | Track every frame; statistics on the longest gap-free run; px → mrad via measured f_px, px → mm via measured black |
| Dataset | None yet |
| Results | **None** |
| Failure Modes | < 10 s gap-free → INVALID; > 5 % unusable frames → INVALID; codec repeating content → warning (scatter is then a lower estimate) |
| Limitations | Measures precision only. A constant bias is invisible in a static clip |
| Conclusion | None yet |
| Next Action | Owner records the clips |

---

## E-003 — Synthetic → real domain gap

| Field | Value |
|---|---|
| Experiment ID | E-003 |
| Date | 2026-10-06 (harness) |
| Status | **PHYSICAL_DATA_REQUIRED** (uses the E-002 clips) |
| Objective | For each property the generator assumes: synthetic assumption, real observation, difference, importance, recommended generator change |
| Software | `ml/evaluation/e003_domain_gap.py`, `app/vision/characterise.py` |
| Method | Edge profile (10–90 % width, equivalent sigma, halo), levels, temporal noise and its lag-1 correlation, block artefacts, axis ratio — on the real clip and on a matched synthetic clip |
| Results | **None.** On synthetic input the measurements recover the generator's own parameters (edge sigma 0.76 px expected from PSF + pixel aperture; shot noise at the white level; uncorrelated frames) — `tests/test_e002_e003_gyro.py`, SIMULATED |
| Limitations | Not measurable from this target: tone curve, chromatic effects, rolling shutter, motion blur, distortion, ring numerals of official targets. At ≤ 3.5 mm/px the ring lines overlap the edge profile |
| Conclusion | None yet. "Importance" and "recommended change" stay empty until a sensitivity run shows that a difference moves the impact error |
| Next Action | Run on E-002 clips |

---

## E-005 — Theoretical localisation limit (Cramér–Rao bound) and error budget

| Field | Value |
|---|---|
| Experiment ID | E-005 (includes gate G2 of the reconstruction plan) |
| Date | 2026-10-06 |
| Status | **COMPLETE** for the synthetic image model — **DERIVED** (bound) / **SIMULATED** (comparison). Refinement with measured noise, blur and focal length: PHYSICAL_DATA_REQUIRED (needs E-002/E-003) |
| Hypothesis | The deterministic baseline is close to the best achievable precision, so single-frame ML has little to gain |
| Objective | Lower bound on the precision of the simulated impact for the E-001 presets and conditions; distance of the baseline from it; a budget that separates precision from accuracy |
| Hardware | CPU only (1 core cloud workspace); no GPU; runtime 185 s; cost none |
| Software | `ml/evaluation/e005_localisation_limit.py`, `ml/evaluation/crlb.py`; config `ml/configs/e005.json`; Python 3.12.3, NumPy 2.4.4, OpenCV 4.13.0 |
| Camera | Synthetic presets of E-001 (ASSUMED fields of view): 6.9, 3.45, 3.28, 2.31 mm/px |
| Configuration | Good light, dim light, good light + motion blur (as E-001) |
| Ground Truth | Exact (synthetic) |
| Method | Fisher information from the noise-free model image (`expected_canvas`) with shot + read noise; 8 parameters (impact x, y; distance; yaw; pitch; white; black; PSF sigma); pixels within 57.75 mm of the target centre; 12 scenes per cell; bound on the impact with the other six unknown. Compared with the E-001 trials (RMS vector error) |
| Parameters | Seed 20261007; finite-difference steps in the config |
| Dataset | SYNTHETIC, generated on the fly (generator 0.1.1, bit-identical to 0.1.0) |
| Results | `ml/evaluation/results/E-005/summary.md`. Bound on the impact, RMS: **0.012–0.235 mm (0.005–0.034 px)**; p95 0.022–0.41 mm. Not knowing scale, tilt, levels and blur costs ×1.15–1.26. Best E-001 estimator per cell: **1.5–3.1× above the bound** (all estimators: 1.5–6.7×). Without per-frame JPEG the hybrid estimator is still 1.7–3.2× above (with JPEG 90: 1.9–3.5×) |
| Error | Checked against a closed form (Gaussian spot) and a Monte-Carlo least-squares case (`tests/test_crlb.py`) |
| Uncertainty | 12 scenes per cell; baseline RMS from 150 trials per cell |
| Failure Modes | — |
| Limitations | The bound is for the synthetic model with ASSUMED noise, blur and contrast; roll and blur kernel treated as known; quantisation and compression excluded (they can only lose information). It bounds precision, not accuracy |
| Conclusion | (1) Under idealised assumptions, sub-pixel target localisation corresponds to a theoretical/derived spatial scale on the order of hundredths to tenths of a millimetre at 10 m. Real-world accuracy remains experimentally unresolved. (2) The hypothesis is **not supported**: the baseline leaves a factor 1.5–3 on the table, and compression is not the reason. (3) That does not open the ML gate: the first candidate is a deterministic model-based fit, and the unmeasured terms (stabilisation, timing, ISP) may dominate anyway |
| Next Action | Deterministic least-squares blurred-disc fit, re-measured against this bound; redo the bound with measured values after E-002/E-003 |

Scale correspondence (DERIVED from SECONDARY focal-length priors): 3.45 mm/px ≈ iPhone 15 Main 1× at 2160p; 6.9 mm/px
≈ Ultra Wide at 2160p; 2.31 mm/px lies between Main 1× and the UNVERIFIED 2× mode.

---

## CAL-EXP-6 — Raw gyroscope characterisation

| Field | Value |
|---|---|
| Experiment ID | CAL-EXP-6 |
| Date | 2026-10-06 (analysis code) |
| Status | **PHYSICAL_DATA_REQUIRED** |
| Objective | Sample rate, timestamp interval and jitter, static bias, noise, Allan deviation where the record is long enough, axis convention, temperature if logged — before any fusion |
| Hardware | iPhone 15 and the Android phone |
| Software | `app/imu/gyro.py`, `ml/evaluation/cal_exp6_gyro.py`; Android logging by the probe app (buttons 5, 6) |
| Method | Deterministic statistics only. No Kalman filter, no neural network |
| Results | **None.** Code checked on simulated logs (`tests/test_gyro.py`) |
| Limitations | iPhone logging depends on a third-party app whose file layout is not verified here |
| Next Action | `docs/experiments/CAL-EXP-6_GYRO_PROTOCOL.md` |
