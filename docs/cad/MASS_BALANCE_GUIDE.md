# Mass and Balance Adjustment Guide

## 1. What is being tuned

The solver separates three goals:

1. total mass;
2. centre of mass;
3. rotational inertia.

Moving a fixed ballast changes COM and inertia but not total mass. Adding/removing a measured weight changes total mass and also changes COM/inertia. Matching one number does not prove the other two.

## 2. Generate a candidate setting

Run the model before touching the printed assembly:

```sh
python scripts/cad_mass_properties.py \
  --config cad/parametric/configurations/iphone15_mass.json \
  --out /tmp/iphone15_mass.json
```

The report gives the best candidate for known targets, the residuals, every component's evidence class, the attainable COM ranges and any unknown target fields. It will report an infeasible target rather than invent a ballast mass.

The current nominal iPhone model predicts 1058 g with the fixed 180 g X stack and 125 g Z stack. That is a provisional model result, not a scale reading.

## 3. Physical adjustment procedure

1. Weigh the phone, case, adapter, chassis, grip, fasteners, electronics and each captive weight separately. Enter the measured values with the measurement record ID.
2. Install the selected phone and adapter. Confirm the adapter ID and case state.
3. Put the X carriage at the solver setting. Read the main scale; the printed scale is an indication only until calibrated.
4. Put the Z cassette at the solver setting and tighten its lock.
5. Verify the carriage/cassette cannot move under ordinary handling and that no weight rattles.
6. Weigh the complete assembly and measure COM using the method in `PHYSICAL_VALIDATION_PLAN.md`.
7. Record actual values and residuals; do not overwrite the model prediction.

## 4. Setting interpretation

The X carriage changes longitudinal balance most strongly. The vertical cassette changes height of COM and can also change inertia about X/Y. If the phone change creates a lateral offset, use symmetric measured trim weights or redesign the cassette interface; do not place a loose washer in a pocket and call it calibrated.

The current G0 design does not include a second independent X carriage. Add one only if a measured inertia target or a physically observed handling difference cannot be reached with the first X carriage plus Z cassette. A second carriage increases part count, lock checks, backlash and calibration work.

## 5. Reference caution

No verified LP10 COM or inertia target is stored. The provisional 1060 g value is a SIGHTLINE design point. Do not use the adjustment guide to claim LP10 equivalence or competition compliance.
