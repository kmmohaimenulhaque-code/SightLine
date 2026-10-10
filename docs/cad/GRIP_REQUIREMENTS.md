# Passive Training Grip — Requirements and Freeze List (Mission 3 G0 implemented)

The grip is a **non-functional, passive holder** for a phone, a BLE trigger switch and optional sensors. It is not a
copy of a commercial air pistol and contains no barrel, no pressure system and no launching mechanism. Parametric CAD
(in `cad/parametric/`) is the source of truth; STL/STEP files are generated outputs. G0 is implemented as a geometry
and interface prototype. Physical fit, printer capability, mass, COM, inertia, ergonomics, camera repeatability and
final device support remain open.

## 1. Freeze list (must be complete before final CAD)

| # | Item | Current status | Evidence / note |
|---|---|---|---|
| 1 | Phone model(s) | **G0 nominal iPhone profile; Android placeholder; final support OPEN** | iPhone 15 profile exists; Android model still unrecorded; E-004a remains relevant to optical support |
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
| 14 | Adjustable parameters | **G0 implemented for X/Z ballast; ergonomics/trigger OPEN** | Captive X carriage and centred vertical cassette exist in `cad/parametric/`; scale/lock accuracy pending coupon |
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
| G0 geometry mule | Hold the declared phone envelope, expose hard datums, retain safely, and provide a repeatable test fixture | Regenerable assembly + physical fit/retention/pose trial prepared; optical result is reported separately, not implied by CAD |
| G1 ergonomic prototype | Hand fit, grip angle range, trigger reach | User trials with ≥ 3 shooters; questionnaire + hold-stability baseline |
| G2 instrumented prototype | BLE trigger + IMU integrated | EXP-HW-1 passes |
| G3 research prototype | Mass/COM adjustable, calibration references | Mass and COM within targets; CAL-EXP-1..3 pass on the reference phone |

## 4. CAD gate after Mission 2 (2026-10-06): revised for G0

The previous gate was closed for final CAD because several camera and physical decisions were open. Mission 3 separates
G0 geometry from final optical and ergonomic release. E-004a is **not** a reason to avoid a preliminary mechanical phone
cradle. G0 can test fit, retention and seating before OIS behaviour is resolved. G1, G2 and G3 remain closed until their
physical evidence exists. See `docs/cad/CAD_GATE_AUDIT.md`.

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
| Re-seating repeatability requirement (< 0.05 px, G0) | Not measured; retained as an aspiration, not a CAD pass criterion | UNVERIFIED | E-002 re-seating clip, Metric A/B trial on the G0 mule |
| Android phone dimensions and camera position | Model not recorded | UNVERIFIED | E-004b records the model; then measure |
| Eye-to-screen distance, sight geometry numbers | Not measured | ASSUMED (700 mm in examples) | E-006 |
| Gyroscope axis convention relative to the phone body | Not measured | UNVERIFIED | CAL-EXP-6 axis logs |
| Mass and centre-of-mass targets | ≤ 1500 g limit VERIFIED; working band ASSUMED | — | Component masses |

A jig for E-004a (board, two rods, shims) is an inert laboratory fixture, not a grip prototype.

## 5. Mission 3 G0 implementation

Implemented files and checks:

* `cad/parametric/assembly.json` — common chassis, grip, adapter interface, X/Z ballast and optional mounts;
* `cad/parametric/phone_profiles/iPhone15.json` — nominal iPhone 15 profile with explicit unmeasured camera fields;
* `cad/parametric/phone_profiles/placeholder_android.json` — dimensionally different placeholder pathway;
* `scripts/generate_cad.py` — deterministic source-driven ASCII STL and faceted exchange export with mesh/capture checks;
* `scripts/cad_mass_properties.py` — weighted COM, transformed inertia and feasible ballast search;
* `tests/test_cad_generation.py` and `tests/test_cad_mass_properties.py` — automated G0 checks.

The implementation status is **MODEL OUTPUT / G0**, not a physical validation result. The exact remaining tasks are in
`docs/cad/PHYSICAL_VALIDATION_PLAN.md`.
