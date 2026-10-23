# SIGHTLINE G1 — closer-silhouette CAD candidate

**Owner decision (2026-10-11):** build the closer copy of the concept render: enclosed tube-like front housing,
iron sights and trigger guard. The owner states that the local rules were checked and that the instrument is a
harmless dry-fire training grip. That legal check was the owner's; this repository did not research it. The
design stays **passive**: there is no bore, muzzle, chamber, projectile path, pressure system, spring energy store
or sear anywhere. The nose cap is solid and orange, and the left side of the housing is engraved
"SIGHTLINE - PASSIVE TRAINING INSTRUMENT / NOT A FIREARM". The CAD font has no em dash, so a hyphen is used.

Absolute visual reference: `docs/cad/reference/g1_absolute_reference.jpg`. Secondary reference:
`g1_secondary_reference.png`. Both are qualitative. No dimension, mass, camera position or tolerance was taken from
them.

Source: `cad/parametric/sightline_g1/` (geom, assembly, checks, solver, render, build) with parameters
`cad/parametric/parameters/g1.json` and configurations `cad/parametric/configurations/g1/`. The G0 design and its
outputs are unchanged.

```
python -m cad.parametric.sightline_g1.build            # all G1 configurations: checks, mass, exports, renders
python -m cad.parametric.sightline_g1.build --quick    # static checks + mass only
python -m pytest tests/test_cad_g1.py
```

## 1. Frame and transform chain

K1 is the chassis frame. X points toward the target, Y to the shooter's left and Z up. The origin is at the housing
rear face, on the lateral centre plane, at the housing top plane.

`p_K = T_KY · T_YQ · T_QP · p_P` and `p_G = T_KG⁻¹ · p_K`. The frames in that chain are:

* **PHONE BODY P** uses the profile convention: origin at the back-face centre, +x out of the back, +y toward the
  top end.
* **ADAPTER Q** sits where three datums meet: datum A (three TPU back pads), datum B (two TPU ledge pads) and
  datum C (the +Y end block).
* **YOKE Y** has its origin on the pivot axis and carries the dial angle.
* **CHASSIS K1** is defined above.
* **GRIP DATUM G** is the grip axis point on the housing underside, at (55, 0, −40) in K1.

Every configuration stores the matrices in `cad/exports/g1/<CONFIG>/frames.json`. The check `transform_chain`
predicts the phone centroid through the chain and compares it with the solid. The error is 0.0000 mm.

## 2. Phone orientation (acceptance test) — and the conflict it resolves

The phone is **landscape**, with its long axis along Y. The screen faces the shooter (−X) and the rear cameras face
the target (+X). The top end of the phone points to +Y. It sits on the **upper side at the operator end**, in a
compact cradle on a pivot yoke.

A phone lying flat would point its camera upward, so the phone stands in the YZ plane instead. That creates a
second conflict: a phone standing behind the rear sight blocks the line of sight. G1 resolves it geometrically:

* The phone's lower edge is **34 mm above the sight line**. The eye looks under the phone, through the notch, to
  the blade.
* The yoke has **two uprights at y = ±16…22 mm** that straddle the sight line. The pivot hub sits 5 mm above the
  line.
* The check `sight_line_clear` runs a 2 × 1 mm corridor from 800 mm behind the instrument to the front blade. The
  corridor is empty at the nominal angle and at both angle limits.

The price is a high phone. The phone COM sits about 90 mm above the housing top, so the COM-z of the assembly is
higher than the G0 design's. The Z ballast in the grip heel offsets part of that. Rear-camera target sensing is
**not claimed**: the camera centre, lens assignment, protrusion, field of view and OIS behaviour are all PENDING. The
camera keep-out covers both short-end zones of the phone back, 30 mm deep toward the target, and stays empty at
−10°, 0° and +10°.

## 3. Active iron sights

All values are DESIGN unless marked otherwise. Performance is UNVERIFIED.

| Item | Value |
|---|---|
| Rear notch origin (K1) | (61.25, 0, 20) mm |
| Front blade origin (K1) | (279.5, 0, 20) mm |
| Sight radius | 218.25 mm |
| Sight height above housing top | 20 mm (notch bottom = blade top) |
| Rear notch / front blade width | 3.6 mm / 4.0 mm (replaceable notch insert and blade) |
| Rear elevation | ±1.0 mm at the notch, set by an M3 screw on a hinged leaf (±4.3°); return spring |
| Rear windage | ±1.5 mm, M3 screw on a slide, knurled knob on the right |
| Front elevation | shims 0…2 mm in 0.5 mm steps (nominal 1.0 mm) |
| Front lateral | paired shims, ±0.8 mm, clamped by an M3 screw through slotted walls |
| Sight picture | at an ASSUMED 700 mm eye distance: blade 4.36 mrad in a 5.14 mrad notch, 0.39 mrad light gap each side |

Both sights are adjusted by screws or shims. Neither relies on friction alone. Both mount rigidly: the rear base
clamps the rail and the front base screws to the housing. The check `sight_adjustment_travel` covers every
combination of extreme elevation and windage, plus every front shim and lateral extreme.

## 4. Cradle and indexed angle

* **Datums.** Three TPU back pads (datum A) sit at y = ±20 mm and 0, away from both camera end zones. Two TPU
  ledge pads (datum B) sit 12 mm and 114 mm from the top end. The +Y end block is datum C.
* **Pad placement.** The pads avoid the ESTIMATED button spans in the profile (24–75 mm and 35–62 mm from the top
  end). That only holds while the top end faces +Y, so the orientation is fixed.
* **Retainers.** They provide preload only. The right retainer has a nylon M4 screw and a knurled knob. The upper
  anti-lift retainer presses only on the top edge. Lips at the short ends overlap the frame edge by 1.5 mm. Nothing
  contacts the screen glass, the camera glass or the buttons.
* **Angle.** Each upright carries a Ø1.5 mm detent pin. It engages one of nine holes in a dial keyed to the cradle
  shaft: −10° to +10° in 2.5° steps, nominal 0°. A knurled knob on each side clamps the dial. Clearance is checked
  at −10°, 0° and +10°.
* **Phone-specific parts.** The cradle, retainers and pads are phone-specific. The yoke, dials, chassis, grip and
  ballast are shared. The case allowance is a parameter (0 = bare phone).

## 5. Sculpted grip

* **Core.** The grip core is a 30-section B-spline loft of superelliptic sections along a 14° raked axis. The
  sections vary along the grip:
  * the palm swell peaks at s = 48 mm and is 5 mm proud on the palm side;
  * three finger reliefs are 2 mm deep, at s = 30, 52 and 74 mm;
  * the rear swell and the palm heel are on the back;
  * the waist tapers.
* **Thumb rest and beavertail.** The lofted thumb rest stands 12 mm proud on the thumb side. The lofted beavertail
  runs 24 mm rearward.
* **Panels and backstrap.** Planes at y = ±9 mm split off the replaceable side panels. They are held by two M3
  through-bolts per side. A plane parallel to the axis, 12 mm behind it, splits off the replaceable backstrap with
  the beavertail. It is held by two M3 screws along X. Backstrap variants S/M/L are offset −2/0/+3 mm.
* **Palm shelf.** A tongue runs in a raked pocket, indexed by a Ø4 cross pin through one of three holes. Drop is
  0, 4 or 8 mm. Interchangeable wings are offered at −5°, 0° and +5°.
* **Left hand.** The left-hand set (configuration `G1-IP15-LH`) is the exact mirror image. A test checks the
  volumes and mirrored centroids.
* **Fit.** The grip is an original SIGHTLINE design. No Steyr geometry, logo or dimension was used. Ergonomic fit
  is **PENDING user trials**.

## 6. Ballast (integrated, captive)

* **X cassette.** A green Ø26 mm closed tube carries up to 5 steel slugs (Ø20 × 12 mm). It hangs on a T-shoe in a
  T-slot channel with capture lips under the front housing. Travel is 156…222 mm in 6 mm steps (12 positions).
  An M4 knurled lock screw passes through the indexed holes in the channel wall and the 6 mm scale. The rear stop is
  integral. The front stop and end cap are removable so the carriage can be inserted. A check confirms that both
  stops engage one step beyond the range.
* **Z cassette.** A Ø14 mm cassette in a bore along the grip axis carries up to 5 steel slugs (Ø11.4 × 8 mm).
  Spacers set the index at 0, 6, 12 or 18 mm. The bore is closed above. Below, the bottom spacer, the palm shelf and
  its pin close it, and that pin is the accessible lock.
* **Fixed bars.** 0–3 steel bars (118 × 14 × 10 mm) fit in the front bay of the housing.
* **Lateral trim.** There is no lateral trim. The predicted COM-y is −0.5…−1.0 mm, from the palm swell and the
  right-side knobs. It is reported, not hidden.
* **Consistency.** The solver enumerates all 6912 discrete settings from per-part CAD mass properties. The check
  `solver_cad_consistency` confirms that the configured CAD assembly and the solver agree for the configured
  setting.

## 7. Phone family and balance

The configured mass and COM below are MODEL OUTPUT (CAD estimate). None of this has been measured.

| Profile | Mass status | Adapter | Configured setting | Configured mass (MODEL OUTPUT) | Ballast envelope | 1060 g target |
|---|---|---|---|---|---|---|
| Apple iPhone 15 (147.6 × 71.6 × 7.8 mm, 171 g) | MANUFACTURER nominal; COM ESTIMATED at the body centre | B-CRADLE (iPhone 15) | 2 bars, 4 X slugs @ 180, 5 Z slugs @ 0 | 1060.1 ± 39.2 g; COM K1 (124.6, −0.6, −15.4) mm | 652–1219 g; COM-x 70.5–147.2 mm | 1060.1 g reachable; 968 g → 969.8 g; NO VERDICT (tolerance TBD) |
| PLACEHOLDER Android 163 × 76 × 8.9 mm, 200 g | PLACEHOLDER | B-CRADLE (placeholder) | 2 bars, 2 X slugs @ 180, 5 Z slugs @ 0 | 1033.3 ± 40.6 g; COM K1 (116.0, −0.7, −9.1) mm | 684–1251 g; COM-x 68.3–143.9 mm | 1060.4 g reachable (2 bars, 4 @ 180, 0 Z); NO VERDICT |

The left-hand iPhone configuration (G1-IP15-LH) gives 1060.1 g with COM-y −0.39 mm. No profile is infeasible for
the 968 or 1060 g targets. A profile counts as infeasible only for a target outside its envelope, as with
DEMO-INFEASIBLE at 1500 g.

These three support levels are kept apart. **Physical fit** is a CAD check. **Repeatable seating** and **calibrated
optical operation** are PENDING measurement for every profile. The 968 and 1060 g targets are PROVISIONAL. The
target files give COM-x for the demonstration target in the G0 frame K, which does not transfer to K1, so the solver
does not use it. LP 10 COM and inertia are UNKNOWN and are not claimed. The DEMO 1500 g target is reported
INFEASIBLE (insufficient ballast).

## 8. Validation status

| Kind | Status |
|---|---|
| Software checks | collision matrix, keep-outs, sight corridor, transform chain, orientation, printability, moving interfaces (angle, X travel and stops, Z index, palm shelf × wing angle, backstraps, sight extremes), solver/CAD consistency, STEP re-import, STL watertight — see `checks.md` per configuration |
| Native CAD reopen | **not done** (no native CAD tool installed; STEP re-imported with OpenCASCADE only) |
| Physical measurements | **PENDING**: part masses, phone mass and COM, assembled mass and COM, inertia |
| Ergonomic and user testing | **PENDING** |
| Phone and camera measurements | **PENDING**: camera centre, protrusion, FOV, OIS, button positions |
| Mechanical reseating, optical repeatability, sight alignment, printer tolerances, material strength | **PENDING**; nothing was fabricated |
