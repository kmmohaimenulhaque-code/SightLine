# SIGHTLINE CAD Gate Audit — Mission 3

**Audit date:** 2026-10-10  
**Branch:** `feature/universal-balanced-grip-cad`  
**Baseline:** `mission-2-experimental-validation` (`68fb7d6`)  
**Scope:** decide what must block a useful G0 mechanical prototype, without silently promoting a research dependency to a geometry freeze.

## 1. Executive decision

The previous Phase 7 gate was correctly conservative about **final optical support** and physical validation, but it was too broad for G0. It treated an unresolved iPhone OIS experiment, an unselected Android model, unmeasured camera coordinates and unmeasured ergonomics as reasons not to create any mechanical prototype.

Mission 3 changes the gate in three ways:

1. **G0 is open for geometry and interfaces.** It may use labelled nominal or placeholder dimensions, provided the exported parts are explicitly marked `MODEL OUTPUT` / `UNVERIFIED` and the open optical region is not described as camera-compatible.
2. **E-004a remains a gate for a camera-supported configuration, not for a phone cradle.** The preliminary adapter can test fit, retention and repeatable mechanical seating before the camera/IMU architecture is selected.
3. **G1–G3 remain closed for claims that require people, hardware or real camera data.** No sub-pixel, OIS, ergonomic, LP10-equivalence or physical mass claim is released by this CAD work.

## 2. Existing freeze list audit

| ID / exact meaning | Current status and evidence | Missing measurement or decision | Blocks | Minimum action to resolve | G0 decision |
|---|---|---|---|---|---|
| 1. Phone model(s) | The Mission 2 brief names iPhone 15 and one Android phone. Android model is not recorded. | Select the Android model. Decide whether iPhone 15 remains a supported camera configuration after E-004a. | G1 for a final phone matrix; G2/G3 for device-specific integration | Record model, variant, OS, case and camera modes in a profile. | **Does not block.** iPhone 15 has a nominal G0 profile; Android is a labelled placeholder. |
| 2. Phone dimensions | iPhone 15 nominal body `147.6 × 71.6 × 7.8 mm` is recorded from the Mission 2 research material. No unit/case caliper record exists. | Measure the exact phone and selected case. | G1 fit acceptance; G3 release | Add caliper record and enter permitted variation/case allowance. | **Does not block nominal geometry.** Blocks a production adapter. |
| 3. Camera position on phone | Candidate coordinates were read from a drawing but lens assignment and datum interpretation are unresolved. | Measure the selected lens centre and protrusion in the phone-body frame. | G2 optical integration; G3 calibration | Measure with a camera jig or manufacturer drawing plus verification; store uncertainty. | **Does not block G0.** G0 leaves the upper rear camera region open. |
| 4. Sight-axis geometry | The software bore ray through camera pixel `p_b` is defined in `docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md`; physical numbers remain open. | Define the measured camera-to-chassis transform and zeroing record after device choice. | G2/G3 instrument calibration | Fit a datum target, record transform, then zero in software; do not infer from appearance. | **Does not block.** The adapter interface and fiducial mount are provided. |
| 5. Grip angle | Adjustable insert was proposed; no reference value or user trial exists. | Choose a design range and test hand fit. | G1 ergonomics; G3 release | Print interchangeable backstraps/angle coupons and run the stated user protocol. | **Does not block.** G0 uses a broad evaluation grip and labels ergonomics open. |
| 6. Target geometry | ISSF target dimensions are verified in the existing validation register. | Actual print scale and target placement still need physical checks. | G2 optical test only | Measure the printed black diameter and distance for each test. | **Not a blocker.** |
| 7. Total mass target | `≤ 1500 g` is an ISSF pistol rule, not automatically a SIGHTLINE product requirement. The `0.95–1.20 kg` band and `≈1.06 kg LP10` value are design assumptions/secondary evidence. | Approve a SIGHTLINE design target and weigh the physical assembly. | G1 balance; G3 release | Keep the provisional 1060 g solver target separate from the rule limit; measure hardware. | **Does not block.** Solver exposes target and residual; no equivalence claim. |
| 8. Centre-of-mass target | Formula is known; no LP10 COM measurement and no SIGHTLINE target COM exist. | Obtain a reference measurement or explicitly set a user-approved target frame and tolerance. | G1/G3 mass-property matching | Measure reference and assembly by a documented method; populate target fields. | **Does not block.** Solver reports attainable ranges and leaves COM target `TBD`. |
| 9. Printer / material | PETG and PLA+ are candidates only. No printer/material coupon data. | Select printer, nozzle, layer height, material and measured fit clearance. | G0 fabrication repeatability; G1 durability | Print a retainer/slider coupon and measure clearance/wear. | **Does not block CAD generation.** Blocks claims about fit and lock force. |
| 10. Fasteners | Captive heat-set inserts are a proposal; thread and insert dimensions are not frozen. | Select standard fasteners and verify insert pull-out/clearance. | G0 physical assembly; G2 serviceability | Use the provisional BOM, then confirm with a hardware audit and coupon. | **Does not block source model.** Export placeholders are not hardware proof. |
| 11. BLE trigger position | Reach and mechanism are open; existing BLE work is a proposal. | Select a passive switch and evaluate finger reach. | G1 and G2 | Mount the selected input-only switch and run EXP-HW-1. | **Does not block.** A passive mount placeholder is included. |
| 12. IMU position | Rigid coupling is desired; axis convention and exact board are unverified. | Select module, mounting datum and axis mapping. | G2 | Add module dimensions, secure with screws/pocket, perform CAL-EXP-6 and axis check. | **Does not block.** Optional mount is clearly provisional. |
| 13. Calibration references | Datum faces and a fiducial plate were proposed. Camera relationship is unmeasured. | Define fiducial geometry, target and calibration procedure. | G2/G3 | Measure fiducial-to-chassis and camera-to-body transforms; keep OIS architecture conditional. | **Does not block.** Passive reference mount is present without optical claim. |
| 14. Adjustable parameters | Ballast mass/position, grip and trigger adjustments were proposed but not implemented. | Confirm travel, lock method and user adjustment workflow. | G0/G1 | Validate captive X and vertical mechanisms on printed coupons/parts. | **Resolved for G0 design.** X/Z mechanisms are implemented; performance is pending. |
| 15. Manufacturing tolerances | `±0.2–0.3 mm` was an assumption, not printer evidence. | Measure printer-specific dimensional capability and wear. | G0 fit repeatability; G3 release | Run coupon, record as-built dimensions, update tolerance budget. | **Does not block source.** It blocks precision/repeatability claims. |

## 3. Gate-by-stage status

| Gate | Meaning after this audit | Status | Evidence in this branch | Open blockers |
|---|---|---|---|---|
| G0 | Regenerable common chassis, one nominal device adapter, retention, ballast interface and checks | **OPEN / implemented as MODEL OUTPUT** | `cad/parametric/`, `scripts/generate_cad.py`, solver and tests | Physical print, fit, mass and slider checks |
| G1 | Human-factors prototype and balance adjustment tested by people | **CLOSED** | None; no participants or physical assembly | Print parts; measure grip angle/reach/comfort and record participants |
| G2 | Instrumented prototype with selected BLE/IMU and camera/IMU decision | **CLOSED** | Existing software architecture is conditional; hardware not selected | E-004a, E-004b, CAL-EXP-6, EXP-HW-1, mounting tests |
| G3 | Specific research configuration released with physical mass, COM, repeatability and optical evidence | **CLOSED** | No physical measurements in repository | All relevant physical and camera experiments; reference COM/inertia if equivalence is claimed |

## 4. Requirements deliberately not frozen

* `0.05 px` is retained as an **aspiration to investigate**, not an acceptance pass. A CAD constraint cannot measure image-registration uncertainty.
* The final camera choice remains conditional on E-004a and device capability results. The mechanical adapter must not be redesigned merely because that experiment is unfinished.
* The LP10 reference remains a handling and mass-property research reference. It is not copied, and its COM/inertia are not invented from a product photograph or total mass.
* The `0.95–1.20 kg` range is implemented as a provisional SIGHTLINE product-design target only. It is not an ISSF requirement and not evidence of LP10 equivalence.

## 5. Audit conclusion

The minimum action needed for useful work was to separate **mechanical fit** from **optical operation**. The branch therefore proceeds with an editable, bright, visibly phone-mounted G0 geometry mule, an iPhone 15 nominal profile, a second profile pathway and a real solver. It does not close any physical validation gate.
