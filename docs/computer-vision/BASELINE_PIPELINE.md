# Deterministic Baseline Pipeline (Phase 3)

Implementation: `app/vision/aiming_mark.py` (detection and measurement), `app/calibration/rectify.py` (image → target
mm), `app/scoring/issf.py` (score). Tests: `tests/test_vision.py`, `tests/test_rectify.py`. Characterisation:
experiment E-001 (`EXPERIMENT_LOG.md`).

## 1. What is measured, and why only the black

At 10 m the printed ring lines (0.1–0.2 mm) are 0.02–0.09 px wide in every realistic camera mode
(`docs/science/TARGET_GEOMETRY_AND_SCORING.md` §4), so rings cannot be detected. The only reliably visible feature is
the black aiming mark (59.5 mm): a high-contrast disc of 4–27 px radius. Everything else — ring overlay, scale,
rectification — is anchored on it using the ISSF geometry (D-004).

## 2. Steps

| # | Step | Method | Key parameters (and why) |
|---|---|---|---|
| 1 | Linearise | Inverse power-law transfer (γ = 2.2, ASSUMPTION) | Flux is conserved by blur only in linear light |
| 2 | Detect candidates | Gaussian smoothing (σ 0.8 px); thresholds at 30/45/60 % of the robust intensity range; 8-connected components | Scale-free (no prior on target size); multi-threshold tolerates exposure |
| 3 | Validate candidates | Fill ratio vs. bounding ellipse 0.7–1.3; aspect ≤ 3; not touching the border; annulus 1.5–2.2 r ≥ 85 % bright; contrast ≥ 25 % of range, ≥ 50 % of the white level, ≥ 8σ of pixel noise | A printed black on a white card has > 10:1 contrast; noise blobs, dark walls and patches fail |
| 4 | Moments refinement (iterative, 6 passes) | Black/white levels from a core disc and an annulus whose borders sit midway between printed lines, corrected for the known line area; intensity-weighted centroid; flux ("equivalent area") radius; second moments | Windows are defined in the normalised distance of the current ellipse estimate, so they follow tilt; the moments window (1.403 R) contains the black, its blur skirt and the complete ring-6 line and excludes ring 5 |
| 5 | Edge refinement | 50 % crossings (linear light) along 32–360 radial rays, bilinear sampling at 0.1 px; direct least-squares ellipse fit (Fitzgibbon / Halíř–Flusser) with 2 rounds of MAD outlier rejection | Uses edge information only; immune to the thin lines; biased inward by ≈ σ²/2r on small, blurred discs |
| 6 | Estimators | **moments**: centre + shape + scale from moments. **edges**: everything from the ellipse fit. **hybrid**: centre from moments, axis ratio and orientation from edges, scale from flux | Compared in E-001 |
| 7 | Rectify | Symmetric un-stretch of the ellipse to the 29.75 mm circle; image v-down → target y-up; orientation from the gravity "up" direction (or roll) | Exact under weak perspective; intrinsics not needed (D-003) |
| 8 | Impact + score | Bore pixel p_b mapped through the affine; ISSF decimal/integer/inner-ten score | No ballistic term (D-005) |

**Pattern-aware corrections (DERIVED from the ISSF geometry, line thickness ASSUMED 0.15 mm):**
the dark flux inside the moments window is 0.9980 × that of a plain disc (white lines inside the black remove area,
the ring-6 line adds area); the per-axis second moment is 1.0333 × that of a plain disc. Without these corrections the
flux radius was biased by up to +1.2 % (found during development on clean renders; see `CHANGELOG.md`).

## 3. Classical alternatives considered

| Approach | Verdict for this problem | Reason |
|---|---|---|
| Hough circle transform | Not used for measurement | Quantised accumulator; sub-pixel accuracy needs a refinement step anyway; assumes circles, but tilt makes ellipses |
| Contour + `fitEllipse` on a binary mask | Not used | Integer contour points; threshold-dependent radius bias under blur |
| Template matching / correlation | Candidate for tracking (Phase 5) | Needs a scale/tilt-matched template; good for frame-to-frame tracking of a known appearance |
| RANSAC ellipse fitting | Not needed yet | Edge points come from rays seeded by the moments estimate, so gross outliers are rare; MAD rejection suffices |
| Homography from card corners | Future option | Card corners give orientation and a second scale reference, but may be occluded or out of the ROI |
| Optical flow | Phase 5 (temporal) | For inter-frame motion, not single-frame geometry |

## 4. Known limitations (current)

* Gamma 2.2 is an ASSUMPTION; real phone tone curves (and local tone mapping, sharpening, denoising) differ — error term E11.
  Must be validated on real captures.
* Candidate validation assumes tilt ≲ 35° (the bright annulus must lie on the card).
* The black/white-level correction assumes the ISSF line layout; non-standard prints break it.
* Edge estimator is biased on small discs (< ~6 px radius) and in heavy JPEG compression.
* Single frame only. No temporal fusion, no occlusion handling, no outlier gating across frames (Phase 5).
* Python reference speed (≈ 10–45 ms per ROI including rendering on a 2-core cloud CPU) says nothing about phone performance.
