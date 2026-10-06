# app/mobile/android-probe — Camera2 capability probe and OIS / gyroscope logger (experiment E-004b)

A single-activity Android app (Java, no third-party libraries, no network permission) that asks the phone what its
cameras can do instead of assuming it. Analysis is done off-device by `ml/evaluation/e004b_android_probe.py`.

| Button | What it does | Output |
|---|---|---|
| 1 | Dumps every `CameraCharacteristics` key of every camera, plus gyroscope/accelerometer facts | JSON (`sightline_camera2_probe`) |
| 2 | Saves the last result to a file you choose | — |
| 3 / 4 | 10 s metadata-only capture with OIS requested ON / OFF, EIS OFF, OIS position reporting ON where available: per-frame sensor timestamp, exposure, rolling-shutter skew, intrinsics, OIS samples; raw gyroscope events | JSON (`sightline_ois_log`) |
| 5 / 6 | Gyroscope only, 60 s / 10 min | CSV `timestamp_ns,x,y,z` (rad/s, device axes, `elapsedRealtimeNanos` clock) |

No pictures or video are stored: the camera stream goes to a 640×480 `ImageReader` whose images are discarded.
Permissions: `CAMERA` (asked on first use of 3/4) and `HIGH_SAMPLING_RATE_SENSORS` (gyroscope above 200 Hz on
Android 12+).

## Status

**IMPLEMENTED — compiled and signed, not yet run on any device.** The APK built from this source installs on
Android 5.0+ (API 21); OIS data keys need Android 9+ (API 28) and are skipped below that. Until it has run on a real
phone, treat its behaviour as untested: if a button fails, the message on screen is the bug report.

## Build (no Gradle)

```sh
ANDROID_SDK_ROOT=/path/to/sdk ./build_apk.sh        # needs JDK 17+, platforms;android-34, build-tools;34.0.0
```

Produces `build/sightline-probe-debug.apk`, signed with a throw-away debug key generated at build time. The build
directory is not committed.

## Notes

* Integer codes in the JSON are Android's own constants (`CameraMetadata`): e.g. OIS mode 0 = OFF, 1 = ON;
  timestamp source 0 = UNKNOWN, 1 = REALTIME. The analysis script decodes the ones it uses; the mapping was written
  from the Android reference from memory and should be re-checked against the reference before publication (UNVERIFIED
  this session).
* "Listed as available" is not "honoured". Whether OIS OFF really stops the lens is judged from the OIS samples of
  button 4, not from the capability list.
