# Target Geometry, Angular Sizes and Scoring

Status labels follow `VALIDATION.md`. Implementation: `app/scoring/issf.py`, `app/scoring/ballistics.py`.

## 1. ISSF 10 m Air Pistol target — VERIFIED

Source: ISSF Rule Book 2026 (Second Print 07/2026, effective 1 July 2026), General Technical Rules 6.3.4.6.

| Ring | Diameter (mm) | Tolerance (mm) | Radius (mm) |
|---|---|---|---|
| 10 | 11.5 | ±0.1 | 5.75 |
| 9 | 27.5 | ±0.1 | 13.75 |
| 8 | 43.5 | ±0.2 | 21.75 |
| 7 | 59.5 | ±0.5 | 29.75 |
| 6 | 75.5 | ±0.5 | 37.75 |
| 5 | 91.5 | ±0.5 | 45.75 |
| 4 | 107.5 | ±0.5 | 53.75 |
| 3 | 123.5 | ±0.5 | 61.75 |
| 2 | 139.5 | ±0.5 | 69.75 |
| 1 | 155.5 | ±0.5 | 77.75 |

* Inner ten: 5.0 mm (±0.1). Black aiming mark: rings 7 to 10 = 59.5 mm (±0.5).
* Ring-line thickness 0.1–0.2 mm. Minimum visible card 170 × 170 mm. Zone numbers 1–8 printed; 9 and 10 unnumbered.
* Calibre 4.5 mm (Pistol Rules 8.4.3.5, 8.4.4). Range 10 m ±0.05 m, measured from the firing line to the target
  face (GTR 6.4.5.1–6.4.5.2); the athlete's foot may not be on or in front of the firing line (6.4.5.4).
* **DERIVED:** the ring pitch is exactly 8.0 mm in radius between every pair of adjacent rings.

## 2. Scoring model

**VERIFIED rule text:** decimal scores divide "the scoring area for one full ring into ten equal scoring rings",
from x.0 to x.9 (GTR 6.3.3.1). An electronic scoring target must score to an accuracy of at least one half of one
decimal ring (GTR 6.3.2.2).

**DERIVED model used by SIGHTLINE.** On paper, a hit that touches a ring line scores the higher value, so for the
**pellet centre** at distance *d* from the target centre:

* scoring-zone radius of ring *n* = ring radius + pellet radius = R_n + 2.25 mm → 10-zone 8.0 mm, 9-zone 16.0 mm, …, 1-zone 80.0 mm;
* decimal step = 8.0 mm / 10 = **0.8 mm**; 10.9 for d ≤ 0.8 mm, 10.8 for 0.8 < d ≤ 1.6 mm, …, 10.0 for 7.2 < d ≤ 8.0 mm, 9.9 for 8.0 < d ≤ 8.8 mm, …, 1.0 for 79.2 < d ≤ 80.0 mm, miss beyond;
* inner ten: d ≤ 2.5 + 2.25 = 4.75 mm;
* integer score = ⌊decimal⌋.

The "touching scores higher" convention is stated in ISSF's separate paper-target scoring annex, which was not
retrieved this session (VALIDATION.md C-010, UNVERIFIED in primary source; high confidence).

**DERIVED accuracy target:** half a decimal ring for air pistol = **0.4 mm** at the target. SIGHTLINE uses this as
its "EST-grade" design target for the image-measurement term (REQUIREMENTS.md MEA-01). SIGHTLINE is not an
ISSF-approved scoring target and makes no claim of approval.

## 3. Angular sizes at 10.00 m — DERIVED

θ = 2·atan(D / 2L), L = 10.00 m.

| Feature | Size (mm) | mrad | degrees | arcsec |
|---|---|---|---|---|
| Inner ten | 5.0 | 0.500 | 0.0286 | 103 |
| 10 ring | 11.5 | 1.150 | 0.0659 | 237 |
| Black aiming mark | 59.5 | 5.950 | **0.3409** | 1227 |
| 1 ring (outer) | 155.5 | 15.550 | **0.8909** | 3207 |
| Card (minimum) | 170 | 17.000 | 0.9740 | 3506 |
| Pellet | 4.5 | 0.450 | 0.0258 | 93 |
| Decimal step | 0.8 | 0.080 | 0.0046 | 16.5 |
| EST-grade accuracy (½ step) | 0.4 | 0.040 | 0.0023 | 8.3 |

**Correction to the concept document.** The concept says the black bull corresponds to a 0.891° field of view.
The black subtends 0.341°; 0.891° is the outer 1-ring. See §5 for how the on-screen size should actually be set.

## 4. Pixel budget at 10 m — DERIVED from ASSUMED fields of view

f_px = (W/2) / tan(HFOV/2); millimetres per pixel at 10 m = 10 000 / f_px. The HFOV values are representative
ASSUMPTIONS for a phone main ("wide", ~26 mm-equivalent) camera and a 3× / 5× telephoto. Real values must come from
per-device calibration.

| Preset (ASSUMPTION) | f_px | mm/px | Black (px) | 1-ring (px) | 10-ring (px) | 0.4 mm in px |
|---|---|---|---|---|---|---|
| Wide, 1080p video (HFOV 67°) | 1450 | 6.90 | 8.6 | 22.6 | 1.7 | 0.058 |
| Wide, 2160p video (67°) | 2901 | 3.45 | 17.3 | 45.1 | 3.3 | 0.116 |
| Wide, 12 MP still (67°) | 3046 | 3.28 | 18.1 | 47.4 | 3.5 | 0.122 |
| Tele 3×, 1080p (25°) | 4330 | 2.31 | 25.8 | 67.3 | 5.0 | 0.173 |
| Tele 3×, 12 MP (25°) | 9094 | 1.10 | 54.1 | 141.4 | 10.5 | 0.364 |
| Tele 5×, 1080p (16.4°) | 6662 | 1.50 | 39.6 | 103.6 | 7.7 | 0.266 |

Consequences (DERIVED):

1. **Ring lines are invisible.** 0.1–0.2 mm lines are 0.02–0.09 px wide in every preset. Rings cannot be
   *detected* at 10 m; they must be *rendered* from the ISSF geometry anchored on the detected black aiming mark
   (ARCHITECTURE.md D-004). "Hough circle detection of the scoring rings" is not feasible at this distance.
2. **Scoring is a sub-pixel measurement problem.** EST-grade accuracy needs the target centre relative to the bore
   pixel to ≈0.06–0.36 px depending on the camera mode.
3. **It is not hopeless.** The black aiming mark is a large, high-contrast disc (8–54 px across). Centroid and
   ellipse estimators average over many edge pixels, so sub-0.1 px precision is plausible under good light.
   Experiment E-001 measures this (SIMULATED).

## 5. Pellet drop — DERIVED (point mass, no drag)

| Muzzle speed | Time of flight (10 m) | Drop below bore line |
|---|---|---|
| 120 m/s | 83.3 ms | 34.1 mm |
| 150 m/s | 66.7 ms | 21.8 mm |
| 160 m/s | 62.5 ms | 19.2 mm |
| 175 m/s | 57.1 ms | 16.0 mm |

* Drag lengthens the time of flight, so these values are lower bounds.
* A 2 mm drop over 10 m would need ≈495 m/s. The concept document's "≈0.2 cm" is therefore wrong by about an order of magnitude.
* **It does not matter for scoring.** Sights are zeroed at the shooting distance; the sight line and trajectory meet
  at 10 m by construction. Relative to a sight line zeroed at Z, the offset at distance d is ½·g·d·(d − Z)/v²
  (small angles, no drag): **0 at 10 m, ±0.096 mm at 10 m ± 0.05 m** (160 m/s).
* **Decision D-005:** no ballistic term in the simulated impact. The muzzle velocity (~160 m/s, secondary source)
  remains UNVERIFIED; the conclusion holds for any plausible air-pistol velocity.

## 6. Print scale and distance

* Scoring is computed in **target units anchored on the printed black** (D-003). A uniformly mis-scaled print
  (e.g. a printer's "fit to page") scales rings and black together, so ring values remain consistent. The only
  residual effect is the pellet-radius term (2.25 mm is a physical size, not a print size). Print scale must
  still be checked (REQUIREMENTS.md CAL-04), because it changes the angular difficulty of the exercise.
* Angular quantities (mrad of hold movement) need the distance. Target-to-eye distance is an ASSUMPTION
  (≈10.0–10.3 m given the firing-line rule).
