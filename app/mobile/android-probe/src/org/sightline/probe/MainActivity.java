// SPDX-FileCopyrightText: SIGHTLINE project. Original work; no third-party code.
package org.sightline.probe;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.SystemClock;
import android.util.Size;
import android.view.Surface;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.OutputStream;
import java.lang.reflect.Array;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;

/**
 * SIGHTLINE experiment E-004b: Android Camera2 capability probe and OIS-sample logger.
 *
 * Button 1 dumps every CameraCharacteristics key of every camera (plus motion-sensor facts) to JSON.
 * Buttons 5 and 6 log the gyroscope alone (60 s or 10 min) to CSV: timestamp_ns,x,y,z in rad/s.
 * Buttons 3 and 4 run a 10 s metadata-only capture (no pictures are stored) with optical stabilisation requested ON
 * or OFF, electronic stabilisation OFF and OIS position reporting ON where available, logging per frame the sensor
 * timestamp and the OIS samples, together with raw gyroscope events. "Save" writes the last result to a file the user
 * chooses. Analysis happens off-device: ml/evaluation/e004b_android_probe.py.
 */
public class MainActivity extends Activity implements SensorEventListener {
    private static final int REQ_SAVE = 1, REQ_CAMERA = 2;
    private static final long RECORD_NS = 10_000_000_000L;

    private TextView out;
    private JSONObject last;
    private String lastName = "sightline_probe.json";

    private HandlerThread thread;
    private Handler handler;
    private CameraDevice device;
    private CameraCaptureSession session;
    private ImageReader reader;
    private JSONArray frames, gyro;
    private JSONObject record;
    private long startNs;
    private boolean pendingOisOn;
    private boolean recording;

    // Gyroscope-only log (buttons 5 and 6): primitive buffers, written as CSV when saved.
    private static final int GYRO_MAX = 400_000;
    private long[] gyroT;
    private float[] gyroV;
    private int gyroN;
    private boolean gyroOnly;
    private boolean lastIsGyroCsv;
    private long gyroStopNs;
    private HandlerThread gyroThread;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 24, 24, 24);
        root.addView(button("1. Probe cameras and sensors", new Runnable() { public void run() { probe(); } }));
        root.addView(button("2. Save last result to a file", new Runnable() { public void run() { save(); } }));
        root.addView(button("3. Record 10 s: OIS ON + gyro", new Runnable() { public void run() { startRecord(true); } }));
        root.addView(button("4. Record 10 s: OIS OFF + gyro", new Runnable() { public void run() { startRecord(false); } }));
        root.addView(button("5. Gyro only: 60 s", new Runnable() { public void run() { startGyro(60); } }));
        root.addView(button("6. Gyro only: 10 min (phone at rest)", new Runnable() { public void run() { startGyro(600); } }));
        out = new TextView(this);
        out.setTextIsSelectable(true);
        out.setTextSize(11f);
        out.setText("SIGHTLINE probe 0.1.0 (experiment E-004b).\nTap 1, then 2 to save the JSON. For 3 and 4, hold the "
                + "phone in your hand pointing at any scene and wobble it gently for the whole 10 s, then save.");
        ScrollView scroll = new ScrollView(this);
        scroll.addView(out);
        root.addView(scroll);
        setContentView(root);
    }

    private Button button(String label, final Runnable action) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setOnClickListener(new android.view.View.OnClickListener() {
            public void onClick(android.view.View v) { action.run(); }
        });
        return b;
    }

    private void show(final String text) {
        runOnUiThread(new Runnable() { public void run() { out.setText(text); } });
    }

    // ------------------------------------------------------------------------------------------------------------
    // Value formatting
    // ------------------------------------------------------------------------------------------------------------
    private static Object json(Object v) throws JSONException {
        if (v == null) return JSONObject.NULL;
        if (v instanceof Number || v instanceof Boolean || v instanceof String) return v;
        if (v.getClass().isArray()) {
            JSONArray a = new JSONArray();
            int n = Array.getLength(v);
            for (int i = 0; i < n; i++) a.put(json(Array.get(v, i)));
            return a;
        }
        return String.valueOf(v);
    }

    private static <T> Object get(CameraCharacteristics c, CameraCharacteristics.Key<T> key) throws JSONException {
        try {
            return json(c.get(key));
        } catch (RuntimeException e) {
            return "ERROR: " + e;
        }
    }

    private JSONObject deviceInfo() throws JSONException {
        JSONObject d = new JSONObject();
        d.put("manufacturer", Build.MANUFACTURER);
        d.put("model", Build.MODEL);
        d.put("device", Build.DEVICE);
        d.put("android_release", Build.VERSION.RELEASE);
        d.put("sdk_int", Build.VERSION.SDK_INT);
        d.put("security_patch", Build.VERSION.SDK_INT >= 23 ? Build.VERSION.SECURITY_PATCH : JSONObject.NULL);
        d.put("probe_version", "0.1.0");
        d.put("elapsed_realtime_ns", SystemClock.elapsedRealtimeNanos());
        d.put("wall_clock_ms", System.currentTimeMillis());
        return d;
    }

    // ------------------------------------------------------------------------------------------------------------
    // 1. Capability probe
    // ------------------------------------------------------------------------------------------------------------
    private JSONObject describeCamera(CameraManager mgr, String id) throws JSONException, CameraAccessException {
        CameraCharacteristics c = mgr.getCameraCharacteristics(id);
        JSONObject o = new JSONObject();
        o.put("camera_id", id);
        o.put("lens_facing", get(c, CameraCharacteristics.LENS_FACING));
        o.put("hardware_level", get(c, CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL));
        o.put("capabilities", get(c, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES));
        o.put("focal_lengths_mm", get(c, CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS));
        o.put("apertures", get(c, CameraCharacteristics.LENS_INFO_AVAILABLE_APERTURES));
        o.put("sensor_physical_size_mm", get(c, CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE));
        o.put("active_array", get(c, CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE));
        o.put("pixel_array", get(c, CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE));
        o.put("available_ois_modes", get(c, CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION));
        o.put("available_video_stabilization_modes", get(c, CameraCharacteristics.CONTROL_AVAILABLE_VIDEO_STABILIZATION_MODES));
        o.put("timestamp_source", get(c, CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE));
        o.put("exposure_time_range_ns", get(c, CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE));
        o.put("sensitivity_range", get(c, CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE));
        o.put("max_frame_duration_ns", get(c, CameraCharacteristics.SENSOR_INFO_MAX_FRAME_DURATION));
        o.put("min_focus_distance_diopters", get(c, CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE));
        o.put("hyperfocal_distance_diopters", get(c, CameraCharacteristics.LENS_INFO_HYPERFOCAL_DISTANCE));
        o.put("focus_distance_calibration", get(c, CameraCharacteristics.LENS_INFO_FOCUS_DISTANCE_CALIBRATION));
        o.put("af_modes", get(c, CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES));
        o.put("ae_modes", get(c, CameraCharacteristics.CONTROL_AE_AVAILABLE_MODES));
        o.put("ae_target_fps_ranges", get(c, CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES));
        o.put("sensor_orientation_deg", get(c, CameraCharacteristics.SENSOR_ORIENTATION));
        if (Build.VERSION.SDK_INT >= 23) {
            o.put("lens_intrinsic_calibration", get(c, CameraCharacteristics.LENS_INTRINSIC_CALIBRATION));
            o.put("lens_pose_rotation", get(c, CameraCharacteristics.LENS_POSE_ROTATION));
            o.put("lens_pose_translation", get(c, CameraCharacteristics.LENS_POSE_TRANSLATION));
        }
        if (Build.VERSION.SDK_INT >= 28) {
            o.put("available_ois_data_modes", get(c, CameraCharacteristics.STATISTICS_INFO_AVAILABLE_OIS_DATA_MODES));
            o.put("lens_distortion", get(c, CameraCharacteristics.LENS_DISTORTION));
            o.put("lens_pose_reference", get(c, CameraCharacteristics.LENS_POSE_REFERENCE));
            o.put("distortion_correction_modes", get(c, CameraCharacteristics.DISTORTION_CORRECTION_AVAILABLE_MODES));
            o.put("physical_camera_ids", new JSONArray(c.getPhysicalCameraIds()));
        }
        if (Build.VERSION.SDK_INT >= 30) {
            o.put("zoom_ratio_range", get(c, CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE));
        }
        StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        if (map != null) {
            o.put("yuv_sizes", json(map.getOutputSizes(ImageFormat.YUV_420_888)));
            o.put("raw_sensor_sizes", json(map.getOutputSizes(ImageFormat.RAW_SENSOR)));
            o.put("high_speed_video_sizes", json(map.getHighSpeedVideoSizes()));
        }
        // Rolling-shutter skew, OIS samples and per-frame intrinsics are capture *results*: they are only known by
        // running a capture (buttons 3 and 4). Here: whether the result keys are advertised at all.
        JSONArray resultKeys = new JSONArray();
        for (CaptureResult.Key<?> k : c.getAvailableCaptureResultKeys()) resultKeys.put(k.getName());
        o.put("available_result_keys", resultKeys);
        JSONObject all = new JSONObject();
        for (CameraCharacteristics.Key<?> k : c.getKeys()) all.put(k.getName(), get(c, k));
        o.put("all_characteristics", all);
        return o;
    }

    private JSONObject describeSensor(SensorManager sm, int type, String label) throws JSONException {
        JSONObject o = new JSONObject();
        o.put("type", label);
        Sensor s = sm.getDefaultSensor(type);
        if (s == null) {
            o.put("present", false);
            return o;
        }
        o.put("present", true);
        o.put("name", s.getName());
        o.put("vendor", s.getVendor());
        o.put("min_delay_us", s.getMinDelay());
        o.put("max_rate_hz_from_min_delay", s.getMinDelay() > 0 ? 1e6 / s.getMinDelay() : JSONObject.NULL);
        o.put("max_delay_us", s.getMaxDelay());
        o.put("resolution", s.getResolution());
        o.put("maximum_range", s.getMaximumRange());
        o.put("fifo_max_event_count", s.getFifoMaxEventCount());
        o.put("power_ma", s.getPower());
        return o;
    }

    private void probe() {
        try {
            JSONObject root = new JSONObject();
            root.put("kind", "sightline_camera2_probe");
            root.put("device", deviceInfo());
            CameraManager mgr = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            JSONArray cams = new JSONArray();
            for (String id : mgr.getCameraIdList()) {
                try {
                    cams.put(describeCamera(mgr, id));
                } catch (Exception e) {
                    cams.put(new JSONObject().put("camera_id", id).put("error", String.valueOf(e)));
                }
            }
            root.put("cameras", cams);
            SensorManager sm = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
            JSONArray sensors = new JSONArray();
            sensors.put(describeSensor(sm, Sensor.TYPE_GYROSCOPE, "gyroscope"));
            sensors.put(describeSensor(sm, Sensor.TYPE_GYROSCOPE_UNCALIBRATED, "gyroscope_uncalibrated"));
            sensors.put(describeSensor(sm, Sensor.TYPE_ACCELEROMETER, "accelerometer"));
            root.put("sensors", sensors);
            last = root;
            lastIsGyroCsv = false;
            lastName = "sightline_probe_" + Build.MODEL.replace(' ', '_') + ".json";
            show("Probe done: " + cams.length() + " camera(s). Tap 2 to save.\n\n" + root.toString(1));
        } catch (Exception e) {
            show("Probe failed: " + e);
        }
    }

    // ------------------------------------------------------------------------------------------------------------
    // 2. Save
    // ------------------------------------------------------------------------------------------------------------
    private void save() {
        if (last == null && !lastIsGyroCsv) {
            show("Nothing to save yet. Tap 1, 3, 4, 5 or 6 first.");
            return;
        }
        Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType(lastIsGyroCsv ? "text/csv" : "application/json");
        i.putExtra(Intent.EXTRA_TITLE, lastName);
        startActivityForResult(i, REQ_SAVE);
    }

    @Override
    protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != REQ_SAVE || result != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try (OutputStream os = getContentResolver().openOutputStream(uri)) {
            if (lastIsGyroCsv) {
                // Sensor timestamps are nanoseconds on the elapsedRealtimeNanos clock; rates are rad/s, device axes.
                java.io.BufferedOutputStream bos = new java.io.BufferedOutputStream(os, 1 << 16);
                bos.write("timestamp_ns,x,y,z\n".getBytes(StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder(64);
                for (int k = 0; k < gyroN; k++) {
                    sb.setLength(0);
                    sb.append(gyroT[k]).append(',').append(gyroV[3 * k]).append(',').append(gyroV[3 * k + 1]).append(',')
                            .append(gyroV[3 * k + 2]).append('\n');
                    bos.write(sb.toString().getBytes(StandardCharsets.UTF_8));
                }
                bos.flush();
            } else {
                os.write(last.toString().getBytes(StandardCharsets.UTF_8));
            }
            show("Saved " + lastName + "\n" + uri);
        } catch (Exception e) {
            show("Save failed: " + e);
        }
    }

    // ------------------------------------------------------------------------------------------------------------
    // 3/4. OIS-sample + gyroscope logger (metadata only)
    // ------------------------------------------------------------------------------------------------------------
    private void startRecord(boolean oisOn) {
        if (recording || gyroOnly) return;
        pendingOisOn = oisOn;
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] {Manifest.permission.CAMERA}, REQ_CAMERA);
            return;
        }
        record(oisOn);
    }

    @Override
    public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        if (request == REQ_CAMERA && results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            record(pendingOisOn);
        } else {
            show("Camera permission is needed for the OIS log (no pictures are stored).");
        }
    }

    private static boolean contains(int[] values, int wanted) {
        if (values == null) return false;
        for (int v : values) if (v == wanted) return true;
        return false;
    }

    private String pickCamera(CameraManager mgr) throws CameraAccessException {
        String firstBack = null;
        for (String id : mgr.getCameraIdList()) {
            CameraCharacteristics c = mgr.getCameraCharacteristics(id);
            Integer facing = c.get(CameraCharacteristics.LENS_FACING);
            if (facing == null || facing != CameraCharacteristics.LENS_FACING_BACK) continue;
            if (firstBack == null) firstBack = id;
            if (contains(c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION),
                    CameraCharacteristics.LENS_OPTICAL_STABILIZATION_MODE_ON)) return id;
        }
        return firstBack;
    }

    private void record(final boolean oisOn) {
        try {
            final CameraManager mgr = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            final String id = pickCamera(mgr);
            if (id == null) {
                show("No back camera found.");
                return;
            }
            final CameraCharacteristics c = mgr.getCameraCharacteristics(id);
            final boolean oisModeAvailable = contains(c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION),
                    oisOn ? CameraCharacteristics.LENS_OPTICAL_STABILIZATION_MODE_ON : CameraCharacteristics.LENS_OPTICAL_STABILIZATION_MODE_OFF);
            final boolean oisDataAvailable = Build.VERSION.SDK_INT >= 28
                    && contains(c.get(CameraCharacteristics.STATISTICS_INFO_AVAILABLE_OIS_DATA_MODES),
                            CameraCharacteristics.STATISTICS_OIS_DATA_MODE_ON);
            Size size = new Size(640, 480);
            StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            if (map != null && map.getOutputSizes(ImageFormat.YUV_420_888) != null) {
                List<Size> sizes = java.util.Arrays.asList(map.getOutputSizes(ImageFormat.YUV_420_888));
                if (!sizes.contains(size) && !sizes.isEmpty()) {
                    size = sizes.get(0);
                    for (Size s : sizes) if ((long) s.getWidth() * s.getHeight() < (long) size.getWidth() * size.getHeight()) size = s;
                }
            }
            frames = new JSONArray();
            gyro = new JSONArray();
            record = new JSONObject();
            record.put("kind", "sightline_ois_log");
            record.put("device", deviceInfo());
            record.put("camera_id", id);
            record.put("stream_size", size.toString());
            JSONObject req = new JSONObject();
            req.put("ois_requested", oisOn ? "ON" : "OFF");
            req.put("ois_mode_listed_as_available", oisModeAvailable);
            req.put("ois_data_mode_on_available", oisDataAvailable);
            req.put("video_stabilization_requested", "OFF");
            record.put("request", req);
            record.put("timestamp_source", get(c, CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE));
            record.put("active_array", get(c, CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE));
            record.put("focal_lengths_mm", get(c, CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS));
            record.put("sensor_physical_size_mm", get(c, CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE));
            if (Build.VERSION.SDK_INT >= 23) {
                record.put("lens_intrinsic_calibration_static", get(c, CameraCharacteristics.LENS_INTRINSIC_CALIBRATION));
            }

            thread = new HandlerThread("probe-camera");
            thread.start();
            handler = new Handler(thread.getLooper());
            reader = ImageReader.newInstance(size.getWidth(), size.getHeight(), ImageFormat.YUV_420_888, 3);
            reader.setOnImageAvailableListener(new ImageReader.OnImageAvailableListener() {
                public void onImageAvailable(ImageReader r) {
                    Image img = r.acquireLatestImage();
                    if (img != null) img.close();   // pixels are discarded: this is a metadata-only log
                }
            }, handler);
            SensorManager sm = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
            Sensor g = sm.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
            if (g != null) {
                sm.registerListener(this, g, SensorManager.SENSOR_DELAY_FASTEST, handler);
                record.put("gyro_sensor", g.getName());
            }
            recording = true;
            show("Recording 10 s with OIS " + (oisOn ? "ON" : "OFF") + " requested...\nWobble the phone gently.");
            mgr.openCamera(id, new CameraDevice.StateCallback() {
                public void onOpened(CameraDevice cam) {
                    device = cam;
                    try {
                        final Surface surface = reader.getSurface();
                        final CaptureRequest.Builder b = cam.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
                        b.addTarget(surface);
                        b.set(CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE, CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE_OFF);
                        if (oisModeAvailable) {
                            b.set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE, oisOn
                                    ? CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_ON : CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_OFF);
                        }
                        if (oisDataAvailable) {
                            b.set(CaptureRequest.STATISTICS_OIS_DATA_MODE, CaptureRequest.STATISTICS_OIS_DATA_MODE_ON);
                        }
                        cam.createCaptureSession(Collections.singletonList(surface), new CameraCaptureSession.StateCallback() {
                            public void onConfigured(CameraCaptureSession s) {
                                session = s;
                                try {
                                    startNs = SystemClock.elapsedRealtimeNanos();
                                    record.put("start_elapsed_realtime_ns", startNs);
                                    s.setRepeatingRequest(b.build(), new CameraCaptureSession.CaptureCallback() {
                                        public void onCaptureCompleted(CameraCaptureSession cs, CaptureRequest r, TotalCaptureResult res) {
                                            logFrame(res);
                                            if (SystemClock.elapsedRealtimeNanos() - startNs > RECORD_NS) finish(null);
                                        }
                                    }, handler);
                                } catch (Exception e) {
                                    finish("capture failed: " + e);
                                }
                            }
                            public void onConfigureFailed(CameraCaptureSession s) {
                                finish("session configuration failed");
                            }
                        }, handler);
                    } catch (Exception e) {
                        finish("camera setup failed: " + e);
                    }
                }
                public void onDisconnected(CameraDevice cam) { finish("camera disconnected"); }
                public void onError(CameraDevice cam, int error) { finish("camera error " + error); }
            }, handler);
        } catch (SecurityException e) {
            recording = false;
            show("Camera permission missing: " + e);
        } catch (Exception e) {
            finish("record failed: " + e);
        }
    }

    private void logFrame(TotalCaptureResult res) {
        if (!recording) return;
        try {
            JSONObject f = new JSONObject();
            f.put("frame_number", res.getFrameNumber());
            f.put("sensor_timestamp_ns", json(res.get(CaptureResult.SENSOR_TIMESTAMP)));
            f.put("exposure_time_ns", json(res.get(CaptureResult.SENSOR_EXPOSURE_TIME)));
            f.put("frame_duration_ns", json(res.get(CaptureResult.SENSOR_FRAME_DURATION)));
            f.put("rolling_shutter_skew_ns", json(res.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW)));
            f.put("ois_mode", json(res.get(CaptureResult.LENS_OPTICAL_STABILIZATION_MODE)));
            f.put("video_stabilization_mode", json(res.get(CaptureResult.CONTROL_VIDEO_STABILIZATION_MODE)));
            f.put("focal_length_mm", json(res.get(CaptureResult.LENS_FOCAL_LENGTH)));
            f.put("focus_distance_diopters", json(res.get(CaptureResult.LENS_FOCUS_DISTANCE)));
            f.put("lens_state", json(res.get(CaptureResult.LENS_STATE)));
            if (Build.VERSION.SDK_INT >= 23) {
                f.put("lens_intrinsic_calibration", json(res.get(CaptureResult.LENS_INTRINSIC_CALIBRATION)));
            }
            if (Build.VERSION.SDK_INT >= 28) {
                f.put("ois_data_mode", json(res.get(CaptureResult.STATISTICS_OIS_DATA_MODE)));
                android.hardware.camera2.params.OisSample[] samples = res.get(CaptureResult.STATISTICS_OIS_SAMPLES);
                if (samples != null) {
                    JSONArray a = new JSONArray();
                    for (android.hardware.camera2.params.OisSample s : samples) {
                        a.put(new JSONArray().put(s.getTimestamp()).put((double) s.getXshift()).put((double) s.getYshift()));
                    }
                    f.put("ois_samples", a);   // [timestamp_ns, x_shift_px, y_shift_px]
                } else {
                    f.put("ois_samples", JSONObject.NULL);
                }
            }
            frames.put(f);
        } catch (JSONException ignored) {
        }
    }

    @Override
    public void onSensorChanged(SensorEvent e) {
        if (gyroOnly) {
            if (gyroN < GYRO_MAX) {
                gyroT[gyroN] = e.timestamp;
                gyroV[3 * gyroN] = e.values[0];
                gyroV[3 * gyroN + 1] = e.values[1];
                gyroV[3 * gyroN + 2] = e.values[2];
                gyroN++;
            }
            if (SystemClock.elapsedRealtimeNanos() > gyroStopNs || gyroN >= GYRO_MAX) stopGyro(null);
            return;
        }
        if (!recording || gyro == null) return;
        try {
            gyro.put(new JSONArray().put(e.timestamp).put((double) e.values[0]).put((double) e.values[1]).put((double) e.values[2]));
        } catch (JSONException ignored) {
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }

    private synchronized void finish(String error) {
        if (!recording) return;
        recording = false;
        ((SensorManager) getSystemService(Context.SENSOR_SERVICE)).unregisterListener(this);
        try {
            if (session != null) session.close();
        } catch (Exception ignored) {
        }
        try {
            if (device != null) device.close();
        } catch (Exception ignored) {
        }
        try {
            if (reader != null) reader.close();
        } catch (Exception ignored) {
        }
        if (thread != null) thread.quitSafely();
        session = null;
        device = null;
        reader = null;
        try {
            record.put("stop_elapsed_realtime_ns", SystemClock.elapsedRealtimeNanos());
            record.put("error", error == null ? JSONObject.NULL : error);
            record.put("frames", frames);
            record.put("gyro", gyro);   // [timestamp_ns, x, y, z] rad/s, device axes
            last = record;
            lastIsGyroCsv = false;
            lastName = "sightline_ois_log_" + record.getJSONObject("request").getString("ois_requested") + "_"
                    + Build.MODEL.replace(' ', '_') + ".json";
            int withSamples = 0;
            for (int i = 0; i < frames.length(); i++) {
                if (frames.getJSONObject(i).optJSONArray("ois_samples") != null
                        && frames.getJSONObject(i).getJSONArray("ois_samples").length() > 0) withSamples++;
            }
            show((error == null ? "Recording done." : "Recording stopped: " + error) + "\nFrames: " + frames.length()
                    + "\nFrames with OIS samples: " + withSamples + "\nGyro events: " + gyro.length()
                    + "\n\nTap 2 to save " + lastName);
        } catch (JSONException e) {
            show("Could not assemble the log: " + e);
        }
    }

    // ------------------------------------------------------------------------------------------------------------
    // 5/6. Gyroscope-only log
    // ------------------------------------------------------------------------------------------------------------
    private void startGyro(int seconds) {
        if (recording || gyroOnly) return;
        SensorManager sm = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        Sensor g = sm.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        if (g == null) {
            show("This device reports no gyroscope.");
            return;
        }
        gyroT = new long[GYRO_MAX];
        gyroV = new float[3 * GYRO_MAX];
        gyroN = 0;
        gyroStopNs = SystemClock.elapsedRealtimeNanos() + seconds * 1_000_000_000L;
        gyroThread = new HandlerThread("probe-gyro");
        gyroThread.start();
        gyroOnly = true;
        sm.registerListener(this, g, SensorManager.SENSOR_DELAY_FASTEST, new Handler(gyroThread.getLooper()));
        show("Logging the gyroscope for " + seconds + " s (" + g.getName() + ").\nKeep this app open and the screen on.");
    }

    private synchronized void stopGyro(String note) {
        if (!gyroOnly) return;
        gyroOnly = false;
        ((SensorManager) getSystemService(Context.SENSOR_SERVICE)).unregisterListener(this);
        if (gyroThread != null) gyroThread.quitSafely();
        lastIsGyroCsv = true;
        lastName = "sightline_gyro_" + Build.MODEL.replace(' ', '_') + ".csv";
        double seconds = gyroN > 1 ? (gyroT[gyroN - 1] - gyroT[0]) * 1e-9 : 0.0;
        show((note == null ? "Gyro log done." : "Gyro log stopped: " + note) + "\nSamples: " + gyroN + "\nDuration: "
                + String.format(java.util.Locale.US, "%.1f", seconds) + " s\nMean rate: "
                + String.format(java.util.Locale.US, "%.1f", seconds > 0 ? (gyroN - 1) / seconds : 0.0) + " Hz\n\nTap 2 to save "
                + lastName);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (recording) finish("activity paused");
        if (gyroOnly) stopGyro("activity paused");
    }
}
