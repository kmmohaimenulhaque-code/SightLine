# cad/parametric

This directory is the editable G0 source of truth for the passive SIGHTLINE
training chassis geometry. It is deliberately a geometry mule: phone body
dimensions, camera centres, case fit, material, fasteners, mass, COM, print
tolerances, strength and reseating repeatability are not claimed as measured.

* `assembly.json` contains units, axes, envelope, design dimensions, required
  component roles and the bright, non-firearm appearance constraints.
* `phone_profiles/*.json` contains replaceable phone envelopes. `iPhone15.json`
  uses the nominal dimensions recorded in `docs/cad/GRIP_REQUIREMENTS.md`;
  `placeholder_android.json` is explicitly an unmeasured placeholder.
* `configurations/*.json` selects a profile and optional mounts/ballast poses.
* `configurations/*_mass.json` is the evidence-labelled mass/COM/inertia input
  for `scripts/cad_mass_properties.py`; it is separate from geometry so a CAD
  estimate cannot be mistaken for a measured part mass.

Generate all derived exports from the repository root:

```sh
python scripts/generate_cad.py --config cad/parametric/configurations/iphone15_g0.json
python scripts/generate_cad.py --config cad/parametric/configurations/placeholder_android_g0.json
python scripts/generate_cad.py --config cad/parametric/configurations/iphone15_g0.json --validate-only
```

The dependency-free generator writes deterministic ASCII STL components,
faceted BREP STEP files, and `manifest.json` under `cad/exports/<config-id>/`.
Generated files are never edited by hand. The coordinate system is X
targetward, Y lateral and Z vertical. The design has no barrel, muzzle,
pressure system or launching mechanism; the phone remains visibly mounted and
the upper rear camera region is left open without inventing camera coordinates.

The JSON profile fields for camera centres, protrusion, buttons, case and
calibration are intentionally allowed to be `null` with an evidence status.
That is preferable to silently converting a drawing interpretation into an
optical compatibility claim.
