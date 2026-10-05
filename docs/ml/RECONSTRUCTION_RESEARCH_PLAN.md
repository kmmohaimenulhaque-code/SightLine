# Computational Reconstruction — Research Plan (Phase 5)

**Thesis under test:** computational reconstruction and learned perception can improve the precision, robustness or
efficiency of smartphone shooting-training measurements under realistic camera limitations.

**Success metric:** measurement error (impact mm, score tenths, bias, robustness, latency, memory, power). Never
"the image looks sharper".

## 1. Principles (DERIVED)

1. **Single-frame processing cannot add information.** Denoising, sharpening or super-resolving one frame is a
   deterministic function of that frame (data-processing inequality). It can only help an estimator that was
   sub-optimal on the raw pixels, and it can add *bias* (ringing moves edges; generative models invent detail).
2. **Multi-frame data can add information:** more photons and sub-pixel phase diversity from hand tremor
   (Wronski et al. 2019 show this in real phone bursts).
3. **Fuse parameters, not pixels.** The motion between frames is the quantity SIGHTLINE measures. Image-domain
   accumulation would blur it. Separate the problem:
   * *static* parameters (black's scale and ellipse shape, print scale) — pool over many frames;
   * *dynamic* parameter (target centre relative to p_b over time) — temporal filter/smoother, evaluated at the trigger time.
4. **Know the floor.** The Cramér–Rao lower bound (CRLB) for locating the black under a given noise/PSF model says
   how much any estimator could still gain. If the deterministic baseline is near the CRLB, a single-frame ML model
   cannot help; only more data (frames, light, focal length) can.

## 2. Comparison arms

| Arm | Content | Status |
|---|---|---|
| RAW | Deterministic estimators on raw frames: moments, edge-ellipse, hybrid (`app/vision/aiming_mark.py`) | Implemented; characterised by E-001 |
| CLASSICAL | Denoise (bilateral, non-local means), deconvolution with known PSF, unsharp/RCAS-style sharpening, then RAW estimators | Planned; must report bias as well as variance |
| TEMPORAL | Per-frame RAW estimates → Kalman filter / smoothing spline / local polynomial; static-shape pooling; evaluation at the trigger time | Planned — first priority (attacks error terms E1, E7, E8) |
| ML | (a) small CNN regressing sub-pixel centre offset from an ROI; (b) learned denoiser feeding RAW; (c) temporal model over ROI sequences | Not started — gated (§4) |
| HYBRID | ML proposal / outlier gating + deterministic refinement | Not started — gated |

## 3. Protocol

1. **Synthetic first** (known ground truth): `ml/datasets/synthetic_target.py`, conditions spanning light, blur,
   compression, tilt, distortion, camera presets. Synthetic results are labelled SIMULATED.
2. **Team-collected with reference motion:** phone on a tripod / rotation stage with commanded angular steps;
   compare SIGHTLINE's measured trajectory with the commanded one (`DATASET_SPEC.md` §4).
3. **Handheld field data** for robustness; ground truth there is weaker, so it validates detection rate and
   consistency, not sub-millimetre accuracy.
4. Splits by device and session, never by frame. One held-out device model.

## 4. Gates (ML must earn its place)

| Gate | Condition to pass | Status |
|---|---|---|
| G1 | Deterministic baseline characterised across presets/conditions | E-001 (first pass) |
| G2 | CRLB computed per condition; gap between baseline and CRLB known | Not started |
| G3 | TEMPORAL arm implemented and compared with single-frame RAW | Not started |
| G4 | ML arm justified only if, in some realistic condition, the remaining error (after G3) is dominated by E1 **and** the baseline is ≥ 1.5× above the CRLB; the gain must survive on team-collected data | Not started |
| G5 | On-device cost acceptable (latency, memory, power) — Phase 6 | Not started |

## 5. Compute

* Synthetic generation and deterministic evaluation run on CPU (this repository's E-001 ran on a 2-core cloud workspace).
* ML training, if gated in: Kaggle NVIDIA T4 (free tier). AMD MI300X only for large sweeps or high-memory jobs, and
  only on free credits; every GPU run is logged in `EXPERIMENT_LOG.md` with GPU, runtime, VRAM, model, dataset,
  parameters, result and cost.
