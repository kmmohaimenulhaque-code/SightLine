# E-004b — Physical protocol: Android Camera2 capabilities and OIS samples

Status: **PHYSICAL_DATA_REQUIRED**. App: `app/mobile/android-probe/`. Analysis: `ml/evaluation/e004b_android_probe.py`.

1. Install `sightline-probe-debug.apk` on the Android phone (Android will ask to allow installing from this source;
   the app has no network permission). The APK is compiled but has not yet run on a device.
2. Open "SIGHTLINE Probe". Tap **1**. Tap **2** and save `sightline_probe_<model>.json`.
3. Tap **3** (allow the camera). For the whole 10 s hold the phone in your hand, pointing at any scene, and wobble
   it gently (a few millimetres at the top edge, a few times a second). Tap **2** to save.
4. Tap **4**, same wobble, save.
5. Send the three JSON files, or run:

```sh
python -m ml.evaluation.e004b_android_probe capabilities sightline_probe_<model>.json
python -m ml.evaluation.e004b_android_probe ois-log sightline_ois_log_ON_<model>.json sightline_ois_log_OFF_<model>.json
```

**What the analysis reports** (per device and Android build, nothing assumed beforehand):

| Question | Source |
|---|---|
| Which cameras have OIS; is OIS OFF listed; is EIS OFF listed | capability dump |
| Are OIS samples offered; timestamp source; rolling-shutter skew; intrinsics; distortion; manual controls | capability dump |
| Are OIS samples actually delivered, and at what rate | OIS log |
| Do frame, OIS and gyroscope timestamps share one timebase | OIS log (all compared with `elapsedRealtimeNanos` at start/stop) |
| Does the reported OIS shift follow the gyroscope; scale (px/rad), sign and axis pairing | OIS log, ON — least-squares fit, so the coordinate convention is measured rather than assumed |
| Does requesting OIS OFF stop the lens | OIS log, OFF — scatter of the OIS samples |

**Still open after this step** (needs pictures, not only metadata): comparing *observed image displacement* with the
reported OIS displacement. That recorder is PLANNED and will only be built if step 2 shows that this phone offers
OIS samples at all.
