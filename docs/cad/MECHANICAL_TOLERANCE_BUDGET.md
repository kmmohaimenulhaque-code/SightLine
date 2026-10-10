# Mechanical Tolerance and Repeatability Budget

**Status:** preliminary feasibility budget; values marked `ASSUMED` are not guaranteed printer capability.  
**Purpose:** identify what must be measured before making a pose or optical repeatability claim.

## 1. Coordinate and repeatability definitions

All geometry is in the right-handed chassis frame:

* X targetward;
* Y lateral;
* Z vertical;
* origin at the underside of the chassis, on its centreline.

**Mechanical pose repeatability (Metric A)** is the change in the phone/adaptor rigid pose relative to this frame after removal and reinstallation. It must be reported as translations and rotations with the instrument and measurement uncertainty stated.

**Observed optical repeatability (Metric B)** is the image-registration displacement after the same phone is removed/reinstalled under a fixed camera mode, target, distance and focus. It is not interchangeable with Metric A.

## 2. Preliminary contributors

| Contributor | G0 value / allowance | Status | How to resolve |
|---|---:|---|---|
| Nominal iPhone 15 body dimensions | 147.6 × 71.6 × 7.8 mm | Manufacturer nominal; actual unit unmeasured | Caliper at ≥5 locations; record max/min and case fit. |
| Android dimensions | 165 × 78 × 9 mm | Placeholder only | Select device and measure. |
| Printed hard-datum dimensional capability | ±0.2–0.3 mm | Assumption inherited from old freeze list | Print coupon in the selected material/orientation and measure 10 features. |
| X/Z slide clearance | 0.5 mm | G0 design parameter | Measure free travel, lock slip and backlash on the actual printed pair. |
| Soft pad thickness | 2 mm | Design allowance, not a precision datum | Measure compression/return and keep it outside the datum stack unless characterised. |
| Anti-lift retainer gap | Profile-dependent nominal clearance | Model output | Check safe retention and screen/case load physically. |
| M4-scale fastener placeholder | 4 mm nominal hole representation | Unverified | Select screw/insert, use supplier dimensions and pull-out test. |
| Adapter/chassis registration | Printed support plane and shoulders | Model output only | Dial indicator/CMM/photogrammetry on repeated adapter installs; consider metal pin/bushing if needed. |
| Camera centre in body | `null` for both current profiles | Unverified | Measure selected lens centre and protrusion. |
| Optical registration uncertainty | 0.05 px aspiration retained | Unverified aspiration | E-002 / reseating trial with an uncertainty budget. CAD cannot pass it. |

## 3. Proposed measurement stack

The first physical stack should be measured in this order:

1. Measure the printed adapter's datum faces and chassis interface with calipers or a height gauge.
2. Install/remove the adapter at least 30 times, recording translational and angular pose against a reference fixture.
3. Install/remove the phone at least 30 times, using the same retainers and pads.
4. Weigh pad and retainer assemblies separately; inspect for compression or creep.
5. Repeat the phone trial after 50 adjustment cycles and inspect wear.
6. Only after Metric A is recorded, capture a fixed target and calculate Metric B.

The sample count is a proposed G0 validation method, not an achieved result. Use a larger sample if the observed distribution is non-Gaussian or if a 95th/99th percentile decision is needed.

## 4. Optical criterion assessment

The previous `<0.05 px` requirement is not deleted, but it is not accepted as a mechanical tolerance. A pixel displacement depends on focal length/readout, crop, registration algorithm, target distance, focus and image processing. The camera/measurement system's repeatability must be smaller than the criterion to claim it.

The acceptance record must report trial count, mode/resolution, target, distance, focus/exposure/stabilisation settings, registration estimator, mean, standard deviation, percentile, maximum and estimator uncertainty. Focus changes, crop changes, OIS/EIS and codec repetition are failure/warning conditions.

## 5. Acceptance rule for this budget

This budget is complete when every `ASSUMED` row has a measured value or a documented reason to remain open, and when the mechanical pose and optical results are recorded separately. Until then, the G0 exports may be printed as a geometry prototype but no pose or 0.05 px claim is valid.
