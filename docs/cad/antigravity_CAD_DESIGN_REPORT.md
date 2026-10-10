A complete G0 design report covering:
1. Architecture: Common chassis + replaceable precision phone adapters + calibrated adjustable ballast
2. Subsystem A: Common grip/instrument chassis — 30×40×150mm core block with ergonomic handle at 105°, T-slot ballast rail at Z=-60mm, 3-2-1 locating pin interface (one 3mm primary, two 2mm orientation pins) on top face
3. Subsystem B: Phone adapter — mates via 3-2-1 pins (0.15mm clearance for FDM), form-fitting cradle per phone model with camera clearance cutout, soft retention pads on non-datum surfaces
4. Subsystem C: X-axis ballast carriage (120mm travel, T-nut captive in T-slot, locking screw, weight platform), Z-axis indexed weight positions at 3 heights (-90, -60, -30mm), lateral Y-axis deemed unnecessary (symmetric chassis, phone centred, camera offset <2mm lateral COM shift)
5. Subsystem D: IMU mount on chassis, BLE button mount on grip, alignment reference fiducial point
6. Coordinate system: X forward toward target, Y lateral, Z vertical up, right-handed, origin at adapter mating plane/centreline intersection
7. Transformation chain: PHONE BODY → PHONE ADAPTER → COMMON CHASSIS → GRIP DATUM
8. CAD toolchain: build123d (Python parametric solid modelling on OpenCASCADE), exports to STEP and STL
9. What works: modular architecture, mass solver, phone profiles
10. What's unproven: FDM tolerances, physical fit, optical repeatability
