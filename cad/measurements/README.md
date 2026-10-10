# cad/measurements

Physical measurements of printed prototypes (mass, centre of mass, tolerances).
Each completed record must retain instrument, calibration/resolution, date,
operator, uncertainty and the exact configuration/profile ID. Empty templates
are provided so a model output cannot be mistaken for a physical result:

* `phone_mass.csv` — exact device, case and scale reading;
* `component_mass.csv` — printed parts, fasteners, pads, electronics and weights;
* `adapter_fit.csv` — body/case fit, datum contact and clearance observations;
* `balance_measurement.csv` — total mass, support reactions and COM;
* `slider_calibration.csv` — X/Z travel, lock slip, backlash, force and wear;
* `reseating_trials.csv` — mechanical pose and observed optical repeatability trials.

Do not fill these with estimates. Use `value_status=measured` only after the
physical measurement has been performed.
