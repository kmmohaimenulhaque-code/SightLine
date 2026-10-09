# Research Log

Every investigation that influences a decision is recorded here (master prompt §3.2 and §30). Newest last.
Fields: Date · Question · Sources · Findings · Decision · Implementation impact · Licence impact · Confidence.
Source IDs refer to `SOURCES_AND_LICENSES.md`.

---

## R-000 — Existing SIGHTLINE repository
* **Date:** 2026-10-05
* **Question:** Is there an existing SIGHTLINE codebase to inspect and preserve before building?
* **Sources:** The owner's GitHub repositories visible to the session (one unrelated private repository); the files supplied with the master prompt (master prompt + original concept document).
* **Findings:** No existing SIGHTLINE repository or code. The original concept document is the only prior artefact; its technical claims were checked (R-002, R-003, D-004).
* **Decision:** Initialise a fresh repository with the master prompt's structure. **Licence impact:** none. **Confidence:** High.

## R-001 — ISSF 10 m air-pistol target and range rules
* **Date:** 2026-10-05
* **Question:** What are the authoritative target dimensions, range distance and scoring rules?
* **Sources:** S-01 (ISSF Rule Book 2026, 2nd print 07/2026: GTR 6.3.2.2, 6.3.2.3, 6.3.3.1, 6.3.4.6, 6.4.5, 6.4.6); S-02 (ISSF Pistol Rules 2026: 8.4.3.5, 8.4.4, 8.12). The official ISSF download URL returned HTTP 404 during the session; the rule text was read from federation-hosted copies of the official PDF.
* **Findings:** Ring diameters 11.5 / 27.5 / 43.5 / 59.5 / 75.5 / 91.5 / 107.5 / 123.5 / 139.5 / 155.5 mm (10 → 1 ring); inner ten 5.0 mm; black = rings 7–10 = 59.5 mm; ring lines 0.1–0.2 mm; card ≥ 170 × 170 mm; calibre 4.5 mm; 10 m range ±0.05 m measured from firing line to target face; decimal scores divide each ring's scoring area into ten equal rings; ESTs must score to at least half a decimal ring; target-centre location is the centre of the 10 ring; 10 m air pistol ≤ 1500 g, trigger ≥ 500 g, measuring box 420 × 200 × 50 mm.
* **Decision:** These constants are the single source of truth in `app/scoring/issf.py`.
* **Implementation impact:** Scoring, rendering, synthetic ground truth, grip mass envelope.
* **Licence impact:** None (facts from a rule book; no text reproduced beyond short identifiers).
* **Confidence:** High. *Open:* the paper-target "touching the line scores the higher value" convention lives in a separate annex not retrieved this session (VALIDATION.md C-010).

## R-002 — The concept document's "0.891°" claim
* **Date:** 2026-10-05
* **Question:** Does the black aiming mark subtend 0.891° at 10 m?
* **Sources:** R-001 dimensions; trigonometry.
* **Findings:** Black (59.5 mm) at 10.00 m subtends 5.95 mrad = **0.341°**. 0.891° corresponds to **155.5 mm, the 1-ring**.
* **Decision:** Treat "0.891°" as a mislabelled number. Display calibration is re-derived from first principles (unity magnification, `docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md` §5).
* **Implementation impact:** `app/calibration/display.py`. **Licence impact:** none. **Confidence:** High (pure geometry).

## R-003 — The concept document's "≈0.2 cm pellet drop at 10 m" claim
* **Date:** 2026-10-05
* **Question:** Is a ballistic drop term needed in the simulated impact?
* **Sources:** Free-fall kinematics; S-10 (secondary source: Steyr LP 10 muzzle velocity "approximately 160 m/s").
* **Findings:** No-drag drop below the bore line over 10 m is 16–34 mm for 175–120 m/s (19.2 mm at 160 m/s); drag only increases it. A 2 mm drop would require ≈495 m/s. With sights zeroed at 10 m the net offset at 10 m is zero by construction; across the ISSF ±0.05 m range tolerance it is below ±0.1 mm.
* **Decision:** No drop term in scoring (ARCHITECTURE.md D-005). `app/scoring/ballistics.py` keeps the arithmetic as documentation and tests.
* **Implementation impact:** Simpler, deterministic impact model. **Licence impact:** none. **Confidence:** High for the conclusion; the velocity figure itself is UNVERIFIED (secondary source) but the conclusion holds for any plausible air-pistol velocity.

## R-004 — AMD-NR / OptiScaler
* **Date:** 2026-10-05 · **Sources:** S-12 (repository at commit `f0c0232…`).
* **Findings / Decision:** See `research/AMD_NR_OPTISCALER_ANALYSIS.md`. GPL-3.0 game mod with additional terms; drives NVIDIA's proprietary DLSS NR network on Radeon GPUs; conflicting weight-licence claims. Nothing incorporated (D-007).
* **Licence impact:** Hard exclusion. **Confidence:** High (licence facts).

## R-005 — AMD FidelityFX / FSR SDK
* **Date:** 2026-10-05 · **Sources:** S-11 (repository at `60f4ea8…`, SDK 2.3.0), S-09 (press report).
* **Findings / Decision:** See `research/AMD_FIDELITYFX_ANALYSIS.md`. FSR 2/3 MIT sources but renderer-specific inputs; FSR 4 signed binary only; single-frame upscaling cannot add measurement information. Nothing incorporated (D-007); principles inform D-009.
* **Licence impact:** None incurred. **Confidence:** High (licences), Medium (algorithms).

## R-006 — Camera stabilisation, per-frame metadata and timestamps
* **Date:** 2026-10-05
* **Question:** Can the app stop OIS/EIS from moving the image, or measure what they do? What timing and intrinsics metadata exist?
* **Sources:** S-03 (Android Camera2 reference pages, fetched raw), S-04 (Apple AVFoundation documentation JSON).
* **Findings:** Android: `CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE` toggles OIS where supported; `CONTROL_VIDEO_STABILIZATION_MODE` toggles EIS; `STATISTICS_OIS_DATA_MODE` / `STATISTICS_OIS_SAMPLES` deliver per-frame OIS shifts in pixels (`OisSample`, **added in API level 28**; positive x moves the optical centre left→right in active-array coordinates); `SENSOR_INFO_TIMESTAMP_SOURCE`; `SENSOR_ROLLING_SHUTTER_SKEW`; `LENS_INTRINSIC_CALIBRATION` / `LENS_DISTORTION`. iOS: `preferredVideoStabilizationMode` defaults to `.off` and stabilisation adds latency; `isCameraIntrinsicMatrixDeliveryEnabled` (iOS 11+) attaches a 3×3 intrinsic matrix to each sample buffer. **Not found:** a public iOS control that disables OIS for video.
* **Decision:** Requirement CAM-01 (EIS off; OIS off or compensated; per-device verification by experiment CAL-EXP-1). Proposed Android-first platform (D-012).
* **Implementation impact:** Capture layer design; device support matrix. **Licence impact:** none. **Confidence:** High (API existence); support across devices UNVERIFIED.

## R-007 — Trigger timing: BLE connection intervals
* **Date:** 2026-10-05 · **Sources:** S-05 (Apple Technical Q&A QA1931, archived).
* **Findings:** Apple's accessory rules: Interval Min ≥ 15 ms (multiples of 15 ms); some devices scale a 15 ms request to 30 ms; with a BLE HID service, intervals down to 11.25 ms may be accepted.
* **Decision:** Trigger events carry a device-side timestamp and sequence number; end-to-end latency is measured by experiment (EXP-HW-1) and compensated (`docs/hardware/BLE_TRIGGER_AND_IMU.md`).
* **Licence impact:** none. **Confidence:** Medium (archived document; current platform behaviour to be measured).

## R-008 — Prior art: optoelectronic shooting trainers and hold metrics
* **Date:** 2026-10-05 · **Sources:** S-08 (Mon-López et al., PLOS ONE 2022).
* **Findings:** In one elite air-pistol athlete (360 shots, six competitions, SCATT system at 50 Hz), "cleanness of triggering" measures (DA, DA250) correlated most strongly with score (r ≈ −0.42 to −0.45), followed by aiming-accuracy measures (r ≈ 0.24–0.28).
* **Decision:** Phase 8 metrics start from trigger-window movement and time-in-zone measures, which need accurate trigger timing (reinforces R-007).
* **Licence impact:** none. **Confidence:** Medium: single-athlete study; coefficients taken from a fetched summary and must be re-checked against the full text before reuse.

## R-009 — Reconstruction and calibration literature
* **Date:** 2026-10-05 · **Sources:** S-06 (Wronski et al., Handheld Multi-Frame Super-Resolution, ACM TOG 2019), S-07 (Karpenko et al., Stanford CTSR 2011-03).
* **Findings:** Hand tremor provides real sub-pixel diversity in phone bursts (S-06). A ~10 s handheld video plus gyroscope data suffices to recover focal length, rolling-shutter readout time, gyro-to-frame delay and gyro drift, with ~1 px reprojection error (S-07).
* **Decision:** Temporal fusion in the parameter domain (D-009); gyro–camera self-calibration is the planned calibration and OIS-detection method (`docs/calibration/CALIBRATION_STRATEGY.md`).
* **Licence impact:** none (methods from papers). **Confidence:** High (S-07 read); Medium (S-06 summary from knowledge, venue confirmed by search).

## R-010 — External datasets
* **Date:** 2026-10-05 · **Sources:** S-13 (SIDD project page), S-14 (Roboflow KNSA dataset page), search results for bullet-hole datasets.
* **Findings:** SIDD (smartphone noise; MIT per project page) is useful for calibrating the synthetic noise model. Public shooting-target datasets found are close-up photos of shot cards for bullet-hole detection (e.g. KNSA, CC BY 4.0, 92 images) and do not match a handheld phone viewing an ISSF target at 10 m.
* **Decision:** First-party and synthetic data are required (D-006). See `DATASETS.md`.
* **Licence impact:** Attribution obligations if KNSA is ever used; licences of other candidates UNVERIFIED. **Confidence:** Medium.

## R-011 — Licences of the Python toolchain
* **Date:** 2026-10-05 · **Sources:** installed package metadata (`importlib.metadata`).
* **Findings:** numpy 2.5.3 (BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0); opencv-python 5.0.0.93 (Apache 2.0); pytest 9.1.1 (MIT). SciPy and Pillow are installed but not dependencies.
* **Decision:** Runtime dependencies limited to NumPy and OpenCV (both permissive). **Confidence:** High.

## R-012 — Process lesson: verify API facts against the primary page
* **Date:** 2026-10-05
* **Finding:** A summarising fetch of the Android `OisSample` page reported "API level 30"; the raw HTML of the same page states **"Added in API level 28"**. The summariser had filled a gap from its own assumptions.
* **Decision:** API levels, licence terms and numeric specifications are verified against raw primary text, not tool summaries. Claims taken from summaries are marked Medium confidence (e.g. R-008).

## R-013 — Mission 2 research report filed
* **Date:** 2026-10-06 (report written in an earlier session; read in full before the experimental work)
* **Question:** What do Apple and Android document about stabilisation control, per-frame metadata, timing and intrinsics for the iPhone 15 and Camera2; what are the theoretical localisation limits; what can a screen sight train; which licences fit?
* **Sources:** `SIGHTLINE Mission 2_ iPhone 15 and Android Camera Stabilisation, Localisation Limits, Sight Geometry and Licensing.md` (repository root), with its own per-statement status labels.
* **Findings used here:** no public Apple statement that stabilisation "off" disables the Main camera's sensor-shift OIS; OIS listed for the Main camera only; Android has an explicit OIS control and per-frame OIS samples on the sensor-timestamp clock (device-dependent); the "≈0.07–0.35 mm" figure is a derived precision scale; a camera overlay is a parallax-free sight, not open sights.
* **Decision:** E-004a/b gate everything else. **Licence impact:** owner plans Apache-2.0 (D-013). **Confidence:** as labelled in the report.

## R-014 — Design of the stabilisation experiment without laboratory equipment
* **Date:** 2026-10-06
* **Question:** How can a known sub-milliradian rotation, and a trustworthy dynamic reference, be produced with household means?
* **Sources:** Geometry (`app/calibration/angular.py`, tests); synthetic sanity run of the harness.
* **Findings:** (1) A lever of 400–1000 mm with shims of 0.04–0.8 mm spans 0.1–2 mrad; uncertainty is dominated by shim thickness. (2) The camera must sit over the pivot, or the parallax term (1 + ρ/L) must be applied. (3) Steps test the settled response only — a re-centring stabiliser passes them. (4) For the dynamic response the ground truth must be an independent gyroscope rigidly fixed to the same board (a rigid body has one angular velocity); the hand only excites. (5) Compressed video can freeze static noise.
* **Decision:** D-020. **Implementation impact:** E-004a tests A–D; probe app gyroscope logger. **Licence impact:** none. **Confidence:** High for the geometry; the simulated findings need real data.
