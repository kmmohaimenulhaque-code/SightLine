# Passive Training Grip — Requirements and Freeze List (Phase 7, not started)

The grip is a **non-functional, passive holder** for a phone, a BLE trigger switch and optional sensors. It is not a
copy of a commercial air pistol and contains no barrel, no pressure system and no launching mechanism. Parametric CAD
(in `cad/parametric/`) is the source of truth; STL files are generated outputs.

## 1. Freeze list (must be complete before final CAD)

| # | Item | Current status | Evidence / note |
|---|---|---|---|
| 1 | Phone model(s) | **OPEN — owner decision** | Prefer one Android reference device that passes CAL-EXP-1 (OIS controllable or OIS samples available) |
| 2 | Phone dimensions | OPEN | Manufacturer spec + caliper measurement into `cad/measurements/` |
| 3 | Camera position on the phone | OPEN | Measured; defines frame C relative to frame G |
| 4 | Sight-axis geometry | Concept defined (bore ray through the camera centre, D-002); numbers OPEN | `docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md` |
| 5 | Grip angle | OPEN | Adjustable insert; no reference value verified this session |
| 6 | Target geometry | **VERIFIED** | ISSF GTR 6.3.4.6 |
| 7 | Total mass target | DESIGN TARGET: ≤ 1500 g hard limit (ISSF 10 m air-pistol maximum, Pistol Rules 8.12 — VERIFIED); proposed working band 0.95–1.20 kg with ballast | Reference: Steyr LP 10 ≈ 1.06 kg filled (secondary source, UNVERIFIED) |
| 8 | Centre-of-mass target | OPEN | Computed as r_COM = Σ mᵢ rᵢ / Σ mᵢ from measured component masses; adjustable ballast positions |
| 9 | Printer / material | OPEN | Candidate FDM materials (PETG, PLA+) — ASSUMPTION |
| 10 | Fasteners | OPEN | Prefer captive heat-set inserts for repeatable assembly — ASSUMPTION |
| 11 | BLE trigger position | OPEN | Trigger-finger reach adjustable |
| 12 | IMU position | OPEN | Rigidly coupled to the phone clamp |
| 13 | Calibration references | Proposal | Datum faces on the phone clamp for repeatable phone placement; optional fiducial for the front camera (eye-tracking research, D-011 O2) |
| 14 | Adjustable parameters | Proposal | Grip-angle insert, palm shelf, trigger reach, pull weight, ballast mass and position |
| 15 | Manufacturing tolerances | OPEN | Measure printed parts; typical FDM ±0.2–0.3 mm is an ASSUMPTION |

Envelope reference: the ISSF measuring box for 10 m air pistols is 420 × 200 × 50 mm (Pistol Rules 8.12 — VERIFIED).
SIGHTLINE is not a competition pistol and need not fit it, but the box is a useful proportion reference.

## 2. Appearance and legal caution

Rules on imitation firearms vary by country and were **not researched this session** (UNVERIFIED, including
Bangladesh). Until checked, the design target is an object that cannot be mistaken for a firearm: bright colour,
no barrel-like tube or muzzle, the phone visibly mounted, and a moulded marking "TRAINING INSTRUMENT — NOT A FIREARM".
Check local rules before transporting or demonstrating prototypes in public.

## 3. Prototype path

| Stage | Purpose | Exit criterion |
|---|---|---|
| G0 geometry mule | Hold the reference phone repeatably; verify camera position and clamp repeatability | Phone re-seating changes p_b by < 0.05 px (measured) |
| G1 ergonomic prototype | Hand fit, grip angle range, trigger reach | User trials with ≥ 3 shooters; questionnaire + hold-stability baseline |
| G2 instrumented prototype | BLE trigger + IMU integrated | EXP-HW-1 passes |
| G3 research prototype | Mass/COM adjustable, calibration references | Mass and COM within targets; CAL-EXP-1..3 pass on the reference phone |

## 4. CAD gate after Mission 2 (2026-10-06): closed — no final grip CAD

Test devices named by the owner for the experiments: iPhone 15 and one Android phone. Whether the iPhone 15 is also
the **reference phone for the grip** is still an owner decision; E-004a may change the answer (a phone whose
stabiliser cannot be controlled or compensated is a poor reference).

| Quantity | Known now | Label | Still needed before CAD |
|---|---|---|---|
| iPhone 15 body | 147.6 × 71.6 × 7.80 mm, 171 g | VERIFIED from Apple's specification as quoted in the Mission 2 research report (Q1) | Caliper measurement of the actual unit, with and without case |
| iPhone 15 camera positions | Candidate coordinates read from the text of Apple's dimensional drawing; lens assignment and datum uncertain | UNVERIFIED interpretation (research report Q1) | Read the drawing visually; measure the phone |
| Camera keep-out cones | 121.83° and 75.55° (rear), diameters at cover glass 9.11 / 6.90 mm | VERIFIED text of the drawing (research report) | Confirm which lens is which |
| Materials near the camera/compass | No magnetic or permeable material in the marked areas; cases must not interfere with OIS | VERIFIED (drawing) / SECONDARY (guideline wording) | Check every fastener and insert against the keep-outs |
| Which camera the grip must leave unobstructed | Unknown: Main, Ultra Wide or both depends on E-004a | UNVERIFIED | E-004a |
| Re-seating repeatability requirement (< 0.05 px, G0) | Not measured | UNVERIFIED | E-002 re-seating clip, then a G0 mule |
| Android phone dimensions and camera position | Model not recorded | UNVERIFIED | E-004b records the model; then measure |
| Eye-to-screen distance, sight geometry numbers | Not measured | ASSUMED (700 mm in examples) | E-006 |
| Gyroscope axis convention relative to the phone body | Not measured | UNVERIFIED | CAL-EXP-6 axis logs |
| Mass and centre-of-mass targets | ≤ 1500 g limit VERIFIED; working band ASSUMED | — | Component masses |

A jig for E-004a (board, two rods, shims) is an inert laboratory fixture, not a grip prototype.
