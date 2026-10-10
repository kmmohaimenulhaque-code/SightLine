# G0 Assembly Guide

This guide describes the passive training instrument prototype generated from `cad/parametric/`. It is an assembly and test sequence, not a claim that the printed parts have passed fit, strength or optical validation.

## 1. Parts

For the iPhone 15 configuration, generate:

```sh
python scripts/generate_cad.py --config cad/parametric/configurations/iphone15_g0.json
```

The output directory contains the common chassis, grip, interface plate, `iphone_adapter`, phone reference envelope, retainers, pads, fiducial mount, X/Z ballast parts, optional mounts and fastener placeholder exports. The phone reference envelope is not a part to print; it documents the nominal design envelope.

## 2. Hardware and preparation

The provisional BOM calls for M4-scale screws/inserts for the chassis and adapter, small captive steel weight stacks, compliant replaceable pad material and a selected passive BLE switch/IMU only if the optional mounts are used. Do not install sharp exposed weights or any energy-storage/launching mechanism.

Before assembly:

1. Deburr all printed edges and remove support material.
2. Check every part against the manifest bounds and inspect for cracked layers, voids or warped datum faces.
3. Print and fit the retainer/slider coupon before the full assembly.
4. Verify that the phone has no case unless the profile explicitly includes one.
5. Do not put screws, inserts or magnetic material into an unmeasured camera/compass keep-out region.

## 3. Mechanical assembly sequence

1. Place the bright chassis on a flat reference surface with the underside datum down.
2. Install the grip body and its selected fasteners. Keep the grip a passive hand support; do not add a barrel-like extension.
3. Install the adapter interface plate against the chassis support plane, lateral shoulders and longitudinal stop. Tighten only enough to seat the plate; the screw head must remain accessible.
4. Install the model-specific adapter module. Confirm that its rear camera opening remains open and that pads are replaceable.
5. Install the lower and side retainers. Set the phone-specific clearance so the retainer presses the phone toward the hard datums rather than bending the phone.
6. Install the passive fiducial mount outside the phone envelope. Its final marker position must be measured later.
7. Install the X ballast rail, carriage, capture lip and end stops. Insert the weight stack into the captive pocket and verify it cannot escape at either end.
8. Install the centred vertical ballast track and cassette. Verify that the cassette is captured through the entire travel and that its lock is accessible.
9. Install optional IMU/BLE brackets only after their actual board dimensions and fasteners are known.
10. Apply the marking `TRAINING INSTRUMENT — NOT A FIREARM` to the physical prototype.

## 4. Phone installation

1. Move the retainers to their open/service positions.
2. Place the phone against the lower, lateral and rear hard datums. Do not use the camera island, screen glass or a soft pad as the locating datum.
3. Close the retainers until the phone is retained without visible flex or button actuation.
4. Confirm connector, button, flash, microphone and camera clearance.
5. Record the adapter ID, phone profile, case state, ballast settings and a photograph in the fit template.

Removal is the reverse sequence. Do not drag the camera island across a printed surface.

## 5. Lock and inspection checklist

Before each use:

* both X end stops are present;
* the X lock is tight enough that a hand-motion check produces no audible shift;
* the vertical cassette is captured and its lock is tight;
* no weight can fall onto the phone or user;
* all adapter fasteners are present;
* the phone cannot touch unsupported screen glass, buttons or camera glass;
* the chassis remains a passive holder with no projectile or pressure mechanism.

Any looseness, rattle, pad tear or layer crack is a stop-use condition until recorded and repaired.
