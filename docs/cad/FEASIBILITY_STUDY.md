# G0 Mechanical Feasibility Study

**Status:** `MODEL OUTPUT` / `DESIGN DECISION`, not physical validation  
**Date:** 2026-10-10

## 1. Design question

Can one passive SIGHTLINE grip and balance chassis support a declared phone family without turning every phone change into a new grip, while retaining a credible path to repeatable optical calibration?

**Answer for G0:** yes, as a mechanical architecture. A common chassis with a replaceable phone adapter is practical. It is not yet evidence that every phone is optically compatible, that printed datums achieve a sub-pixel image criterion, or that the instrument matches an LP10.

## 2. Alternatives

| Alternative | Print cost / part count | Phone-change time | Compatibility | Rigidity | Calibration repeatability | Wear / maintenance | Decision |
|---|---|---:|---|---|---|---|---|
| Fully adjustable cradle with hard adjustable stops | One cradle, several slides and screws; lowest adapter count | 2–5 min after learning the stops | Broad body envelope, but camera islands and buttons create many conflicts | Fair; each slide is a compliance path | Depends on re-setting stops; poor auditability across users | High wear at printed slides and soft pads | Rejected as sole precision interface |
| Common adjustable cradle plus model-specific locator inserts | One mechanism plus small inserts/camera masks | 1–3 min | Good for a controlled family with similar orientation | Good if inserts have hard datum faces | Good when each insert has a documented transform | Inserts are replaceable; common mechanism still wears | Viable hybrid for later refinement |
| Common chassis plus replaceable precision phone adapter modules | One chassis, one module per supported device | <2 min with captive fasteners | Best controlled support; each module owns camera clearance | Best; module can use three datum pads and metal hardware | Best of the three; transform is stored per module | Module absorbs wear and is replaceable | **Chosen for G0** |

The chosen design still uses adjustable retainers on the device module. Retainers only provide retention force. The phone position is defined by the module's hard seating surfaces and the chassis interface, not by clamp friction.

## 3. Common interface decision

The G0 interface is a simple 3-2-1-inspired scheme suitable for FDM prototyping:

* **Primary:** broad adapter-interface support plane on the common chassis.
* **Secondary:** two lateral locating faces on the interface plate.
* **Tertiary:** a longitudinal shoulder/stop. Captive fasteners clamp the adapter against these features.
* **Positive attachment:** accessible M4-scale placeholder fasteners through the interface. Actual insert and screw selection remains open.
* **No printed precision dowel claim:** the first prototype does not claim machine-tool tolerance from printed pins. If the physical repeatability study requires it, add a metal dowel/bushing pair or a separately measured machined insert.

This is intentionally less ambitious than a kinematic metal coupling. It keeps the G0 printable and exposes the datum surfaces for measurement. The source model can later replace the fastener placeholders with a measured metal locating scheme without redesigning the grip or ballast rails.

## 4. Ballast feasibility

The first solver model uses two fixed-mass captive weights:

* **X carriage:** 180 g, nominal usable travel −20 to +68 mm, 4 mm model search increment. The printed track has hard end stops, a capture lip, a readable scale reference and a lock placeholder.
* **Z cassette:** 125 g, nominal usable travel 24 to 84 mm, 4 mm model search increment. The cassette is captive in a vertical track with upper/lower end stops and a lock placeholder.

These increments are **search/indication increments**, not claimed positioning accuracy. Actual accuracy depends on the printed fit, lock force, backlash, weight stack, scale calibration and wear. A lead screw is not included in G0 because the current problem is balance-range coverage, not sub-millimetre mass positioning. If a coupon shows creep or backlash that matters, a captured M6 lead screw or metal threaded insert is the next controlled upgrade.

The current design uses a centred vertical cassette rather than a one-sided weight. That avoids an unnecessary lateral COM offset. A lateral trim interface is therefore not required for the first chassis. If a measured phone/camera/module arrangement creates a meaningful Y error, add symmetric trim pockets or a paired carrier; do not solve it by hand-placing loose washers.

## 5. Geometry and manufacturing feasibility

The installed environment has Python 3.14 but no FreeCAD, OpenSCAD, Blender or CadQuery executable/module. The G0 source therefore uses a dependency-free deterministic Python generator with exact orthogonal solids, ASCII STL output and a faceted STEP-like export path. The editable authority remains JSON parameters and Python generation code; exports are disposable.

This is a practical way to produce and test a first prototype in the current repository, but it has limits:

* no native CAD-kernel fillets, shell validity or interference solver;
* no material assignment or CAD mass properties;
* STEP re-open must be checked in a CAD kernel before it is treated as a manufacturing interchange file;
* printed surfaces and camera clearances are not physically certified.

The first print should be a fit/clearance coupon before the complete chassis. See `docs/cad/PRINTING_AND_TOLERANCES.md`.

## 6. Compatibility levels

Every phone profile reports three separate levels:

1. **Physical fit:** body/case envelope can be placed in the adapter envelope. This is a model check until measured.
2. **Repeatable mechanical seating:** the phone contacts hard datums and can be removed/reinstalled without changing the adapter. This is a physical test, pending.
3. **Calibrated optical operation:** the active camera is unobstructed, the camera-to-chassis transform is measured, and the camera mode/OIS behaviour is accepted. This is pending E-004a/E-004b and optical repeatability trials.

The iPhone 15 G0 profile is level 1 by nominal geometry only. The Android profile is a level-1 configuration test placeholder, not a supported phone.

## 7. Feasibility conclusion

The architecture is feasible for G0 and has a credible path to a multi-device family. The correct claim at this stage is:

> SIGHTLINE has an implemented, editable, dependency-free G0 geometry mule with replaceable adapter profiles and captive balance mechanisms. No physical fit, mass, COM, optical or ergonomic claim has passed.
