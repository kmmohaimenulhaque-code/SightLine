"""E-004b off-device analysis, on fabricated probe files (SYNTHETIC — no claim about any device)."""

import numpy as np

from ml.evaluation import e004b_android_probe as b

RESULT_KEYS = ["android.sensor.timestamp", "android.statistics.oisSamples", "android.sensor.rollingShutterSkew",
               "android.lens.intrinsicCalibration"]


def _probe():
    main = {"camera_id": "0", "lens_facing": 1, "hardware_level": 1, "capabilities": [0, 1, 3], "focal_lengths_mm": [6.1],
            "available_ois_modes": [0, 1], "available_video_stabilization_modes": [0, 1], "available_ois_data_modes": [0, 1],
            "timestamp_source": 1, "available_result_keys": RESULT_KEYS,
            "lens_intrinsic_calibration": [3000.0, 3000.0, 2000.0, 1500.0, 0.0]}
    wide = {"camera_id": "2", "lens_facing": 1, "hardware_level": 0, "capabilities": [0], "focal_lengths_mm": [2.2],
            "available_ois_modes": [0], "available_video_stabilization_modes": [0, 1], "timestamp_source": 0,
            "available_result_keys": ["android.sensor.timestamp"]}
    front = {"camera_id": "1", "lens_facing": 0, "hardware_level": 0, "available_ois_modes": [0]}
    return {"kind": "sightline_camera2_probe", "device": {"manufacturer": "Fabricated", "model": "Test", "sdk_int": 34,
            "android_release": "14"}, "cameras": [main, front, wide, {"camera_id": "9", "error": "boom"}],
            "sensors": [{"type": "gyroscope", "present": True, "name": "g", "vendor": "v", "max_rate_hz_from_min_delay": 400.0}]}


def test_capabilities_are_read_from_the_file_not_assumed():
    rep = b.capabilities_report(_probe(), "SYNTHETIC")
    assert rep["status"]["evidence_class"] == "SIMULATED"
    cams = {c["camera_id"]: c for c in rep["cameras"]}
    assert set(cams) == {"0", "1", "2"}                                   # the camera that failed is not invented
    assert cams["0"]["ois_controllable"] and cams["0"]["ois_samples_available"] and cams["0"]["timestamp_source"] == "REALTIME"
    assert cams["0"]["f_px_reported"]["value"] == 3000.0 and cams["0"]["manual_exposure"] and cams["0"]["raw_capability"]
    assert not cams["2"]["ois_present"] and cams["2"]["ois_samples_available"] is False
    assert cams["2"]["timestamp_source"] == "UNKNOWN" and not cams["2"]["rolling_shutter_skew_reported"]
    v = rep["verdict"]
    assert v["ois_off_requestable_on"] == ["0"] and v["back_cameras_without_ois"] == ["2"] and v["ois_samples_on"] == ["0"]
    md = b.capabilities_markdown(rep)
    assert "Scope: this device and build only" in md and "NOT experimental evidence" in md
    assert b.capabilities_report({"kind": "other"})["status"]["experiment_status"] == "INVALID"


def _ois_log(requested, lens_gain, rng, f_px=3000.0, seconds=10.0):
    """Fabricated log: hand wobble about gyro x and y; the lens shift is -lens_gain * f_px * angle (plus noise)."""
    t0 = 5_000.0
    gt = t0 + np.arange(int(seconds * 400)) / 400.0
    ang = np.column_stack([3e-3 * np.sin(2 * np.pi * 2.1 * gt), 2e-3 * np.sin(2 * np.pi * 3.4 * gt + 1.0), 0 * gt])
    omega = np.gradient(ang, gt, axis=0) + rng.normal(0, 1e-3, ang.shape)
    frames = []
    for k in range(int(seconds * 30)):
        ts = t0 + k / 30.0
        st = ts + np.arange(6) / 180.0
        a = np.column_stack([3e-3 * np.sin(2 * np.pi * 2.1 * st), 2e-3 * np.sin(2 * np.pi * 3.4 * st + 1.0)])
        shift = -lens_gain * f_px * a[:, ::-1] + rng.normal(0, 0.01, (6, 2))     # image x follows gyro y, y follows x
        frames.append({"frame_number": k, "sensor_timestamp_ns": int(ts * 1e9), "ois_mode": 1 if requested == "ON" else 0,
                       "video_stabilization_mode": 0, "exposure_time_ns": 8_000_000, "rolling_shutter_skew_ns": 20_000_000,
                       "ois_samples": [[int(s * 1e9), float(x), float(y)] for s, (x, y) in zip(st, shift)]})
    return {"kind": "sightline_ois_log", "device": {"model": "Test"}, "camera_id": "0", "timestamp_source": 1,
            "request": {"ois_requested": requested}, "error": None, "lens_intrinsic_calibration_static": [f_px, f_px, 2000, 1500, 0],
            "start_elapsed_realtime_ns": int(t0 * 1e9), "stop_elapsed_realtime_ns": int((t0 + seconds) * 1e9),
            "frames": frames, "gyro": [[int(t * 1e9), *map(float, w)] for t, w in zip(gt, omega)]}


def test_ois_log_scale_axes_and_timebase_are_recovered():
    rep = b.ois_log_report(_ois_log("ON", 0.9, np.random.default_rng(0)), "SYNTHETIC")
    f = rep["findings"]
    assert abs(f["frames"]["rate_hz"] - 30.0) < 0.01
    assert all(f["timebase"][k] for k in ("frame_timestamps_in_elapsed_realtime_window",
                                          "gyro_timestamps_in_elapsed_realtime_window", "ois_timestamps_within_frame_span"))
    og = f["ois_vs_gyro"]
    assert og["r2"] > 0.95 and abs(og["compensation_fraction_x"] - 0.9) < 0.05 and abs(og["compensation_fraction_y"] - 0.9) < 0.05
    m = np.array(og["px_per_rad_matrix_rows_gyro_xyz_cols_ois_xy"])
    assert m[1, 0] < -2000 and m[0, 1] < -2000 and abs(m[0, 0]) < 300   # sign and axis pairing are measured, not assumed


def test_ois_off_is_judged_from_the_lens_samples():
    rng = np.random.default_rng(1)
    honoured = b.ois_log_report(_ois_log("OFF", 0.0, rng), "SYNTHETIC")["findings"]
    ignored = b.ois_log_report(_ois_log("OFF", 0.9, rng), "SYNTHETIC")["findings"]
    assert honoured["ois_off_honoured"] is True and ignored["ois_off_honoured"] is False
    no_samples = _ois_log("OFF", 0.0, rng)
    for fr in no_samples["frames"]:
        fr["ois_samples"] = None
    assert b.ois_log_report(no_samples, "SYNTHETIC")["findings"]["ois_off_honoured"] is None   # cannot be judged


def test_a_failed_recording_is_invalid():
    log = _ois_log("ON", 0.9, np.random.default_rng(2), seconds=0.5)
    assert b.ois_log_report(log, "TEAM_COLLECTED")["status"]["experiment_status"] == "INVALID"
    log = _ois_log("ON", 0.9, np.random.default_rng(2))
    log["error"] = "camera error 4"
    assert "camera error" in b.ois_log_report(log, "TEAM_COLLECTED")["status"]["reason"]
