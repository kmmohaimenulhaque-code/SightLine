# Changelog

## 0.3.0 — 2026-10-10 — Mission 3 G0 parametric CAD

No physical CAD, mass, COM, optical repeatability or ergonomic result is claimed in this version. The generated
geometry and mass reports are MODEL OUTPUT; the physical measurement templates are intentionally empty.

### Added
* Dependency-free editable G0 CAD source and generator: common chassis/grip, replaceable phone adapters, retainers,
  camera-open region, captive X/Z ballast, passive fiducial and optional IMU/BLE mounts.
* iPhone 15 nominal profile plus an explicitly unselected, dimensionally different Android placeholder profile.
* Deterministic STL/faceted exchange exports, manifests, dimensioned communication drawings and physical measurement templates.
* Weighted mass/COM/inertia solver with rigid transforms, parallel-axis theorem, ballast enumeration, attainable ranges,
  provenance and infeasible-target reporting.
* CAD gate audit, feasibility study, mass reference, compatibility, tolerance, assembly, balance, fabrication, BOM and
  physical-validation documentation.
* 14 focused CAD generation/mass-property tests.

### Decisions
* G0 is opened before E-004a is complete; E-004a remains a gate for camera-supported operation, not for preliminary
  mechanical fit and seating work.
* The 1060 g value is a provisional SIGHTLINE design target only. LP10 COM/inertia values remain unknown.

## 0.2.0 — 2026-10-06 — Mission 2 experimental validation (branch `mission-2-experimental-validation`)

No physical experiment has been run in this version. It adds the means to run them, and one theoretical result.

### Added
* **E-004a** harness (`ml/evaluation/e004a_ois_transfer.py`): response of the image to known rotation — static,
  step, ramp, oscillation; Main vs Ultra Wide comparison with written decision rules; expected-displacement table
  (DERIVED); synthetic sanity check (SIMULATED, 44/44 harness checks).
* Angular ground truth with uncertainty and pivot parallax (`app/calibration/angular.py`); per-frame target tracker
  with four estimators (`app/vision/motion.py`); video reader with presentation timestamps (`app/vision/video.py`);
  time-series analysis (`app/analytics/timeseries.py`).
* **E-004b**: Android Camera2 probe app (`app/mobile/android-probe/`, Java, no libraries; compiles and signs, not
  run on a device) and off-device analysis (`ml/evaluation/e004b_android_probe.py`).
* **E-002 / E-003** harnesses; image characterisation (`app/vision/characterise.py`).
* **E-005**: Cramér–Rao bound (`ml/evaluation/crlb.py`, `e005_localisation_limit.py`) — run; results committed.
* **CAL-EXP-6**: gyroscope log loading and characterisation (`app/imu/gyro.py`, `ml/evaluation/cal_exp6_gyro.py`).
* Capture manifests (`ml/datasets/capture.py`); experiment status vocabulary and evidence-class guard
  (`ml/evaluation/status.py`); synthetic sequences (`ml/datasets/synthetic_sequence.py`).
* Physical protocols and the Mission 2 experimental report (`docs/experiments/`); printable true-scale target.
* 71 new tests (142 in total). `.gitignore`.

### Changed
* Synthetic renderer 0.1.0 → 0.1.1: `expected_canvas` (noise-free model image) and a fixed canvas window
  (`bounds`). Verified bit-identical to 0.1.0 on 37 renders (images and ground truth, SHA-256) before and after.
* Experiment numbering follows the Mission 2 brief (ARCHITECTURE.md D-017). The E-001 entry is unchanged.
* VALIDATION.md: status set extended with REFUTED; "EXPERIMENTAL" now means measured on physical data.
* C-010 (touch scoring rule): now cites the rule text quoted in the Mission 2 research report.

### Findings (all DERIVED or SIMULATED — none experimental)
* Step and ramp tests measure the settled response only; a re-centring stabiliser reads like none (C-052). The
  oscillation test against an independent gyroscope is the decisive one.
* A lens ahead of the rotation pivot adds parallax: 300 mm at 5 m = +6 % (C-053).
* Simulated inter-frame encoders repeat static picture content, so static scatter from compressed video can
  understate noise (C-054).
* The baseline is 1.5–3.1× above the Cramér–Rao bound; per-frame JPEG explains little of it (C-055, C-056).

### Development findings (fixed before release)
* Tracking lost the target when it jumped by more than its radius between frames; the tracker now re-detects in the
  same frame before declaring it invalid.
* Automatic step segmentation split a still interval on a sub-step codec glitch (libx265); the stillness floor is now
  25 % of the smallest expected step. A plateau-count mismatch makes the run INVALID rather than being guessed.
* The first version of the comparison rule called a low ratio with a large uncertainty "tracks"; "tracks" now also
  requires enough precision to exclude suppression.

### Not done
* No `LICENSE` file (owner plans Apache-2.0; D-013). No ML. No grip CAD. No sensor fusion. No still-image analysis.
  No image recorder for the Android OIS-sample comparison (gated on the probe result).

## 0.1.0 — 2026-10-05

### Added
* Repository structure per the master prompt; foundation documents (architecture, specification, requirements,
  validation register, dataset spec and survey, experiment log, sources ledger, third-party register, model card stub).
* Research: verified ISSF 10 m air-pistol target/range/scoring rules (2026 rule book); licence and architecture audits
  of AMD-NR---OptiScaler (commit `f0c0232`) and the FidelityFX/FSR SDK (2.3.0, commit `60f4ea8`); camera-API,
  BLE-timing, prior-art and dataset research (`research/RESEARCH_LOG.md` R-001 … R-012).
* Science notes: target geometry and scoring model, coordinate systems and sight geometry, error budget; calibration
  strategy; reconstruction research plan with gates; BLE trigger/IMU and grip requirements.
* Deterministic baseline (`app/`): ISSF scoring, camera model, pose/bore geometry, ellipse fitting, target-anchored
  rectification with gravity "up", unity-magnification maths, aiming-mark detection with moments/edges/hybrid estimators.
* Synthetic renderer with exact ground truth, provenance records and schema, 13-sample reference set with manifest.
* Experiment E-001 (SIMULATED) and 71 tests.

### Corrected (claims from the original concept document)
* "Black bull ↔ 0.891°" → the black subtends 0.341°; 0.891° is the 1-ring (VALIDATION.md C-012).
* "Pellet drop ≈ 0.2 cm at 10 m" → ≥ 16 mm below the bore for plausible speeds, and zero net effect at the zero
  distance; no drop term (C-013, C-014, D-005).
* "Hough-circle ring detection" → rings are sub-pixel at 10 m; rendered from the ISSF geometry instead (D-004).

### Development findings (fixed before release)
* The moments estimator's flux radius was biased by up to +1.2 % on clean high-resolution renders. Cause: the
  black/white levels were medians, and the thin ring lines, once blurred, cover most core pixels; the ring-6 line also
  sat on the edge of the moments window. Fix: windows placed midway between printed lines, mean levels corrected for
  the known line area, and second moments corrected for the line pattern (D-016). Residual radius error on clean
  renders: < 0.1 %.
* Rectifying with the ellipse alone leaves an in-plane rotation of ≈ yaw·pitch/2 under compound tilt (0.29 mm on a
  19 mm offset at 10°/10°). Added gravity-"up" orientation (D-015): 0.01 mm.
* Pure-noise images produced a false detection; candidates now need contrast ≥ 50 % of the white level and ≥ 8σ of
  the estimated pixel noise.
