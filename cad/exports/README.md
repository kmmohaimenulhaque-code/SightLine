# cad/exports

Generated outputs (ASCII STL, faceted STEP and JSON manifests). Never edit by
hand; regenerate from `cad/parametric/` with `scripts/generate_cad.py`.

Current example configurations:

* `iphone15_g0/` — nominal iPhone 15 G0 geometry and model mass report;
* `placeholder_android_g0/` — dimensionally different placeholder geometry and
  model mass report.

The STEP writer is deterministic and intended for a CAD-reader reopen check.
The current environment has no FreeCAD/OCCT installation, so native reopen is
still a physical/toolchain validation task rather than a passed claim.
