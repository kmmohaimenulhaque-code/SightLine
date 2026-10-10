# Physical Validation Plan

All items below are pending until parts are printed and measurements are actually made. A model output, render or export check must not be copied into a physical-result column.

## 1. G0 geometry and interface

| Test | Method | Record | Exit evidence |
|---|---|---|---|
| Phone fit and safe retention | Install the exact phone/case; inspect screen, buttons, connector, flash, microphones and camera clearance | `phone_fit_record.csv` + photographs | Phone retained without contact damage or uncontrolled datum use |
| Printed dimensions | Caliper/height-gauge survey of datum faces, rail and bosses; record instrument uncertainty | `component_mass_and_dimensions.csv` | As-built dimensions compared with tolerance budget |
| Slider coupon | Cycle retainer/X/Z interfaces 50 times; measure clearance, lock slip, backlash, insertion force and wear | `slider_calibration.csv` | Selected clearance and lock method documented |
| Ballast retention | Invert/shake ordinary handling test with locks engaged; inspect captive path | `balance_measurement.csv` | No weight escape or rattle |
| Adapter change | Remove/reinstall adapter 30 times; verify accessible fasteners and datum seating | `adapter_fit_record.csv` | No damage, binding or inaccessible fastener |
| Mesh/export reopen | Open STL and STEP in an available CAD kernel; compare bounds and solids | `export_reopen_record.csv` | All intended solids reopen; current environment lacks a kernel |

## 2. Mass properties

1. Weigh phone/case with a calibrated scale; record resolution, calibration date and uncertainty.
2. Weigh every printed component after post-processing, every fastener/insert, pads, electronics and ballast separately.
3. Enter each value with source `measured` and a record ID; retain the original estimate in the configuration history.
4. Weigh the assembled configuration.
5. Measure COM using a two-support reaction-force method or a documented balance fixture. Repeat in X/Y/Z where possible and state the coordinate transform.
6. Compare measured mass/COM with the solver report. Inertia remains unknown unless a separate rigid-body test is performed.

## 3. Reseating and optical repeatability

**Metric A — mechanical pose:** use a fixed reference fixture, datum targets and a repeatable measurement instrument. Remove/reinstall the adapter and phone at least 30 times. Report translation/rotation mean, standard deviation, p95 and maximum with instrument uncertainty.

**Metric B — observed optical:** use the same phone, camera, mode, resolution, crop, focus/exposure lock, target, distance and registration algorithm. Capture repeated remove/reinstall trials. Report mean, standard deviation, p95, maximum, registration uncertainty, focus/crop changes, stabilisation state and codec warnings.

The existing 0.05 px value is an aspiration only. Do not mark it passed from CAD or a render. If it is below measurement-system uncertainty, propose a revised criterion and record the decision.

## 4. G1/G2/G3 follow-up

* G1: actual hand-fit trials, grip angle, wrist/finger clearance, reach, comfort, balance adjustment usability and participants recorded; the intended three-shooter trial has not happened in this branch.
* G2: selected BLE switch and optional IMU installed; communication, latency, axis convention, rattle and serviceability tested; EXP-HW-1 and CAL-EXP-6 results recorded.
* G3: phone-specific adapters and calibration datums released only after P1/P2/P3 evidence, measured masses/COM and any adopted reference target are complete.
