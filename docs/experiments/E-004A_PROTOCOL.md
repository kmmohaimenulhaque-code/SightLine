# E-004a — Physical protocol: does the iPhone 15 image follow a known rotation?

Status: **PHYSICAL_DATA_REQUIRED**. Harness: `ml/evaluation/e004a_ois_transfer.py`. Geometry: `app/calibration/angular.py`.
Nothing in this document is a result.

**Question.** With stabilisation set to "Off", does the Main camera's image move by `f_px · θ` when the phone rotates
by a known small angle θ — like the Ultra Wide camera (no OIS listed by Apple) should?

**What each test can and cannot show** (the synthetic sanity run demonstrates the second point):

| Test | Ground truth | Shows | Cannot show |
|---|---|---|---|
| A static | none needed | noise floor, drift, codec behaviour | anything about stabilisation |
| B step, C ramp | lever geometry | the *settled* response; a stabiliser that holds its correction; slow re-centring (creep) | a stabiliser that cancels fast motion and then re-centres reads exactly like "no stabiliser" here |
| D oscillation | independent gyroscope | response per frequency band, 0.5–14 Hz — **the decisive test** | response below ~0.5 Hz (gyro drift) |

## 1. Equipment (no laboratory needed)

* iPhone 15; a camera app with manual control and a stabilisation switch (the research report identified Blackmagic
  Camera; write down the app and version you use).
* Printed target `docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf`, printed at 100 %. Measure the black's
  diameter and both bars with a steel rule (read to 0.5 mm, or better with calipers).
* A stiff board 45–100 cm long (shelf plank, aluminium level). It must not flex when you press its end.
* Two straight round rods (metal rods, dowels, new pencils), tape, a steel rule or tape measure.
* Shims of known thickness: feeler gauges if available; otherwise printer paper — measure a stack of 100 sheets and
  divide (state the uncertainty: e.g. 10.0 ± 0.5 mm → 0.100 ± 0.005 mm per sheet).
* For test D: the Android phone running the SIGHTLINE probe app (button 5), fixed to the same board.
* Passive, inert parts only. No mechanism of any other kind is involved (SAF-01).

## 2. The lever jig

```
   target on the wall  <----------- L (measure) ------------ phone lens
                                                               |
   front rod F (taped under the board)                         v
        |                                              [phone, on its long edge, lens over P]
   =====o=========================== board ====================o=====
        ^ shims go here                                        ^ pivot rod P (taped to the table)
        |<--------------------- r (measure) ------------------>|
```

* The board points at the target. The pivot rod P is taped to the table across the board near its back end; the
  board rests on it. The front rod F is taped under the board near its front end and rests on the table.
* Clamp the phone on the board **directly above the pivot rod**, on its long edge, rear cameras toward the target.
  Reason: a lens that sits ahead of the pivot also moves sideways when the board tilts, which adds parallax: 300 mm
  ahead at 5 m is a 6 % error. Measure how far the lens is ahead (+) or behind (−) of the pivot line, ±5 mm; the
  analysis corrects for it.
* `r` = distance between the two rod centre lines. Measure on both edges of the board and average; state ±1 mm.
* Raising the front rod by a shim of thickness `d` tilts the board by `θ = atan(d / r)`.

| r | 0.1 mrad | 0.25 mrad | 0.5 mrad | 1 mrad | 2 mrad |
|---|---|---|---|---|---|
| 400 mm | 0.04 mm | 0.10 mm | 0.20 mm | 0.40 mm | 0.80 mm |
| 1000 mm | 0.10 mm | 0.25 mm | 0.50 mm | 1.00 mm | 2.00 mm |

With paper (≈0.1 mm) and r = 400 mm the reachable set is ≈0.25, 0.5, 1, 2 mrad (1, 2, 4, 8 sheets). 0.1 mrad needs a
1 m board or a 0.04 mm feeler gauge. **Use what you can actually build and record the real values** — the target
angles are a wish list, not a requirement. Expected image motion for planning:
`ml/evaluation/results/E-004a/expected_displacements.md` (DERIVED).

## 3. Scene and camera settings

* Target flat on a wall at lens height, 3–5 m from the lens (measure L to ±10 mm). Even, bright light.
* Record for **each** of: Main 1×, Ultra Wide; and Main 2× as a separate condition (do not assume what 2× is).
* Stabilisation **Off**. HDR / Dolby Vision **off** (SDR, Rec.709) — the analysis rejects HDR files.
* 3840×2160, 30 fps (60 fps for test D), HEVC, highest quality the app offers.
* Focus: focus on the target, then lock; note the lens-position number. Exposure: fixed shutter (1/100 s suits 50 Hz
  mains lighting), fixed ISO chosen so the white paper is bright but not clipped; white balance locked.
* Do not touch the phone, board or table while a still interval is being recorded. Start/stop with a remote or the
  volume button on a cable if you have one; otherwise wait 5 s after touching.

## 4. Tests (repeat each for every camera; same settings, same jig)

**A — static, 30 s.** Nothing moves.

**B — steps.** One continuous clip: 5 s still (no shim) → lift the board front gently, slide shim 1 under the front
rod, release → 5 s still → shim 2 → … Use cumulative stacks (e.g. 1, 2, 4, 8 sheets). Write the stack used at each
level. At least 3 levels plus the baseline.

**C — slow ramp.** One clip: 5 s still (no shim) → slide a "staircase" of sheets (each sheet set back 10 mm from the
one below) under the front rod slowly, taking about 10 s to reach the full stack → 10 s still on the full stack.
Enter two levels in the manifest: 0 and the full stack. The analysis checks the end point and whether the image
creeps while the mechanism is still.

**D — oscillation (decisive).** Fix the Android phone flat on the same board with tape so that it cannot shift
(same rigid body ⇒ same angular velocity, wherever it sits). Start the probe's button 5 (60 s gyro log). Start the
iPhone recording at 60 fps. Tap the board sharply three times (gives both records a common landmark). Then for about
30 s press the front of the board up and down by hand with small, varied movements — slow (about once a second) to
as fast as you can (several times a second) — keeping the target in view. Stop the video; save the gyro CSV.
The hand is only the excitation: the gyroscope is the ground truth, and frequencies are measured from the data, never
assumed.

## 5. Files and manifests

For every clip: `python -m ml.datasets.capture new --experiment E-004a --test B_step --video <clip>` writes a template
with what the file itself reveals. Fill in every `null` (device, iOS version, app, settings, distance, measured black
diameter, jig numbers; for D the gyro file and its sha256). `UNKNOWN` is allowed only for the fields listed in
`ml/datasets/capture.py`. Raw video is not committed — the manifest carries its checksum.

```sh
python -m ml.datasets.capture validate <manifest.json> --video <clip>
python -m ml.evaluation.e004a_ois_transfer analyse --capture <manifest.json> --video <clip>
python -m ml.evaluation.e004a_ois_transfer compare ml/evaluation/results/E-004a/<main run> ml/evaluation/results/E-004a/<uw run> ...
```

## 6. What invalidates a run (reported as INVALID, never patched)

More than 5 % unusable frames · number of still intervals found ≠ number of levels in the manifest · checksum
mismatch · HDR file · the Ultra Wide control not reproducing the expected motion (then the jig, not the phone, is in
question) · for D, no frequency band with enough motion.

## 7. Reading the result

Scope every statement to: iPhone 15 + the iOS version tested + the camera + the capture configuration. The comparison
table applies fixed, written-down rules (`ml/configs/e004a.json`, thresholds ASSUMED). One experiment on one phone is
not a statement about iPhones.
