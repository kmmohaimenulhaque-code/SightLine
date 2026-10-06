# SIGHTLINE Mission 2: Research Findings on iPhone 15 and Android Camera Control, Stabilisation, Localisation Limits, Sight Geometry and Licensing

The single most important finding: on the iPhone 15, no public Apple document says that turning stabilisation "off" disables the main camera's sensor-shift OIS in video. OIS is designed to hold the target image still on the sensor while the hand shakes, so it removes the very signal SIGHTLINE measures. E-004 is therefore the gating experiment. The research supports continuing, but the pipeline should be redesigned around (a) an Android device that honours OIS OFF or reports OIS samples, (b) the iPhone 15's non-OIS ultra-wide camera as a control, and (c) gyroscope-based hold measurement fused with vision-based absolute pointing.

## TL;DR

- **Stabilisation is the main risk, and on iPhone it cannot be settled from documentation.** Apple's iPhone 15 spec lists "Sensor-shift optical image stabilisation for video (Main)". `AVCaptureVideoStabilizationMode.off` is documented only as "A mode that doesn't stabilize video capture". A 2025 Apple Developer Forums thread asking whether `.off` disables hardware OIS shows no answer. Android Camera2, by contrast, has an explicit `LENS_OPTICAL_STABILIZATION_MODE` control and per-frame `OisSample` shifts in pixels on the same clock as `SENSOR_TIMESTAMP` (API 28+). Support depends on the device.
- **The theoretical floor allows sub-millimetre target-relative localisation, but only in ideal conditions.** Photogrammetry literature reports ≈0.02 px precision for well-imaged circular targets under ideal conditions and ≈0.1 px for simple centroids on real CCD images. At ≈3.46 mm/px (main camera, 4K, 10 m) that is ≈0.07–0.35 mm. This matches the E-001 simulation range. It is a precision floor, not accuracy: OIS shift, lens distortion, print scale, focus and compression all add bias that only E-002/E-003 can measure.
- **Recommendation: continue to a prototype, but redefine what is measured.** Use vision for absolute, target-relative pointing at low frequency. Use the gyroscope, which OIS cannot alter, for high-frequency hold and tremor (≈100 Hz on iOS; up to 200 Hz on Android 12+ without a special permission). Treat the screen sight as a sight-picture/hold/trigger trainer, not an optical replica of iron sights.

## Key Findings

### Status legend
VERIFIED = read in a primary source this session. SECONDARY = blog, forum, review, aggregator or third-party summary. DERIVED = calculated here from verified or secondary inputs. UNVERIFIED = from prior knowledge or not found; must be checked or measured.

## Q1. iPhone 15 (standard) hardware

| Item | Finding | Source / status | Confidence | SIGHTLINE implication |
|---|---|---|---|---|
| Rear cameras | Dual system: 48 MP Main 26 mm f/1.6; 12 MP Ultra Wide 13 mm f/2.4, 120° FOV; "2x optical zoom out" with digital zoom to 10x | Apple Support, iPhone 15 Tech Specs, support.apple.com/111831 (Apple test footnotes dated August 2023) — VERIFIED | High | Three usable fields of view; the 2x mode is a sensor crop, not a separate lens |
| OIS | "Sensor-shift optical image stabilisation for video (Main)" — OIS is listed for the Main camera only | Apple Tech Specs — VERIFIED | High | **The Ultra Wide (and the TrueDepth front camera) have no listed OIS. That makes the Ultra Wide a natural OIS-free control camera for E-004** |
| Main sensor size / pixel | 1/1.56-inch type, 1.0 µm native pixel, "dual pixel PDAF", sensor-shift OIS; Ultra Wide 12 MP f/2.4 13 mm | rfsafe.com spec page (GSMArena-style aggregator) — SECONDARY | Medium | Apple does not publish sensor size on the spec page. A 2.0 µm binned "quad-pixel" figure (12 MP mode) is UNVERIFIED here |
| Actual focal length | ≈6.0–6.3 mm (DERIVED: 1/1.56-inch ≈ 8.06 × 6.05 mm active area at 8064 × 6048 px × 1.0 µm, diagonal ≈ 10.1 mm, crop ≈ 4.3, 26 mm / 4.3 ≈ 6.06 mm) | DERIVED; read EXIF FocalLength from a real HEIC to confirm | Medium | Use the EXIF value or calibrated fx; never the marketing equivalent |
| Angular pixel at 4K | ≈0.346 mrad/px ⇒ ≈3.46 mm/px at 10 m (Main, 3840 px across ≈8.06 mm sensor width); black 59.5 mm ≈ 17 px; 10-ring 11.5 mm ≈ 3.3 px | DERIVED, consistent with the Mission 1 figure of 3.4 mm/px | Medium-high | Ring lines are invisible; scoring must be model-based (fit the black, infer rings from ISSF geometry) |
| 2x mode | Marketed as an "optical-quality" 52 mm-equivalent crop of the 48 MP sensor. If 4K is read from a native-pitch central crop, ≈1.7 mm/px at 10 m (black ≈ 34 px) | UNVERIFIED (crop/readout behaviour in video is not documented) | Low-medium | Potentially doubles resolution; E-002 should capture 1x and 2x |
| Ultra Wide at 4K | ≈6.9 mm/px at 10 m (DERIVED from half the focal length); black ≈ 8.6 px | DERIVED | Medium | Coarser but OIS-free; still ≈8 px across the black, enough for an ellipse fit |
| Video modes | 4K at 24/25/30/60 fps; 1080p at 25/30/60 fps; 720p at 30 fps; Dolby Vision HDR to 4K60; slo-mo 1080p at 120/240 fps; "Cinematic video stabilisation (4K, 1080p and 720p)"; "Continuous autofocus video"; 8 MP stills during 4K | Apple Tech Specs — VERIFIED | High | 1080p240 slo-mo is attractive for timing, but its stabilisation and processing state are unknown |
| Codecs | "Video formats recorded: HEVC and H.264" — no ProRes or Log listed for the standard iPhone 15 | Apple Tech Specs — VERIFIED (ProRes/Log are Pro-model features by omission) | High | Least-processed video on iPhone 15 = high-bitrate HEVC with HDR off. Third-party apps cannot add ProRes where the hardware/OS does not offer it |
| Stills | HEIF/JPEG; ProRAW is a Pro feature; Bayer RAW (DNG) through AVCapturePhotoOutput on non-Pro models | UNVERIFIED (not re-read this session) | Medium | If Bayer DNG is available, it is the best route to photon-transfer noise measurement (Q5c) |
| Front TrueDepth camera | 12 MP, ƒ/1.9 aperture, autofocus with Focus Pixels; 4K 24/25/30/60 fps; 1080p slo-mo 120 fps; Face ID | Apple Tech Specs (video) — VERIFIED; f/1.9 and AF from phonetradr spec page — SECONDARY | Medium-high | Eye/face tracking at 0.6–0.8 m is plausible but accuracy is undocumented (see Q2e/Q6d) |
| Body | 147.6 × 71.6 × 7.80 mm, 171 g; 6.1-inch OLED | Apple Support, iPhone 15 Tech Specs: "Width: 2.82 inches (71.6 mm); Height: 5.81 inches (147.6 mm); Depth: 0.31 inch (7.80 mm); Weight: 6.02 ounces (171 grams)" — VERIFIED | High | Grip CAD baseline; measure the actual unit with calipers |
| Display resolution | 2556 × 1179 px at 460 ppi | Apple Support, iPhone 15 Tech Specs, Display section: "2556‑by‑1179-pixel resolution at 460 ppi" — VERIFIED | High | ≈55 µm pixel pitch; relevant to overlay-sight rendering resolution |
| Dimensional drawing | Apple publishes "iPhone 15 Dimensional Drawings" (PDF dated 2023-10-10, sheet 1–3, at developer.apple.com/download/files/accessories/dimensional-drawings/iphone-15.pdf). Accessory Design Guidelines main document is "Release R31"; the Accessories page says "Updated September 21, 2026" | Apple Developer — VERIFIED (document existence, dates) | High | Primary source for camera position |
| Camera/flash positions | Text extracted from sheet 2 includes "PRODUCT CENTER 35.81" (= 71.62/2, the half-width) and "-73.82" (≈ 147.6/2, the half-height), so dimensions are referenced to the product centre. Candidate coordinate pairs are "9.05 / 57.58" and "14.05 / 62.08". Keep-out cones: Rear Camera 1 121.83°, Rear Camera 2 75.55°, Flash inner 112.01°/outer 157.00°. Keep-out diameters at cover glass: Rear Camera 1 9.11, Rear Camera 2 6.90, Flash 9.56 (mm). Front camera keep-out cone 94.00° | VERIFIED text, **UNVERIFIED interpretation** (text extraction loses the drawing geometry; which pair is which lens and from which datum is not certain) | Low for coordinates, high for cone/diameter values | Read sheet 2 visually and confirm by caliper measurement of the real phone before CAD. The 121.83° cone (≈ Ultra Wide 120° FOV) suggests Rear Camera 1 = Ultra Wide and Rear Camera 2 = Main, but this is an inference |
| Case/grip constraints | Earlier guideline releases state: "Cases must not interfere with the Apple device's magnetic compass or rear camera OIS feature if present." The iPhone 15 drawing marks areas "DO NOT OBSTRUCT THIS AREA WITH MAGNETIC OR PERMEABLE MATERIAL" (compass) and conductive-material keep-outs | Accessory Design Guidelines (R5 copy, third-party host) — SECONDARY for wording; iPhone 15 drawing — VERIFIED | High | **No magnets or steel inserts near the camera module in the grip. Magnetic BLE-button mounts must respect the compass and OIS keep-outs** |

## Q2. iOS camera control for measurement (AVFoundation, iOS 17–26)

### Q2a. Stabilisation and OIS
- **Modes and history.** Apple Technical Note TN2409 (2014-10-30) lists four original modes: `Off`, `Standard`, `Cinematic`, `Auto`. Its key statements are:
  - "The default value for preferredVideoStabilizationMode is AVCaptureVideoStabilizationModeOff."
  - "Setting the preferred stabilization mode to a constant other than AVCaptureVideoStabilizationModeOff does not force video stabilization on."
  - "iOS 6 introduced API support for video stabilization on the iPhone 4s."

  The note does not name the iOS version for these constants; iOS 8 is inferred. Status: VERIFIED (via the research subagent's full fetch).
- **Later modes.**
  - `cinematicExtended` is documented as "A mode that uses the extended cinematic stabilization algorithm" (iOS 13, UNVERIFIED version).
  - `cinematicExtendedEnhanced` is documented as "A mode that stabilizes video using the enhanced extended cinematic stabilization algorithm" (iOS 18, UNVERIFIED version). Apple's WWDC25 session 319 sample code uses it, and an Apple Developer Forums accepted answer says spatial video on iPhone 15 Pro requires a cinematic mode.
  - `previewOptimized` is iOS 17 (UNVERIFIED version).
  - `lowLatency` is described in WWDC26 session 341: "The Center Stage front camera supports a real-time, low-latency stabilization mode starting in iOS 26. It's off by default."

  Status: VERIFIED for doc one-liners and WWDC quotes; introduction versions other than iOS 26 for `lowLatency` are UNVERIFIED because Apple's JavaScript documentation pages could not be read.
- **What `.off` does to OIS: undocumented.** The `.off` case text is only "A mode that doesn't stabilize video capture." Apple Developer Forums thread 801283, "Disabling Hardware OIS via AVFoundation", asks exactly whether `.off` "guarantees the complete deactivation of the physical OIS module". The retrieved page shows no reply. Apple's iPhone 6s-era note (Developer Forums thread 21694) said "On iPhone 6s Plus, optical image stabilization is used ... for stabilizing video for video data output or movie file output." An Apple Community user quotes Apple docs that the stabilisation property "automatically enables both optical and digital stabilization on devices supporting video OIS", which implies OIS may be coupled to the mode rather than always on. Status: the absence of documentation is VERIFIED; actual behaviour is UNVERIFIED. **Settle by E-004 (see experiments).**
- **Practitioner reports are contradictory.** Apple Community users (2016–2018) say "There is no way to disable the image stabilization on the iPhone". A 2025 Developer Forums post reports OIS-like shake artefacts in high-vibration use on lenses with OIS. Status: SECONDARY.
- **Photo-only lens stabilisation API.** `AVCaptureDevice.LensStabilizationStatus` is documented as "Constants that indicate the status of optical image stabilization hardware during a bracketed photo capture". `isLensStabilizationDuringBracketedCaptureSupported` and `AVCapturePhotoBracketSettings.isLensStabilizationEnabled` were added in iOS 10 (iOS 10 API diffs). This is the only public API that reports OIS state, and it covers bracketed stills, not video. Status: VERIFIED for the one-liners.

### Q2b. Per-frame intrinsics and calibration data
- `kCMSampleBufferAttachmentKey_CameraIntrinsicMatrix` is "An attachment that indicates a 3x3 camera intrinsic matrix to apply to the current sample buffer". It is enabled through `AVCaptureConnection.isCameraIntrinsicMatrixDeliveryEnabled`. Support "is true only if both the connection's input device format and output class support delivery of camera intrinsics" (doc text quoted on the Developer Forums). Status: VERIFIED one-liners.
- **Whether the principal point tracks OIS is not documented.** One Developer Forums report (thread 654288, iOS 13.5.1) observed fx/fy varying with focus fixed, which hints that the matrix is dynamic. Status: SECONDARY. Google's video-stabilisation patents (US 10,462,370 / 11,064,119 / 11,683,586 / 12,167,134) model "OIS lens shift data ... as an additional offset to a principal point". That is exactly the model SIGHTLINE needs, but it is Google's, not Apple's.
- **MARS logger (OSU, arXiv 2001.00470)** enables CameraIntrinsicMatrix delivery so that "every frame has an attachment containing the focal length and principal point offsets in pixels". Status: VERIFIED (peer-reviewed/preprint).
- `AVCameraCalibrationData` (intrinsicMatrix "relates a camera's internal properties to an ideal pinhole-camera model"; lensDistortionLookupTable is "a C array of floats" of radial magnifications from lensDistortionCenter, WWDC17 session 507) is delivered with depth/dual-camera captures. Whether iPhone 15's dual-wide virtual device delivers it for video, and with which formats, is UNVERIFIED. Probe `AVCaptureDevice.formats` on the device.

### Q2c. Timing, exposure and focus
- **Clock.** MARS logger: Core Motion data are "timestamped by the clock returned by CMClockGetHostTimeClock() while the camera frames have presentation times referring to the masterClock of a capture session". They convert with `CMSyncConvertTime()`. Status: VERIFIED (arXiv). `CMLogItem.timestamp` is "The time when the logged item is valid"; it is quoted on the Apple forums as "seconds since the device booted". Its exact clock domain is not stated in the docs (UNVERIFIED).
- **Which instant the video PTS represents** (start of exposure, mid-exposure or start of readout) is not documented by Apple in any source found. Status: UNVERIFIED. Settle with an LED-flash timing experiment.
- **Rolling-shutter readout time** for iPhone 15 in 1080p/4K: no published measurement found. Status: UNVERIFIED. Karpenko et al. (2011) show it can be estimated from a ≈10 s gyro + video recording.
- **Manual control.** Custom exposure (`setExposureModeCustom(duration:iso:)`), `setFocusModeLocked(lensPosition:)` (0.0–1.0, not calibrated in distance) and locked white balance are standard AVFoundation (UNVERIFIED against the docs this session). Blackmagic Camera exposes focus "from minimum focus distance (0.00) to maximum focus distance (1.00)", matching the lensPosition scale (VERIFIED from Blackmagic tech specs).
- **Focus at 10 m vs infinity (DERIVED, f ≈ 6.06 mm, f/1.6, aperture ≈ 3.8 mm).** Focused at infinity, an object at 10 m blurs to ≈ A·f/s ≈ 3.8 × 6.06 / 10 000 ≈ 2.3 µm ≈ 1.1 output pixels at 4K. Hyperfocal distance with a 4.2 µm circle of confusion (2 output pixels) is ≈5.5 m, so 10 m is inside the depth of field either way. Focus breathing and lens-position-dependent focal length still change scale (Google's Fused Stabilisation post explicitly models "focus breathing"). **Lock focus once at the target and record the lensPosition.**

### Q2d. Core Motion
- **Rate.** Third-party evidence suggests ≈100 Hz is the practical ceiling through high-level wrappers:
  - zheerwang/ios-sensor-logger measured "approximately 100.5 Hz" for both accelerometer and gyroscope on an iPhone 15 Pro, even when 200 Hz and 500 Hz were requested (via Expo Sensors).
  - SensorLog (App Store) states "up to 100Hz".

  Status: SECONDARY. Whether native `CMMotionManager` with `gyroUpdateInterval` < 0.01 s delivers more than 100 Hz on iPhone 15 is UNVERIFIED (Apple docs retrieved give no maximum). **Measure with a native build or a logger that reports inter-sample intervals.**
- **IMU part and noise density.** Not identified in any source found this session. Status: UNVERIFIED. Measure an Allan variance on the static phone instead.
- **Device frame.** Core Motion uses x to the right, y towards the top of the device, z out of the screen (UNVERIFIED this session; standard Apple convention). Note that the camera looks along −z.

### Q2e. ARKit
ARKit's `ARFrame` exposes `camera.intrinsics`, `timestamp`, `exposureDuration` and `exposureOffset` (UNVERIFIED this session). ARKit does not offer OIS control. Published accuracy for ARKit face-tracking eye position at 0.6–0.8 m was not found (UNVERIFIED). TrueDepth range for Face ID is designed for arm's length, so tracking at 0.6–0.8 m is plausible, but mm accuracy needs an experiment against a calibrated head target.

### Q2f. Capture tools for an owner without a Mac
| Tool | What it offers | Status | Fit for SIGHTLINE |
|---|---|---|---|
| Blackmagic Camera (iOS, free; "requires an iPhone XR or later running iOS 16 or later" at launch) | Stabilisation "Off, Standard, Cinematic, Extreme"; ISO "21 to 5472"; white balance "Locked, Auto or Manual"; focus AF on/off plus manual 0.00–1.00; shutter angle/speed; frame rate; changelog: "Addressed an issue where stabilization could not be switched off." | Blackmagic tech specs and App Store page — VERIFIED (vendor); 9to5Mac — SECONDARY | **Best no-code video recorder for E-002/E-004.** "Off" most likely maps to `.off`, which still leaves the OIS question open. Metadata export of per-frame intrinsics is not documented (UNVERIFIED) |
| Blackmagic Camera (Android) | Stabilisation "Off, Standard, Optical"; ISO 25–10666 | Blackmagic tech specs — VERIFIED (vendor) | Gives the Android test device a quick OIS-vs-EIS toggle without code |
| SensorLog (iOS) | Up to 100 Hz in the foreground; background long-term accelerometer recording at up to 50 Hz | App Store — VERIFIED (vendor) | **Simultaneous use with a foreground camera app is doubtful.** iOS suspends background apps, so expect logging to stop when the camera app is in front (UNVERIFIED; test it) |
| SensorLogger – CSV Export, Sensor Logger+ Data (iOS) | Accelerometer/gyroscope/magnetometer to CSV; configurable rate | App Store — VERIFIED (vendor) | Same background limitation |
| MARS logger (OSUPCVLab/mobile-ar-sensor-logger) | Camera frames ≈30 Hz plus IMU ≈100 Hz "synced to one clock source", per-frame intrinsics and exposure duration to CSV, on Android (API 21+) and iOS | GitHub README and arXiv 2001.00470 — VERIFIED | Ideal data format, **but on iOS it must be built with Xcode** (no App Store build found). Licence not verified this session |
| ios_logger (Varvrar) | Camera frames plus accelerometer/gyroscope/motion logs | GitHub — SECONDARY | Also requires Xcode |

**Implication.** Without a Mac, the best iPhone workflow is to film with Blackmagic Camera (Off, locked focus/ISO/shutter/WB) and run a timing/IMU reference on a second device or on the Android phone. A free Apple ID with Xcode on a borrowed Mac (7-day sideload) would unlock MARS-style synchronised logging.

## Q3. Android Camera2 for stabilisation research

### Q3a. API semantics
| Key | Documented semantics | Status |
|---|---|---|
| `LENS_OPTICAL_STABILIZATION_MODE` / `LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION` | "Sets whether the camera device uses optical image stabilization (OIS) when capturing images"; OFF/ON; API 21 | VERIFIED (key text); API level UNVERIFIED this session |
| `CONTROL_VIDEO_STABILIZATION_MODE` / `CONTROL_AVAILABLE_VIDEO_STABILIZATION_MODES` | OFF / ON (API 21) / PREVIEW_STABILIZATION (API 33). The Android reference warns that enabling OIS and EIS together may interact badly | UNVERIFIED this session (prior knowledge) |
| `STATISTICS_OIS_DATA_MODE`, `STATISTICS_INFO_AVAILABLE_OIS_DATA_MODES`, `STATISTICS_OIS_SAMPLES` | "A control for selecting whether optical stabilization (OIS) position information is included in output result metadata"; samples are an array of `OisSample`; `STATISTICS_OIS_DATA_MODE_ON` "Added in API level 28" | VERIFIED |
| `OisSample` | "contains the timestamp and the amount of shifts in x and y direction, in pixels, of the OIS sample. A positive value for a shift in x direction is a shift from left to right in active array coordinate system. For example, if the optical center is (1000, 500) in active array coordinates, a shift of (3, 0) puts the new optical center at (1003, 500)." The timestamp is in nanoseconds and "in the same timebase as and comparable to android.sensor.timestamp" | VERIFIED (developer.android.com) |
| `SENSOR_TIMESTAMP` | "Time at start of exposure of first row of the image sensor active array, in nanoseconds" | VERIFIED |
| `SENSOR_INFO_TIMESTAMP_SOURCE` | REALTIME: "in the same timebase as SystemClock.elapsedRealtimeNanos(), and they can be compared to other timestamps using that base". UNKNOWN: "monotonic, but can not be compared to timestamps from other subsystems (e.g. accelerometer, gyro etc.) ... with accuracy ... roughly in the same timebase as SystemClock.uptimeMillis()", accurate enough "for A/V synchronization" | VERIFIED |
| `LOGICAL_MULTI_CAMERA_SENSOR_SYNC_TYPE_CALIBRATED` | "the timestamp of a physical stream image accurately reflects its start-of-exposure time" | VERIFIED |
| `SensorEvent.timestamp` | "The time in nanoseconds at which the event happened ... using the same time base as SystemClock.elapsedRealtimeNanos()" | VERIFIED |
| `SENSOR_ROLLING_SHUTTER_SKEW` (API 21), `SENSOR_READOUT_TIMESTAMP` (API 34), `SENSOR_EXPOSURE_TIME`, `LENS_INTRINSIC_CALIBRATION` (API 23), `LENS_DISTORTION` (API 28), `LENS_POSE_*`, `CONTROL_ZOOM_RATIO` (API 30), `INFO_SUPPORTED_HARDWARE_LEVEL` | Standard keys. Whether `LENS_INTRINSIC_CALIBRATION` is per-frame and includes the OIS shift is device-dependent and should not be assumed | UNVERIFIED this session (prior knowledge) |
| `LENS_DISTORTION` model | Radial κ1–κ3 plus tangential κ4–κ5 polynomial (the CaptureResult page shows both forms, including the deprecated variant with κ0) | VERIFIED |

**Key implication.** If the Android test device reports `TIMESTAMP_SOURCE_REALTIME` and `OIS_DATA_MODE_ON`, SIGHTLINE can (1) subtract the OIS optical-centre shift per frame and (2) align frames with gyroscope events on one clock. That is exactly the "known motion → OIS compensation → residual" chain needed for E-004.

### Q3b. Real-world behaviour
- A Google CameraX engineer on the CameraX developers list says behaviour "highly depend[s] on the camera framework and the device". He adds that digital stabilisation "will be automatically enabled when a video stream is configured" in CameraX. A user reports no visible change after setting OIS ON. Status: SECONDARY (Google employee, informal).
- Samsung forum: two Galaxy S8 variants (SM-G950F Exynos vs SM-G950W Snapdragon, both Android 9) report different `LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION` lists. Variants of the same phone model can differ. Status: SECONDARY.
- **Google Pixel Fused Video Stabilization (Google Research blog, 10 November 2017).** "both OIS and EIS are enabled simultaneously during video recording". Google "carefully optimize[s] the system to ensure perfect timestamp alignment between the CMOS image sensor, the gyroscope, and the lens motion readouts. A misalignment of merely a few milliseconds can introduce noticeable jittering". It corrects rolling shutter and focus breathing. Status: VERIFIED (Google primary). Implication: Pixels are the most likely to expose OIS samples, but this is UNVERIFIED per model.
- Which specific phones honour OIS OFF or report OIS samples: no authoritative list found. Status: UNVERIFIED. Run a capability probe on the father's phone first.

### Q3c. Free tools
Blackmagic Camera for Android (Off/Standard/Optical) is VERIFIED (vendor). MARS logger Android (API 21+) records video plus IMU on one clock (VERIFIED). OpenCamera Sensors (Skoltech), Open Camera's own options, and Camera2 probe apps (e.g. "Camera2 API Probe") were not researched this session (UNVERIFIED). Open Camera's official site (opencamera.org.uk) states "Open Camera is released under the GPL v3 or later", and F-Droid lists it as "GNU General Public License v3.0 or later". That matters only if its code is copied, not if it is used as a tool.

### Q3d. Android IMU rate
Android 12 (API level 31) caps sensor updates at 200 Hz for third-party apps. The ARMOUR study (arXiv 2507.02177, 2025), citing Android's behaviour-change documentation, states: "Android 12 starts to limit the highest available sampling rate to 200 Hz for common sensor usage by third-party apps, where any app that needs a higher sampling rate is required to declare the use in the manifest file through the HIGH_SAMPLING_RATE_SENSORS permission." Expo and .NET MAUI docs restate the same policy. The same ARMOUR study observed `SENSOR_DELAY_GAME` = 52 Hz and up to 206 Hz without the permission on a OnePlus device, and reports that "Requesting sampling rates higher than 206 Hz without declaring the HIGH_SAMPLING_RATE_SENSORS permission in Android 12 and above results in compiling errors." Microsoft's MAUI docs add that if the user disables microphone access, "motion and position sensors are always rate-limited". Status: VERIFIED via a peer-reviewed study citing the Android primary source, consistent across sources. Implication: 200 Hz gyroscope covers the 8–12 Hz tremor band with a wide margin; declare the permission for higher rates.

## Q4. Effect of OIS/EIS on pointing measurements

- **(i) Stroke and band.** STMicroelectronics' OIS white paper says hand jitter has "An amplitude typically less than 0.5 degrees" and "a spectrum in the range 0 – 20 Hz". It states that a ±1° correction range "allows good compensation to suppress jitter", resolving "around ten thousandth of degree". Status: VERIFIED (vendor white paper). An OIS control paper (via ResearchGate abstract) targets "2-12 Hz". Nidec says conventional OIS works "with tilt displacement of up to ±1º approximately" (vendor). A camera-module developer blog cites OIS ≈±1° and EIS ≈±3° (SECONDARY). Patents describe gyro angle limits of ±1–3°.
  - **DERIVED consequence.** The whole ISSF black (0.341°) and the 10-ring (11.5 mm ≈ 0.066° at 10 m) are far inside OIS stroke. OIS can therefore fully cancel tremor-scale pointing changes in the image.
  - **Re-centring/high-pass behaviour** for slow sway is generally implied by the "0–20 Hz" design band and gyro-integration drift handling, but no smartphone vendor publishes it (UNVERIFIED). This is the central E-004 measurement: OIS transfer function vs frequency.
- **(ii) Gyro–image calibration methods.**
  - Karpenko, Jacobs, Baek and Levoy (Stanford CSTR 2011-03) estimate "camera focal length, rolling-shutter duration, gyroscope-to-camera timing delay, gyroscope drift, and axis correspondence from one approximately ten-second calibration recording" (VERIFIED via summary; Stanford PDF not fetched).
  - Bell et al., "A Non-Linear Filter for Gyroscope-Based Video Stabilization" (ECCV 2014, Springer), extends this (VERIFIED abstract).
  - Google's patents model OIS as a principal-point offset at the scanline time; the target time is "typically ... the middle of the exposure duration".
  - Status: VERIFIED. **Implication: SIGHTLINE should adopt the Karpenko calibration as its standard camera–IMU calibration (E-004 step 1).**
- **(iii) Tremor and hold.**
  - ST: <0.5°, 0–20 Hz (above). For physiological tremor, a 2024 review ("Updates in essential tremor", Parkinsonism & Related Disorders) states: "High frequency tremor is 8–12 Hz and physiologic tremor is usually within this range" (VERIFIED, peer-reviewed review).
  - A study summary on ResearchGate (study identity not confirmed) reports horizontal aiming-point variability "M = 6.91 mm, SD = 2.40" at original distance vs 10.00 mm at reduced distance (SECONDARY).
  - Other relevant studies, without retrieved numbers: Chadefaux et al. (2020, Computer Methods in Biomechanics and Biomedical Engineering) used SCATT traces for elite vs novice and found more pistol and centre-of-pressure motion in novices; Ihalainen et al. ("Key technical components for air pistol shooting performance"); and the "Postural tremor and control of the upper limb in air pistol shooters" accelerometer study.
  - **DERIVED interpretation.** Hold movement of ≈5–10 mm at 10 m ≈ 0.5–1 mrad ≈ 1.5–3 px (main, 4K). It is measurable by vision only with sub-pixel precision, and it sits inside the OIS band.

## Q5. Theoretical localisation limits

- **(a) Precision theory.**
  - Trinder (1989, Photogrammetric Engineering & Remote Sensing 55(6):883–886): "precision of target location can be of the order of 0.02 pixel or better under ideal circumstances". Deviations from ideal images "cause considerable loss of precision".
  - Shortis, Clarke & Short (1994, SPIE 2350:239–250) compared binary centroid, grey-scale centroid, squared centroid, ellipse fitting and Gaussian fitting. Practical tests on CCD cameras gave "a precision 0.1 of a pixel using either a binary centroid or a simple grey scale centroid algorithm", with best cases ≈0.02 px.
  - Status: VERIFIED via abstracts/secondary pages.
  - Formal CRLB derivations, Ahn et al. on circular-target eccentricity bias and Mallon & Whelan (2007) on perspective bias were not retrieved (UNVERIFIED citations). The physics is well known, though: under perspective the centre of the imaged ellipse is not the image of the circle's centre. The bias grows with target size and obliquity, so a 59.5 mm black at 10 m with a few degrees of tilt gives a negligible bias (DERIVED; verify numerically in E-005).
  - **DERIVED floor.** At 3.46 mm/px, 0.02–0.1 px ≈ 0.07–0.35 mm, assuming a high-contrast, well-sampled edge. An ellipse fit to the black's full perimeter (≈53 px circumference, ≈17 px diameter) is the right estimator; centroiding a 17 px blob is quantisation-limited.
- **(b) Compression/ISP effects.** Not retrieved this session (UNVERIFIED). Expectation: HEVC/H.264 quantise 8×8–32×32 blocks and can shift low-contrast edges by sub-pixel amounts. Sharpening creates overshoot halos that bias threshold-based edges. Denoising lowers effective SNR on small targets. **E-003 must compare HEVC vs still HEIF vs (if available) DNG of the same scene.**
- **(c) Sensor noise.** No photon-transfer measurement for the iPhone 15 sensor was found (UNVERIFIED). Do not import numbers. Measure via a photon-transfer curve on DNG stills or on flat-field video if RAW is unavailable.
- **(d) Diffraction/defocus (DERIVED).** Airy disk diameter = 2.44·λ·N = 2.44 × 0.55 µm × 1.6 ≈ 2.1 µm, about 2 native pixels and about 1 output pixel at 4K. Defocus at 10 m when focused at infinity is ≈2.3 µm (Q2c). Optical blur is therefore ≈1–1.5 output pixels, which is good for sub-pixel edge fitting (moderate blur avoids aliasing).
- **(e) Print tolerances.** The ISSF/CMP target-specification snippets show ring tolerances are tight (CMP 2025: "Air Rifle scoring rings must be within ±0.1"; the air-pistol tolerance text was truncated in the retrieved snippet). Office printer scale accuracy and dot gain were not sourced (UNVERIFIED). **Print a 100 mm and 150 mm calibration bar on the same sheet and measure with a steel rule/caliper. Scale the scoring model by the measured black diameter rather than trusting the 59.5 mm nominal value.**

## Q6. Sight geometry and human factors

- **(a) Sight dimensions.** Model-specific notch/blade data were not retrieved this session (UNVERIFIED beyond the brief's Steyr LP10 316–365 mm sight radius). Use calipers on a real pistol if available.
- **DERIVED angular-vs-parallel error.** A sight misalignment δ at sight radius r produces a target error E ≈ δ·(D/r), with D = 10 m:
  - δ = 0.1 mm at r = 350 mm gives E ≈ 2.9 mm, about a quarter of the 10-ring diameter (11.5 mm).
  - A parallel (sight-picture) error, with sights aligned but the picture displaced, moves the shot only by the displacement itself, i.e. ×1.

  This is the quantitative reason coaching stresses alignment over sight picture.
- **(b) Visual performance.** Vernier/alignment acuity values and accommodation literature were not retrieved (UNVERIFIED). The physics stands: the eye can focus only one of the three planes (rear ≈0.7 m, front ≈1.0 m, target 10 m) at a time.
- **(c) Parallax-free overlays.** An overlay drawn at a fixed pixel of live camera video is a parallax-free reticle. Its line of sight is the camera's optical axis, independent of where the eye is. It therefore behaves like a red-dot or reflex sight, not like iron sights. Status: DERIVED. The ISSF's official Disciplines page (issf-sports.org) states: "Pistol sights: Only open sights are permitted. The open sights consist of a post or blade sight at the front of the gun, and a notch at the rear. Any other type of sight — optical, mirror, telescope, laser beam or electronically projected beam — are prohibited." **A camera overlay is therefore an electronically produced, parallax-free sight that ISSF does not permit, so SIGHTLINE must not claim rule-equivalent sight training.**
- **What a screen-based sight CAN train (DERIVED):**
  - hold stability (trace);
  - trigger release without disturbing the aim (the BLE press-to-motion signature);
  - timing and follow-through;
  - an abstract alignment task (a rendered notch/blade with light gaps that the shooter must centre, driven by the measured phone attitude);
  - sight-picture placement (6 o'clock vs centre hold).
- **What it CANNOT train:** the real eye–rear–front collinearity with accommodation on a physical front blade. A flat display at ≈0.7 m is a single focal plane, and the real "angular error" arises from the eye's position relative to two physical sights.
- **(d) Head-tracked rendering.** A head-tracked "window" (TrueDepth/ARKit or MediaPipe) could in principle re-introduce eye-position dependence. Whether it is good enough depends on eye-position accuracy at arm's length. No published mm accuracy was found (UNVERIFIED), so it should be an E-006 sub-experiment.
- **Redesign proposal.** Keep the feature but rename it "Alignment Trainer (simulated)". Make the rendered rear notch fixed to the screen, and make the front blade move with the gyro-measured attitude error relative to the camera-measured target. That trains alignment discipline as a control task, explicitly not as optics.
- **(e) Optoelectronic trainers.** SCATT is the instrument used in the Chadefaux et al. study for "aiming time, and trace length" (VERIFIED as usage). Calibration procedures and accuracy claims for SCATT, Rika and Noptel were not retrieved (UNVERIFIED; manufacturer claims only).

## Q7. Licensing and rules

- **(a) Dependencies.**
  - opencv-python 5.0.0.93 on PyPI: "OpenCV itself is available under Apache 2 license", the packaging scripts are MIT, and "All wheels ship with FFmpeg licensed under the LGPLv2.1". "Non-headless Linux wheels ship with Qt 5 licensed under the LGPLv3", so headless wheels avoid Qt but still contain FFmpeg (VERIFIED, PyPI).
  - OpenCV's own FFmpeg readme: the plugin is an "LGPL library, not BSD libraries", is "Loaded at runtime", and the advice is: "If LGPL/GPL software can not be supplied with your OpenCV-based product, simply exclude opencv_videoio_ffmpeg*.dll".
  - FFmpeg's legal page requires, for redistribution, LGPL builds without "--enable-gpl", dynamic linking, and distributing the corresponding source.
  - **Conclusion: no conflict for an Apache-2.0 source repository that only declares `opencv-python-headless` as a dependency.** LGPL obligations arise only if SIGHTLINE redistributes the wheel or binaries (PyInstaller bundle, app package). In that case, ship FFmpeg's notice, the LGPL text and a source offer.
  - NumPy (BSD-3-Clause, with bundled components under other permissive licences) and pytest (MIT, development only) are compatible (UNVERIFIED this session; well-established).
- **How to apply Apache-2.0 (prior knowledge, UNVERIFIED this session):**
  - Full LICENSE text.
  - A NOTICE file only for SIGHTLINE's own attribution notices (Apache-2.0 §4(d) requires preserving NOTICE files of Apache-licensed works you redistribute; OpenCV is not redistributed if only declared as a dependency).
  - `SPDX-License-Identifier: Apache-2.0` headers.
  - In pyproject (PEP 639): `license = "Apache-2.0"` and `license-files = ["LICENSE", "NOTICE"]`, with no legacy licence classifiers.
- **(b) Non-code assets (recommendation only).**

| Asset | Option | Pros | Cons |
|---|---|---|---|
| CAD (grip) | CERN-OHL-P-2.0 | Permissive, hardware-specific, patent and "source location" concepts | Less familiar to hobbyists |
| CAD (grip) | CERN-OHL-W/S-2.0 | Reciprocal: improvements stay open | Deters commercial reuse |
| CAD (grip) | CC BY 4.0 | Widely understood | Not designed for hardware; no patent clause |
| Datasets | CC BY 4.0 | Standard, attribution | Database rights nuance in EU |
| Datasets | CDLA-Permissive-2.0 | Data-specific, minimal | Less known |
| Datasets | ODC-By | Database-rights aware | Less known outside open data |
| Model weights | Apache-2.0 (with code) | Simple, patent grant | No use restrictions (likely fine) |

  Recommendation: CERN-OHL-P-2.0 for CAD, CC BY 4.0 for images/datasets, and Apache-2.0 for any weights. Decide after asset strategy (UNVERIFIED legal advice; not a lawyer).
- **(c) ISSF scoring rule.** The ISSF "Rules for Paper Target Scoring", edition 2022 (effective 1 January 2022, first print 01/2023), says:
  - "If any part of a higher value scoring ring is touched by a bullet hole, the shot must be scored the higher value of the two scoring zones. This is determined by whether the bullet hole or a plug gauge inserted in the hole touches any part of the outside edge of the scoring ring."
  - The "4.5mm OUTWARD Gauge for 10m Air Pistol" has a measuring edge diameter of "11.50mm (+0.00/-0.05mm)", spindle diameter "4.60mm (+0.05mm)", and is "To be used for: 10m Air Pistol, rings 2 to 10".

  Status: VERIFIED (ISSF backoffice PDF). A 2025/2026 edition was not located this session.
  - **Implication.** "Touch" scoring means the scoring boundary for ring n is ring-radius + 2.25 mm (pellet radius), using the outside edge of the line. SIGHTLINE's model must score centre-distance ≤ R_n + 2.25 mm, with R_n taken to the outside edge.

## Capability Matrix

Every cell "requires experimental verification" on the actual devices.

| Capability | iPhone 15 (documented) | Android Camera2 (documented; device-dependent) |
|---|---|---|
| OIS hardware | Main camera sensor-shift OIS; Ultra Wide and front camera have none listed — requires experimental verification | Reported via `LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION` — requires experimental verification |
| OIS disable | No documented control; `.off` semantics ambiguous — requires experimental verification | `LENS_OPTICAL_STABILIZATION_MODE_OFF` if listed; OEM may ignore — requires experimental verification |
| OIS metadata | None for video; `LensStabilizationStatus` for bracketed stills only — requires experimental verification | `STATISTICS_OIS_SAMPLES` (x/y px shift, sensor-timestamp clock, API 28+) if `OIS_DATA_MODE_ON` available — requires experimental verification |
| EIS control | `preferredVideoStabilizationMode` (off/standard/cinematic/cinematicExtended/…/lowLatency) — requires experimental verification | `CONTROL_VIDEO_STABILIZATION_MODE` OFF/ON/PREVIEW_STABILIZATION; CameraX may auto-enable — requires experimental verification |
| Stabilisation fully disabled | Unknown; best candidate is the Ultra Wide with `.off` — requires experimental verification | Plausible if OIS OFF and EIS OFF are both honoured — requires experimental verification |
| Per-frame intrinsics | `CameraIntrinsicMatrix` attachment where format/output support it; OIS tracking undocumented — requires experimental verification | `LENS_INTRINSIC_CALIBRATION` (static or per-result, device-dependent) plus OIS samples — requires experimental verification |
| Lens distortion data | `AVCameraCalibrationData.lensDistortionLookupTable` for depth/dual captures — requires experimental verification | `LENS_DISTORTION` radial/tangential coefficients — requires experimental verification |
| Focal length | EXIF/intrinsics; ≈6.06 mm derived — requires experimental verification | `LENS_INFO_AVAILABLE_FOCAL_LENGTHS`, `LENS_FOCAL_LENGTH` — requires experimental verification |
| Sensor information | Not published by Apple (1/1.56-inch, 1.0 µm secondary) — requires experimental verification | `SENSOR_INFO_PHYSICAL_SIZE`, `PIXEL_ARRAY_SIZE`, `ACTIVE_ARRAY_SIZE` — requires experimental verification |
| Frame timestamps | PTS on session clock, convertible to host time via `CMSyncConvertTime`; exposure instant undocumented — requires experimental verification | `SENSOR_TIMESTAMP` = start of exposure of first row; REALTIME source = elapsedRealtimeNanos — requires experimental verification |
| Rolling-shutter readout | Undocumented; estimate via Karpenko calibration — requires experimental verification | `SENSOR_ROLLING_SHUTTER_SKEW`, `SENSOR_READOUT_TIMESTAMP` (API 34) — requires experimental verification |
| Manual exposure/focus | Custom duration/ISO; `lensPosition` 0–1; WB lock (Blackmagic exposes all) — requires experimental verification | `SENSOR_EXPOSURE_TIME`, `SENSOR_SENSITIVITY`, `LENS_FOCUS_DISTANCE` (diopters, if MANUAL_SENSOR) — requires experimental verification |
| IMU access | Core Motion ≈100 Hz observed via wrappers; native maximum unknown; host-time clock — requires experimental verification | SensorEvent on elapsedRealtimeNanos; 200 Hz cap without `HIGH_SAMPLING_RATE_SENSORS` (Android 12+) — requires experimental verification |
| Least-processed video | HEVC/H.264 only; no ProRes/Log/RAW video on standard iPhone 15 — requires experimental verification | RAW_SENSOR stills/streams on some devices; YUV via ImageReader; no ISP bypass guaranteed — requires experimental verification |
| Face/eye tracking | TrueDepth + ARKit face tracking; mm accuracy unpublished — requires experimental verification | Front camera + MediaPipe Face Mesh (monocular, no metric depth) — requires experimental verification |

## Recommendations

1. **The concept is physically viable enough to continue, conditionally.** Target-relative localisation has a theoretical floor (≈0.07–0.35 mm, DERIVED) far below the 10-ring scale. The unresolved threat is OIS/EIS, not resolution. The 0.07–0.23 mm E-001 figure remains a SIMULATION result. The 0.4 mm ISSF electronic-target figure remains an EXTERNAL STANDARD, not a SIGHTLINE requirement.
2. **Architecture change: split the measurement.**
   - Vision gives the absolute, target-relative bore-pixel position at frame rate and low frequency, scored with the ISSF "touch" rule.
   - The gyroscope gives the high-frequency hold, tremor and trigger signature. It is immune to OIS/EIS.
   - The two are fused after a Karpenko-style camera–IMU calibration.
   - Keep "target-relative scoring" (needs no metric calibration) separate from "physical calibration" (sight axis, pose, IMU fusion, multi-device), as the owner asked.
3. **Grip CAD constraints now known:** no magnetic or permeable material near the compass and OIS keep-outs; respect the 121.83°/75.55° camera keep-out cones; confirm lens coordinates by measuring the actual phone.
4. **Three highest-value next experiments:**
   - **E-004a, OIS transfer function (iPhone 15).** Mount the phone on a turntable or tilting jig with a known small rotation (e.g. a micrometer screw at a known lever arm giving 0.1–2 mrad steps, plus a sinusoid at 1, 5 and 10 Hz from a speaker cone or vibration motor). Record simultaneously with Main (Blackmagic "Off") and with the Ultra Wide (no OIS) in separate runs, filming the printed target. Compare image displacement with rotation × focal length. A Main-camera response below the Ultra-Wide response at tremor frequencies means OIS is active despite "Off".
   - **E-004b, Android capability probe plus OIS-sample validation.** Dump CameraCharacteristics. If `OIS_DATA_MODE_ON` exists, verify that pixel shift minus OIS sample matches the gyroscope-predicted shift on the REALTIME clock.
   - **E-002/E-003, real target capture.** Use 1x and 2x, HEVC video and HEIF/DNG stills, locked focus at 10 m, a measured print scale and a fixed tripod. Compare repeatability (static-frame jitter in px) and bias with E-001 synthetic statistics: edge profile width, noise power spectrum, compression block artefacts.

## Caveats

- Apple's DocC reference pages could not be read in full (JavaScript-rendered). iOS introduction versions for most stabilisation modes and the full Discussion text of the intrinsics keys are therefore unconfirmed.
- The iPhone 15 camera coordinates came from text extraction of Apple's drawing. The datum and lens assignment must be read visually.
- Several Android API levels, Apple manual-control API names, NumPy/pytest licences and PEP 639 details are from prior knowledge, not re-verified this session.
- Not researched or found this session: sight dimensions, vernier acuity, SCATT/Rika/Noptel accuracy, sensor noise and printer tolerances. Those items are explicitly UNVERIFIED and must not be cited as facts.
- No source states iPhone 15 rolling-shutter readout time, video PTS exposure instant, maximum native gyroscope rate, IMU part number or ARKit eye-tracking accuracy.

## Unresolved Questions and Experiments That Settle Them

| Question | Experiment |
|---|---|
| Does `.off` (or Blackmagic "Off") disable Main-camera OIS in video? | E-004a: Main vs Ultra-Wide response to known rotation steps and sinusoids |
| Does OIS re-centre during slow sway (high-pass corner)? | E-004a with slow ramps (0.05–0.5 Hz) and holds; check for image drift-back |
| Does the iOS per-frame intrinsic matrix principal point track OIS? | Native build (borrowed Mac/Xcode) logging `CameraIntrinsicMatrix` during E-004a |
| What instant does the iOS video PTS mark; readout time? | LED blinking at known phase, recorded by camera plus a photodiode/second device; Karpenko calibration |
| Native Core Motion maximum rate on iPhone 15; can a logger run alongside the camera app? | Native or logger test with requested 200/500/1000 Hz; foreground/background test |
| Gyroscope noise density / bias stability | Static Allan-variance recording (≥1 h) |
| Android device: OIS OFF honoured? OIS samples? Timestamp source? | E-004b capability probe and dual-mode recordings |
| Real localisation precision and bias (HEVC vs HEIF vs DNG; 1x vs 2x) | E-002/E-003 tripod repeatability, print-scale measurement |
| Sensor read noise / full well | Photon-transfer curve from flat-field DNG pairs |
| Eye-position accuracy at 0.6–0.8 m (ARKit / MediaPipe) | E-006: head phantom on a measured rail vs reported eye positions |
| ISSF 2025/2026 rule text (scoring clause in the current edition) | Download current ISSF General Technical Rules and Pistol Rules from issf-sports.org and quote the clauses |