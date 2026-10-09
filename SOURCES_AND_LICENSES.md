# Sources and Licences Ledger

Every external source SIGHTLINE relies on, separated by kind. "Accessed" dates are UTC calendar dates of the session
that read the source. Team-derived work is listed separately and must never be presented as an external source.

## 1. Scientific sources — standards, papers, technical documentation

| ID | Source | URL | Accessed | Used for | Verification |
|---|---|---|---|---|---|
| S-01 | ISSF Rule Book 2026 Edition (Second Print 07/2026, effective 1 July 2026) — General Technical Rules | Copy hosted by the Polish Shooting Federation: <https://www.pzss.org.pl/assets/files/dokumenty/przepisy/kolegium-sedziow/issf/issf-2026/issf-rule-book-2026-edition-2025-second-print-07-2026-effective-1-july-2026.pdf>. The official ISSF link for the first print returned HTTP 404 on access. | 2026-10-05 | GTR 6.3.2.2, 6.3.2.3, 6.3.3.1, 6.3.4.6, 6.4.5, 6.4.6 | Rule text read directly from the PDF |
| S-02 | ISSF Pistol Rules, Edition 2025 (First Print 12/2025, effective 1 January 2026) | Copy: <https://www.tiroalcorcon.com/wp-content/uploads/2026/01/PISTOL_ISSF2026.pdf> | 2026-10-05 | 8.4.3.5, 8.4.4 (calibre), 8.12 (weight, trigger, measuring box) | Rule text read directly |
| S-03 | Android Camera2 API reference: `OisSample`, `CaptureRequest`, `CaptureResult`, `CameraCharacteristics` | <https://developer.android.com/reference/android/hardware/camera2/params/OisSample> and sibling pages | 2026-10-05 | Stabilisation control, OIS samples (API 28), timestamps, rolling-shutter skew, intrinsics keys | Raw HTML read |
| S-04 | Apple AVFoundation / Core Media docs: `preferredVideoStabilizationMode`, `AVCaptureVideoStabilizationMode.off`, `isCameraIntrinsicMatrixDeliveryEnabled`, `kCMSampleBufferAttachmentKey_CameraIntrinsicMatrix` | <https://developer.apple.com/documentation/avfoundation/avcaptureconnection/preferredvideostabilizationmode> and sibling pages | 2026-10-05 | iOS stabilisation default, per-frame intrinsics | Documentation JSON read |
| S-05 | Apple Technical Q&A QA1931 — BLE advertising and connection parameters (archived) | <https://developer.apple.com/library/archive/qa/qa1931/_index.html> | 2026-10-05 | BLE interval limits | Read via fetch summary; archived document |
| S-06 | Wronski et al., "Handheld Multi-Frame Super-Resolution", ACM Transactions on Graphics 38(4), 2019 | <https://arxiv.org/abs/1905.03277> | 2026-10-05 | Hand tremor as sub-pixel diversity | Venue confirmed by search; content summarised from prior knowledge — re-read before citing in a publication |
| S-07 | Karpenko, Jacobs, Baek, Levoy, "Digital Video Stabilization and Rolling Shutter Correction using Gyroscopes", Stanford CTSR 2011-03 | <https://graphics.stanford.edu/papers/stabilization/karpenko_gyro.pdf> | 2026-10-05 | Gyro–camera self-calibration | Paper fetched and summarised |
| S-08 | Mon-López et al., "Optoelectronic analysis of technical factors and performance of elite-level air pistol shooting", PLOS ONE 17(1): e0262276, 2022 | <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0262276> | 2026-10-05 | Prior-art metrics and correlations | Fetched summary; re-check coefficients against full text |
| S-09 | Tom's Hardware, "AMD accidentally marks FSR 4 open-source…", 2025-08-21 | <https://www.tomshardware.com/pc-components/gpus/amd-accidentally-marks-fsr-4-open-source-source-code-reveals-potential-support-for-older-radeon-gpus> | 2026-10-05 | History of FSR 4 source exposure | Press report (one source) |
| S-10 | Wikipedia, "Steyr LP 10" | <https://en.wikipedia.org/wiki/Steyr_LP_10> | 2026-10-05 | Non-authoritative reference values (≈160 m/s, ≈1.06 kg) | Secondary source — UNVERIFIED |
| S-15 | Literature cited from domain knowledge, **not fetched this session**: Zhang (2000) planar camera calibration; Fitzgibbon, Pilu & Fisher (1999) direct least-squares ellipse fitting; Halíř & Flusser (1998) numerically stable direct ellipse fitting; Heikkilä (2000) circular control points; Schied et al. (2017) SVGF; Karis (2014); Salvi (2016); Hartley (1997) rotating-camera self-calibration | — | — | Method background | Verify bibliographic details before any publication |

## 2. Software (dependencies — linked, not copied)

| Package | Version used | Licence | Role | Verification |
|---|---|---|---|---|
| NumPy | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Runtime | Installed package metadata |
| opencv-python(-headless) | 5.0.0.93 | Apache-2.0 | Runtime (image ops, connected components, codecs) | Installed package metadata |
| pytest | 9.1.1 | MIT | Development (tests) | Installed package metadata |

Tools used but neither linked into nor distributed with SIGHTLINE (added 2026-10-06; no new Python dependency):

| Tool | Version used | Licence | Role | Note |
|---|---|---|---|---|
| ffprobe / ffmpeg (command line) | system build | LGPL/GPL depending on the build | Optional: frame timestamps and metadata of clips (`app/vision/video.py`); encoding synthetic test clips | Called as an external program if present; the code works without it |
| Android SDK build-tools, platform `android.jar` | 34.0.0 / API 34 | Android SDK licence (accepted at install) | Compiling and signing the probe APK | Not in the repository; the APK contains only SIGHTLINE classes |
| JDK (Eclipse Temurin) | 17 | GPL-2.0 with Classpath Exception | `javac`, `keytool` for the probe build | Build tool only |

Runtime versions in the Mission 2 session: Python 3.12.3, NumPy 2.4.4, OpenCV 4.13.0 (E-001 was run with the versions
in the table above).

Candidates for the mobile phase (licences **to be verified at adoption**): OpenCV mobile builds, ONNX Runtime Mobile,
LiteRT / TensorFlow Lite, Core ML, MediaPipe.

## 3. Repositories inspected (not incorporated)

| ID | Repository | Commit | Outcome |
|---|---|---|---|
| S-11 | <https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK> | `60f4ea81909200d8542eca14dccb2628b763a9a3` (SDK 2.3.0) | Reference only — `research/AMD_FIDELITYFX_ANALYSIS.md` |
| S-12 | <https://github.com/3zwr1/AMD-NR---OptiScaler> | `f0c0232a2384f1fc9ee0167dcabf2dbe34fd7708` | Reference only — `research/AMD_NR_OPTISCALER_ANALYSIS.md` |

## 4. Data

| ID | Dataset | URL | Licence | Status in SIGHTLINE |
|---|---|---|---|---|
| S-13 | SIDD — Smartphone Image Denoising Dataset | <https://abdokamel.github.io/sidd/> | MIT (stated on the project page) | Candidate for noise-model calibration; not downloaded |
| S-14 | KNSA-shooting-target (Roboflow Universe) | <https://universe.roboflow.com/knsashootingtargets/knsa-shooting-target> | CC BY 4.0 (stated on the page) | Low relevance; not downloaded |
| — | Others surveyed | See `DATASETS.md` | UNVERIFIED | Not used |

## 5. Models and weights

None used. None downloaded.

## 6. Third-party code incorporated

None. See `THIRD_PARTY_CODE.md`.

## 7. Team-derived work (SIGHTLINE's own — DERIVED / SIMULATED)

| Item | Where | Status |
|---|---|---|
| Angular sizes, pixel budget, ring-line visibility argument | `docs/science/TARGET_GEOMETRY_AND_SCORING.md` | DERIVED |
| Shot-centre scoring-zone model and EST-grade 0.4 mm target | same | DERIVED |
| Pellet-drop analysis and the no-drop decision | same; `app/scoring/ballistics.py` | DERIVED |
| Bore-axis definition, sight-alignment decoupling finding, unity-magnification formula, local-affine rectification argument | `docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md` | DERIVED |
| Error budget | `docs/science/ERROR_BUDGET.md` | DERIVED / ASSUMPTION |
| Deterministic baseline, synthetic generator | `app/`, `ml/datasets/` | Implementation |
| Experiment E-001 results | `EXPERIMENT_LOG.md`, `ml/evaluation/results/E-001/` | SIMULATED |
| Mission 2 research report (camera control, stabilisation, localisation limits, sight geometry, licensing) | repository root | Research summary; each statement carries its own status |
| E-004a expected displacements and synthetic sanity check | `ml/evaluation/results/E-004a/` | DERIVED / SIMULATED |
| E-005 Cramér–Rao bound and comparison | `ml/evaluation/results/E-005/` | DERIVED / SIMULATED |
| Printable test target SL-T1-A4 (ISSF-style geometry from the rule dimensions; not an official target) | `docs/experiments/print/` | Original; generated by `scripts/make_print_target.py` |
| Probe app | `app/mobile/android-probe/` | Original; no third-party code |
