# Mass and Balance Reference

**Status:** `PROVISIONAL` / `TBD`; no physical reference or trustworthy reference mass-property measurement is present.  
**Coordinate frame:** chassis frame, X targetward, Y lateral, Z vertical; origin at the underside of the common chassis centreline.

## 1. Reference configuration audit

The intended handling reference is the **Steyr LP10 classic 10 m pneumatic competition pistol**. The exact production year, grip variant, sight configuration and installed weight configuration are not recorded in the repository. The repository's earlier `≈1.06 kg filled` statement comes from a secondary Wikipedia entry (`S-10`) and is explicitly not treated as a manufacturer-verified value.

The manufacturer's public source was not successfully retrieved during this implementation run, and no LP10 is available for weighing. Therefore this design adopts **no LP10 mass, centre-of-mass or inertia value as verified data**.

| Quantity | Adopted value | Evidence class | Interpretation |
|---|---:|---|---|
| LP10 total mass | Not adopted | `UNVERIFIED` | Secondary ≈1.06 kg value remains a research lead only. |
| LP10 centre of mass | Unknown | `UNVERIFIED` | Must not be inferred from photographs, grip shape or total mass. |
| LP10 inertia tensor | Unknown | `UNVERIFIED` | Requires a measured rigid-body test or a trustworthy manufacturer/model data source. |
| ISSF 10 m pistol maximum | 1500 g | `VERIFIED` in existing S-02 citation | A competition limit, not a SIGHTLINE balance target. |
| SIGHTLINE G0 mass target | 1060 g nominal | `DESIGN_TARGET_ONLY` | Chosen as a provisional product-design point within the previously discussed band; it does not imply LP10 equivalence. |
| SIGHTLINE working band | 950–1200 g | `DESIGN_TARGET_ONLY` | Useful exploration band only; it is not an ISSF or manufacturer requirement. |

## 2. Component evidence policy

The solver distinguishes:

* `measured` — a physical item was weighed and the method/date/instrument are recorded;
* `manufacturer_specified` — a manufacturer value, not a measurement of the installed unit;
* `estimated` — CAD density, allowance or placeholder;
* `user_measured_or_entered` — an operator override supplied to the solver, which still needs a record;
* `unknown` — not usable for a release claim.

The iPhone 15 profile uses 171 g as a manufacturer-nominal input for the model. The current chassis, grip, adapter, hardware, electronics and ballast values are G0 estimates. The Android profile uses 210 g only in a clearly labelled placeholder mass model; it is not a selected device.

The difference between these values matters. A CAD density estimate can omit infill, shells, heat-set inserts, screws, adhesive, pads and ballast. A nominal phone mass can differ from the exact phone, case and accessories. Until those are weighed, the solver's total is a model output rather than an assembly measurement.

## 3. Target parameter model

Each configuration contains the following fields under `target`:

```json
{
  "reference_id": "NO_VERIFIED_LP10_MASS_PROPERTY_REFERENCE",
  "reference_mass_g": null,
  "target_mass_g": 1060,
  "target_com_mm": null,
  "target_inertia_tensor_g_mm2": null,
  "mass_tolerance_g": 10,
  "com_tolerance_mm": null,
  "inertia_tolerance": null,
  "status": "DESIGN_TARGET_ONLY"
}
```

`target_com_mm`, `target_inertia_tensor_g_mm2`, their tolerances and any LP10 reference value remain `TBD`. The solver accepts them when evidence is available and otherwise reports the attainable COM range. It never treats a missing target as zero.

## 4. What the current model says

The generated reports are reproducible model outputs from:

```text
python scripts/cad_mass_properties.py --config cad/parametric/configurations/iphone15_mass.json
python scripts/cad_mass_properties.py --config cad/parametric/configurations/placeholder_android_mass.json
```

With the provisional fixed weight stacks, the model totals are 1058 g for the nominal iPhone 15 configuration and 1097 g for the placeholder Android configuration. The iPhone model is within the provisional 1060 ± 10 g design target; the placeholder Android model is not. The X/Z positions change COM, not total mass. The reported X and Z ranges are not measurements and do not show LP10 matching.

The complete reports include the inertia tensor about the chassis origin and about the calculated total COM. Because component inertia tensors are not yet measured or supplied, those tensors currently contain only point-mass/parallel-axis contributions and are not a release-quality rotational-inertia prediction.

## 5. Measurement needed before a reference claim

1. Obtain the exact LP10 variant/configuration or an authoritative manufacturer data sheet.
2. Record installed accessories and adjustable weight settings.
3. Weigh the reference with a calibrated scale and uncertainty.
4. Measure COM in the same chassis coordinate convention, or document a transform from the reference fixture.
5. Measure inertia only if the project decides dynamic equivalence is necessary; otherwise mark it unknown.
6. Enter each adopted value, method and uncertainty into `cad/measurements/` and update this document without deleting the provisional history.
