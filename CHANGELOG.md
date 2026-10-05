# Changelog

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
