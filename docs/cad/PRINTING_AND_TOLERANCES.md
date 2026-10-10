# Printing and Tolerances

## 1. Process assumptions

The G0 source is designed for a normal consumer FDM printer, but the repository does not contain a measured printer/material capability. The following are starting recommendations, not guarantees:

| Part | Suggested material | Orientation | Critical features | Supports / post-process |
|---|---|---|---|---|
| Common chassis | PETG or tough PLA+ | broad support face on bed | adapter plane, shoulders, screw bosses, rail capture | avoid support on datum plane; deburr and flatten only if measured |
| Grip body | PETG or PLA+ | grip long axis Z if layer direction permits; use brim if needed | wall thickness, backstrap interface, hand edges | light supports; round/deburr user surfaces |
| Phone adapter | PETG/nylon preferred for repeated service | back plate flat on bed | lower/lateral datums, camera opening, retainer slots | protect datum faces from support scars |
| Retainers and pads carrier | PETG/nylon | slide direction parallel to layer-safe axis | captive capture, screw holes, pad seat | coupon first; replace compliant pad rather than sanding precision faces |
| X ballast rail/carriage | PETG/nylon with metal screw/insert interfaces | rail floor on bed | capture lip, end stops, lock boss, sliding fit | coupon first; do not rely on bare printed threads for repeated locking |
| Z cassette/track | PETG/nylon | track back on bed | capture lip, cassette travel, end stops | coupon first; verify no warp closes the channel |
| Fiducial/optional mounts | PLA+/PETG | flat face on bed | marker plane and board hole spacing | low support; measure before camera calibration |

Use a bright orange/cyan scheme for the chassis and adapters. The upper rear phone region must remain visibly open. Add the non-firearm marking on the physical print.

## 2. Fit coupons before full prints

Print `cad/measurements/retainer_slider_coupon.csv` as a design record and create the corresponding simple coupon from the same material, nozzle, layer height and orientation. The coupon should test:

* nominal 0.3, 0.5 and 0.7 mm sliding gaps;
* the retainer pad seat;
* the M4-scale hole/insert choice;
* X carriage capture lip and end-stop engagement;
* Z cassette capture and lock.

Measure free travel, lock slip, backlash, insertion force and wear after 50 cycles. Enter the selected gap into the configuration only after that test.

## 3. Dimensional rules

* The 0.5 mm slide clearance in `assembly.json` is a starting design parameter, not a guaranteed tolerance.
* Soft pads are replaceable contact material and are excluded from hard-datum precision until their compression/return is measured.
* Do not sand a datum face until the amount removed is recorded; otherwise the adapter-to-chassis transform is no longer traceable.
* Heat-set insert holes must use the chosen supplier's dimensions and a test coupon. Do not assume a generic “M4 insert” is interchangeable.
* Keep any metal fastener, insert or weight away from unmeasured phone camera/compass/IMU keep-outs.

## 4. Likely failure modes

Warped adapter planes, elephant-foot at the phone datums, layer separation at lock bosses, creep in a loaded PETG rail, pad compression, loose inserts, screw head interference and weight rattle are expected prototype risks. Each must be inspected and recorded before a phone is installed.

The G0 generator checks digital mesh closure and envelope/capture logic. It cannot check layer adhesion, dimensional drift, material creep, actual strength or safe phone contact.
