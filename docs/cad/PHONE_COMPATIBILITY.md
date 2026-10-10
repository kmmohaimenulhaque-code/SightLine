# Phone Compatibility and Adapter Registry

## 1. Compatibility contract

SIGHTLINE does not call a phone “supported” because it fits in a loose clamp. A profile must pass three separately recorded levels:

| Level | Meaning | Evidence required |
|---|---|---|
| P1 — physical fit | The body and selected case fit the declared envelope without pressure on glass, buttons or camera island. | Manufacturer dimensions plus caliper check of the actual unit/case; adapter fit trial. |
| P2 — repeatable seating | Hard datum surfaces define the installed pose; retainers only preload the phone against those datums. | Re-seat trial, mechanical pose measurement and wear/rattle check. |
| P3 — calibrated optical operation | Selected camera has clear glass/FOV, a measured phone-to-chassis transform, an accepted camera mode and an optical repeatability result. | Camera survey, E-004a/E-004b where applicable, calibration record and optical trials. |

No profile in this branch has passed P2 or P3. The iPhone 15 is a nominal P1 geometry example; the Android entry is only a parametric envelope placeholder.

## 2. Registry

| Profile / adapter | Device | Body envelope (mm) | Case | Mass input | Camera data | Level | Status |
|---|---|---:|---|---:|---|---|---|
| `iPhone15` / `iphone_adapter` | Apple iPhone 15, 6.1-inch base variant; exact unit not recorded | 147.6 × 71.6 × 7.8 nominal | none selected; allowance 0 | 171 g manufacturer nominal; not weighed | Lens centre, protrusion and assignment unverified; upper rear region left open | P1 nominal only | G0 reference profile, not release-supported |
| `placeholder_android` / `android_adapter` | No Android model selected | 165 × 78 × 9 placeholder | none selected | 210 g in solver only; not a device value | Unknown | configuration test only | Not supported |

The machine-readable source is `cad/parametric/phone_profiles/`. Adding a new phone should normally require a new profile, a new adapter configuration and a calibration record, not a new grip body or ballast rail.

## 3. Adapter datum strategy

The device module uses:

* a broad back/support surface away from the camera island;
* lower and lateral hard stops to define the body location;
* an open upper rear region so the camera island is not used as an unmeasured datum;
* replaceable soft pads outside the precision datum function;
* adjustable lateral and anti-lift retainers that preload the device against the hard stops;
* a common interface plate that attaches to the chassis datum plane and locating shoulders.

Pad compression, friction and printed surface roughness are deliberately excluded from the claimed precision transform. If a future design needs a compliant pad as a datum, its compression/return uncertainty must be measured and added to the tolerance budget.

## 4. Camera and service clearances

The iPhone 15 profile records manufacturer-drawing field angles and cover-glass diameters from the existing Mission 2 research notes, but does not assign them to a lens or convert them into a body-frame keep-out cone. The CAD generator therefore leaves the upper rear body region open and records `camera_centres_mm: null`.

The adapter must not touch or cover:

* active camera glass, flash and the complete measured keep-out envelope;
* unsupported screen glass;
* side buttons and the connector;
* microphones and any sensor that the selected calibration uses.

These are design checks for the physical fit trial, not passed CAD-only claims.

## 5. Adding a second device

The placeholder Android example demonstrates the intended path:

1. Copy `placeholder_android.json` to a model-specific ID.
2. Replace the body, case, mass, camera and clearance fields with measured/provenanced values.
3. Set the phone-body-to-chassis transform and adapter ID.
4. Add/adjust only the adapter configuration dimensions; keep `assembly.json` and the grip/ballast interface unchanged unless an actual envelope conflict is demonstrated.
5. Regenerate the exports and run the CAD/profile/solver tests.
6. Run P1/P2 physical checks, then the relevant camera experiment before calling it P3.

## 6. Calibration metadata required per profile

Each released profile must store:

* exact device model, variant, OS and case;
* body/case dimensions and variation;
* phone mass and method;
* active camera and mode/resolution/crop;
* camera centre and orientation in the phone-body frame, with uncertainty;
* camera aperture/keep-out geometry;
* phone-to-adapter and adapter-to-chassis transforms;
* bore-pixel zeroing value and calibration date;
* OIS/EIS capability/evidence and whether the configuration is supported;
* P2 pose-reseat statistics and P3 observed optical repeatability statistics.

Until those fields are complete, the profile remains a G0 mechanical configuration and must not be presented as universal optical compatibility.
