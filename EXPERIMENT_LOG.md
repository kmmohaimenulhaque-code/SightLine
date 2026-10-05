# Experiment Log

Every experiment that produces evidence gets an entry. Template fields: id, date, question, hypothesis, data
(category!), method, compute (GPU, runtime, VRAM, cost), parameters, results, conclusion, caveats, artefacts, next.
GPU experiments must also record the GPU model, VRAM used and credits/cost.

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
