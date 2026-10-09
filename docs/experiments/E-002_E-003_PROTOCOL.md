# E-002 / E-003 — Physical protocol: real target capture and the synthetic → real gap

Status: **PHYSICAL_DATA_REQUIRED**. Harnesses: `ml/evaluation/e002_static_capture.py`, `ml/evaluation/e003_domain_gap.py`.

## Setup

* Print `docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf` at 100 %. Measure and record: black diameter, the
  150 mm and 100 mm bars, printer and paper. Do not assume the printer's scale is right.
* Target flat on a plain wall. Phone on a tripod or wedged on a table, **10.00 m** from the target face (tape
  measure; record the uncertainty). Lens at target height, target near the image centre.
* Lighting: record what it is; lux at the target if a meter (or a light-meter app, stated as such) is available.
* Camera settings as in the E-004a protocol §3: stabilisation Off, HDR off, focus/exposure/white balance locked,
  3840×2160 at 30 fps, HEVC.

## Captures

Three repeats of a 30 s clip, nothing touched, for each configuration available:

| Configuration | Note |
|---|---|
| iPhone 15 Main 1× | |
| iPhone 15 Main 2× | separate condition; record `zoom_readout` as UNKNOWN unless measured |
| iPhone 15 Ultra Wide | |
| Android phone, each rear camera | settings as close as the app allows; record them |
| (optional) H.264 instead of HEVC; 1080p | to see what the codec and resolution change |

Re-seat nothing between repeats 1–3; then remove and replace the phone once and record a fourth clip (shows how much
re-seating moves the image — needed later for the grip).

## Analysis

```sh
python -m ml.datasets.capture new --experiment E-002 --test static --video <clip>      # then fill in and validate
python -m ml.evaluation.e002_static_capture analyse --capture <manifest.json> --video <clip>
python -m ml.evaluation.e002_static_capture table ml/evaluation/results/E-002/*
python -m ml.evaluation.e003_domain_gap analyse --capture <manifest.json> --video <clip>
```

E-002 reports, per configuration: mean, standard deviation, RMS, p95, maximum, drift and spectrum of the measured
centre — in pixels, milliradians and millimetres at the target — plus the share of exactly repeated positions (a
sign that the video encoder is copying picture content between frames, which makes the scatter look smaller than
the sensor's).

**E-002 measures precision, not accuracy.** A constant offset of the estimated centre cannot be seen in a static
clip. Accuracy needs known displacements (E-004a steps) or a second, independent measurement.

E-003 puts measured image properties (edge blur, halo, contrast, temporal noise and its frame-to-frame correlation,
blocking) beside the same measurements on a matched synthetic clip. It lists the difference and stops there:
whether a difference matters is decided by re-running E-001 with the measured value. The generator is not changed
just because real video looks different.

**Is 2× a crop or an upscale?** Compare the equivalent edge sigma in millimetres at the target (sigma in px × mm/px)
between 1× and 2×: about half ⇒ the sensor is read at finer pitch; about equal ⇒ digital enlargement. Record the
outcome in `zoom_readout`; until then it is UNKNOWN.
