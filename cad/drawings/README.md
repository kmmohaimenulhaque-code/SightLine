# cad/drawings

Dimensioned G0 interface drawings. These are communication drawings derived
from the editable JSON source, not inspection drawings and not a substitute for
as-built measurement. Dimensions marked nominal/design must be rechecked after
the printer, material, case and fasteners are selected.

* `assembly_g0.svg` — common chassis/grip/ballast envelope and axis datum;
* `iphone_adapter_g0.svg` — nominal iPhone 15 adapter envelope and datum concept.

Regenerate the solid exports with `scripts/generate_cad.py`. A future native CAD
workflow may replace these SVGs, but the JSON/Python source remains the source
of truth until a native model is adopted and checked in.
