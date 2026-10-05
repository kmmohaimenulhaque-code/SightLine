# Calibration Strategy (multi-device)

Goal: SIGHTLINE behaves consistently across iPhone and Android devices with different sensors, focal lengths,
aspect ratios, resolutions, zoom pipelines and distortion. The key design insight is that **different outputs need
different calibrations**, and the score needs the least.

## 1. What each output depends on

| Output | Needs intrinsics (f_px, cx, cy, distortion)? | Needs other calibration | Basis |
|---|---|---|---|
| Score and shot position (mm on target) | **No** — the printed black is the local ruler | Bore pixel p_b fixed in the phone body (stabilisation off or compensated); overlay drawn at S(p_b) | D-003; `docs/science/COORDINATE_SYSTEMS_AND_SIGHT_GEOMETRY.md` §6 |
| Hold metrics in mm on target | No (target-anchored) | Frame timestamps; trigger-clock offset | D-003 |
| Hold metrics in angle (mrad) | Only target distance (≈10 m) — or f_px if the target is not visible | Distance | — |
| Unity-magnification display ("Fit to FOV") | Not with the target-anchored variant | Eye-to-screen distance (grip geometry), screen ppi | §5 of the geometry doc |
| Gyro ↔ image fusion, OIS detection | Yes: f_px | Gyro-to-frame delay, readout time | Karpenko et al. 2011 |

## 2. Methods

### 2.1 Planar-pattern intrinsic calibration (offline, per device and camera mode)
Zhang's method with a printed checkerboard/ChArUco pattern (OpenCV `calibrateCamera`). Calibrate per
*(device model, physical camera, capture resolution, frame rate, zoom ratio)*, because video modes crop or bin the
sensor. Lock focus near infinity first: focus breathing changes the focal length (CAL-EXP-5).

### 2.2 Platform intrinsics (online)
* iOS: per-frame 3×3 intrinsic matrix via `isCameraIntrinsicMatrixDeliveryEnabled` (iOS 11+, VERIFIED API). Whether
  it reflects OIS-induced principal-point motion is UNVERIFIED (part of CAL-EXP-1).
* Android: `LENS_INTRINSIC_CALIBRATION` and `LENS_DISTORTION` (VERIFIED keys); availability per device UNVERIFIED.
  `DISTORTION_CORRECTION_MODE` must be recorded, since the ISP may already undistort.

### 2.3 Gyro–camera self-calibration (online, ~10 s)
Karpenko et al. (2011) recover focal length, rolling-shutter readout time, gyro-to-frame delay and gyro drift from a
~10 s handheld clip with ~1 px reprojection error. SIGHTLINE variant: the printed target is the tracked feature, the
user "wobbles" the instrument for 10 s before a session. Outputs: f_px, time offset camera ↔ IMU, readout time —
and a **stabilisation check**: if image motion ≠ f_px × gyro rotation, OIS/EIS is active.

### 2.4 Target-anchored scale (every frame)
The black's ellipse gives the local image→target map (scoring). Combined with an assumed 10 m distance it also gives
f_px × (true distance / 10 m) — distance and print scale cannot be separated from one image of a circle.

### 2.5 Print verification (per printed target)
The user measures the black with a ruler (or the printed card carries a scale bar). Recorded as a print-scale
factor; prints outside 59.5 mm ± 0.5 mm (the ISSF tolerance) are flagged.

### 2.6 Zeroing (per user/session)
Default p_b = principal point. Optional user sight adjustment in fixed clicks.

## 3. Per-device calibration profile (schema draft)

```json
{
  "device_model": "string", "os_version": "string", "camera_id": "string",
  "mode": {"width": 1920, "height": 1080, "fps": 60, "zoom_ratio": 1.0},
  "intrinsics": {"fx": 0, "fy": 0, "cx": 0, "cy": 0, "k1": 0, "k2": 0, "method": "zhang|platform|gyro"},
  "stabilisation": {"eis_controllable": true, "ois_controllable": "true|false|unknown",
                     "ois_samples_available": "true|false|unknown", "cal_exp_1_passed": "true|false|untested"},
  "timing": {"timestamp_source": "REALTIME|UNKNOWN|host_clock", "readout_time_ms": 0, "gyro_offset_ms": 0},
  "display": {"ppi": 0, "ppi_source": "spec|measured"},
  "verified_on": "YYYY-MM-DD", "notes": "string"
}
```

## 4. Calibration experiments (planned — none run yet)

| ID | Question | Method | Pass criterion |
|---|---|---|---|
| CAL-EXP-1 | Does stabilisation move the image relative to the body? | Phone on a tripod head; slow controlled rotations and small taps; compare image motion of the target with f_px × gyro angle, with OIS/EIS on vs. off | Residual between image and gyro motion ≤ 0.1 px RMS with stabilisation off (or after OIS-sample compensation) |
| CAL-EXP-2 | Camera ↔ IMU time offset and readout time | Gyro self-calibration (§2.3) repeated 10× | Offset repeatability ≤ 1 ms (1σ) |
| CAL-EXP-3 | BLE trigger latency | LED-in-frame method (`docs/hardware/BLE_TRIGGER_AND_IMU.md`) | Latency known to ≤ 5 ms (1σ) |
| CAL-EXP-4 | Print-scale tolerance in practice | Print the target on 3 printers × 2 settings, measure | Report distribution; set acceptance limits |
| CAL-EXP-5 | Focus breathing at 10 m | Calibrate at locked focus vs. autofocus | f_px change < 0.2 % with locked focus |
