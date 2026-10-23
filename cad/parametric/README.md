# cad/parametric — the editable CAD source (source of truth)

Scripted parametric CAD on CadQuery 2.8 / OpenCASCADE (FreeCAD is not required; every STEP export opens in it).
Everything in `cad/exports/` and `cad/drawings/` is generated from here — never edit generated files.

```
parameters/g0.json          every dimension: value, unit, status, note (single source of truth)
phone_profiles/*.json       one file per phone model (docs/cad/PHONE_COMPATIBILITY.md)
configurations/*.json       assembled configurations: profile + ballast settings + options
configurations/targets/     mass targets (LP 10 references, a demonstration target)
sightline_cad/              params (derived values), profiles, frames, parts, assembly, statics, massmodel,
                            checks, coupons, export, drawings
build.py                    regenerates everything
```

## Regenerate

```bash
pip install -e ".[cad]"                       # cadquery, trimesh, matplotlib (+ numpy)
python -m cad.parametric.build                # every configuration: checks, STEP/STL (verified), drawings, reports
python -m cad.parametric.build --config cad/parametric/configurations/g0_iphone15.json
python -m cad.parametric.build --no-export --no-drawings --quick        # checks only, about 1 min per configuration
python -m pytest tests/test_cad_g0.py         # regeneration and parameter-change tests (skipped without CadQuery)
```

Exit code 1 if any check fails or any export does not verify.

## Change something

* **A dimension**: edit `parameters/g0.json` (keep the status honest: MEASURED only for measured values), rebuild,
  read `cad/exports/<config>/checks.md`.
* **Fits from the coupons**: the `CALIBRATE` entries (`process.fit_*`, `coupling.socket_gap`, `platform.tenon_gap`).
* **The grip**: `grip.size_scale` (S 0.94 / M 1.00 / L 1.06), `grip.hand` (right / left), `grip.backstrap_offset`,
  `grip.length` (heel-rest height), `grip.rake_deg`, `grip.thumb_rest`, `grip.heel_rest` (`docs/cad/ERGONOMIC_GRIP.md`).
* **A phone**: add a profile and a configuration (`docs/cad/PHONE_COMPATIBILITY.md` §5).
* **A ballast setting**: the configuration's `ballast` block, or ask the solver
  (`python scripts/cad_mass_properties.py solve …`).
* **Measured masses**: `cad/measurements/component_mass.csv` → `scripts/cad_mass_properties.py measured`.

Frames, subsystems and every check: `docs/cad/CAD_DESIGN_REPORT.md`. Generated parameter reference:
`cad/exports/PARAMETERS.md`; generated part list: `cad/exports/PARTS.md`.

## G1 (closer silhouette)

G1 is a separate generator with its own parameters, so the G0 outputs above are not touched:
`sightline_g1/` (geom, assembly, checks, solver, render, build), `parameters/g1.json` and
`configurations/g1/*.json` (G1-IP15-RH reference, G1-IP15-LH mirrored grip, G1-AND163-RH placeholder Android).

    python -m cad.parametric.sightline_g1.build          # checks, mass reports, STEP/STL, renders → cad/exports/g1, docs/cad/renders/g1
    python -m cad.parametric.sightline_g1.build --quick  # static checks + mass only
    python -m pytest tests/test_cad_g1.py

Design notes and evidence status: `docs/cad/G1_DESIGN.md`.
