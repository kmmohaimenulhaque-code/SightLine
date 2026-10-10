# SIGHTLINE Mission 3 — G0 CAD Design Report

## 1. Result

Mission 3 implements a first practical, editable G0 mechanical prototype rather than another concept-only review. The design is a passive, bright-colour training instrument with a visibly mounted phone, a common chassis/grip, replaceable phone adapter geometry, captive ballast and a tested mass-property calculator.

The source of truth is:

```text
cad/parametric/assembly.json
cad/parametric/phone_profiles/*.json
cad/parametric/configurations/*.json
scripts/generate_cad.py
scripts/cad_mass_properties.py
```

Generated exports under `cad/exports/` are disposable and are not edited by hand.

## 2. What the old gate got right / what changed

The old freeze list correctly kept camera coordinates, OIS behaviour, physical fit, COM, printer tolerances, ergonomics and hardware integration open. It also correctly prohibited firearm-like mechanisms and unsupported optical claims.

It was too restrictive to block **all** mechanical CAD until E-004a and every physical measurement had run. E-004a is relevant to the eventual camera measurement architecture, but not to whether a preliminary phone holder can be made. The revised gate opens G0 for a nominal mechanical adapter while keeping G1–G3 closed for physical and optical claims. Full evidence is in `CAD_GATE_AUDIT.md`.

## 3. Architecture

The common foundation contains:

1. broad common training chassis;
2. short broad grip body;
3. adapter interface with support plane, lateral shoulders and a longitudinal locating strategy;
4. removable model-specific phone adapter and open rear camera region;
5. adjustable retainers and replaceable pad placeholders;
6. X captive ballast guide, carriage, end stops, scale reference and lock placeholder;
7. centred vertical captive ballast track, cassette, end stops and lock placeholder;
8. passive fiducial mount;
9. optional IMU and BLE/input-device mounts;
10. fastener placeholders.

The model intentionally does not include a barrel, muzzle, pressure vessel or projectile-launching mechanism. The orange chassis and cyan adapter make the intended non-firearm role visible; the physical print should add the required training marking.

## 4. Device profiles and transforms

Implemented profiles:

* `iPhone15.json` — Apple iPhone 15 nominal body dimensions, 171 g manufacturer-nominal input, no measured case, camera coordinates/protrusion `null`. This is the complete first adapter path but is not an optically supported release.
* `placeholder_android.json` — deliberately unselected Android envelope for configuration testing. It is not a claim about any Android phone.

The profile transform chain is recorded as:

```text
PHONE BODY → PHONE ADAPTER → COMMON CHASSIS → GRIP DATUM
```

The current body-frame transform places the iPhone nominal envelope at X ≈ −51.9…−44.1 mm, Y ±35.8 mm, Z 16…163.6 mm. The camera centre is not fabricated; the upper rear region is left open until it is measured.

## 5. Datum and expected repeatability

G0 uses a printable 3-2-1-inspired scheme: one support plane, two lateral locating faces and one longitudinal stop, with accessible captive fasteners. Printed pins are not treated as precision-machine datums. If repeated mechanical pose variation exceeds the future requirement, the interface can receive a measured metal dowel/bushing pair without changing the grip or ballast system.

The expected repeatability is therefore a **test hypothesis**, not a numeric pass claim. The 0.05 px optical aspiration remains unverified and is evaluated only by Metric B after Metric A is measured.

## 6. Ballast operation

* X carriage: nominal 180 g stack, −20…+68 mm travel in the solver model, hard stops, capture lip, readable scale reference and positive lock placeholder.
* Z cassette: nominal 125 g stack, 24…84 mm travel in the solver model, hard stops, capture lip and positive lock placeholder.
* Lateral adjustment: not included as a moving axis. The vertical track is centred and the frame is symmetric for G0; a measured Y offset would justify paired symmetric trim weights rather than an arbitrary loose weight.
* Second independent X carriage: not included. The two-axis X/Z design covers the first known need with less part count and less backlash. It can be added if a measured inertia target cannot be reached with the current system.

The scale pitch and solver increment are indication/search values. Positioning accuracy, lock slip and backlash require a printed slider calibration coupon.

## 7. Modelled mass results

The mass solver reports the following `MODEL OUTPUT` using explicitly labelled estimates:

| Configuration | Total mass | Best mass residual to 1060 g | Attainable COM X range | Attainable COM Z range | Status |
|---|---:|---:|---:|---:|---|
| iPhone 15 G0 | 1058 g | −2 g | −8.27…+6.70 mm | 23.89…30.98 mm | Within provisional mass target; COM target unknown |
| Placeholder Android G0 | 1097 g | +37 g | −9.69…+4.75 mm | 28.78…35.62 mm | Outside provisional mass target; phone itself is unselected |

The total mass is constant as weights move because the first G0 model uses fixed installed stacks; moving the stacks changes COM and inertia. All inertia tensors are provisional point-mass/parallel-axis calculations until component inertias are supplied. No LP10 COM/inertia match is claimed.

## 8. Optical and OIS boundary

This CAD work does not assume that camera-axis alignment can disable or cancel OIS/EIS. E-004a remains the experiment that determines whether an iPhone camera configuration is usable for body-motion measurement. The mechanical adapter provides a repeatable seating path and calibration fiducial, while software retains device-specific zeroing and residual calibration.

## 9. Regeneration and exports

From the repository root:

```sh
python scripts/generate_cad.py --config cad/parametric/configurations/iphone15_g0.json
python scripts/generate_cad.py --config cad/parametric/configurations/placeholder_android_g0.json
python scripts/generate_cad.py --config cad/parametric/configurations/iphone15_g0.json --validate-only
python scripts/generate_cad.py --check-exports cad/exports/iphone15_g0
python scripts/cad_mass_properties.py --config cad/parametric/configurations/iphone15_mass.json
```

The generator validates watertight component meshes, positive volumes, declared roles, envelope bounds and captive-track sanity. The current environment has no native CAD kernel, so a FreeCAD/OCCT reopen check remains a release follow-up even though deterministic ASCII STL and faceted exchange files are generated.

## 10. Remaining work

The branch is complete for G0 implementation, not for a final research-prototype release. Physical fit, hardware selection, printer tolerances, masses, COM, inertia, pose repeatability, optical repeatability, OIS behaviour, ergonomics and legal review remain open as listed in `PHYSICAL_VALIDATION_PLAN.md`.
