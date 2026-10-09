"""Per-frame target tracking on synthetic sequences with exact ground truth (SIMULATED), and video reading."""

import math

import cv2
import numpy as np
import pytest

from app.calibration.camera import CameraModel
from app.vision.motion import FRAME_FIELDS, TargetTracker, track_frames, valid_arrays, write_frames_csv
from app.vision.video import iter_frames, probe_video
from ml.datasets.synthetic_sequence import hypothetical_stabiliser, render_sequence

CAM = CameraModel.from_hfov(3840, 2160, 67.0)        # ASSUMED field of view; ~3.45 mm/px at 10 m


def _sequence(theta_mrad, seed=0):
    theta = np.zeros((len(theta_mrad), 2))
    theta[:, 1] = np.asarray(theta_mrad) * 1e-3
    frames, centres = render_sequence(CAM, theta, np.random.default_rng(seed))
    return [(i, i / 30.0, f) for i, f in enumerate(frames)], centres


def test_tracker_follows_known_sub_pixel_motion():
    items, centres = _sequence([0.0, 0.1, 0.25, 0.5, 1.0, 2.0, -1.0, 0.0])
    recs = track_frames(items)
    assert all(r.valid for r in recs)
    for name, tol in (("ellipse", 0.05), ("moments", 0.05), ("centroid", 0.25)):
        _, _, xy = valid_arrays(recs, name)
        assert np.abs(xy - centres).max() < tol, name
    _, _, shift = valid_arrays(recs, "phase")
    assert np.abs(shift - (centres - centres[0])).max() < 0.2          # secondary estimator: coarser, same sign
    assert min(r.confidence for r in recs) > 0.8
    # 1 mrad of rotation moves the image by f_px * 1e-3 pixels (2.90 px here)
    assert abs(centres[4, 1] - centres[0, 1]) == pytest.approx(CAM.fy * math.tan(1e-3), rel=1e-3)


def test_unusable_frames_are_marked_invalid_not_interpolated():
    items, _ = _sequence([0.0, 0.2, 0.4, 0.6])
    blank = np.full_like(items[2][2], 128)
    items[2] = (2, items[2][1], blank)
    recs = track_frames(items)
    assert [r.valid for r in recs] == [True, True, False, True]
    assert recs[2].reason and math.isnan(recs[2].x)
    idx, t, xy = valid_arrays(recs)
    assert idx.tolist() == [0, 1, 3] and len(xy) == 3


def test_no_target_is_reported_and_hint_selects_among_detections():
    tracker = TargetTracker()
    rec = tracker.process(0, 0.0, np.full((120, 160), 90, np.uint8))
    assert not rec.valid and rec.reason == "target not detected"
    items, centres = _sequence([0.0])
    img = cv2.copyMakeBorder(items[0][2], 0, 0, 0, 256, cv2.BORDER_REFLECT)   # mirrored second target on the right
    left = TargetTracker(hint_px=(centres[0, 0], centres[0, 1])).process(0, 0.0, img)
    right = TargetTracker(hint_px=(511 - centres[0, 0], centres[0, 1])).process(0, 0.0, img)
    assert left.valid and right.valid and right.x - left.x > 100


def test_frames_csv_has_every_field(tmp_path):
    items, _ = _sequence([0.0, 0.5])
    recs = track_frames(items)
    path = tmp_path / "frames.csv"
    write_frames_csv(recs, path, extra={"camera": "synthetic"}, per_frame={"residual": [0.0, 0.1]})
    header = path.read_text().splitlines()[0].split(",")
    assert header == FRAME_FIELDS + ["camera", "residual"]
    assert len(path.read_text().splitlines()) == 3


def test_hypothetical_stabiliser_limits():
    theta = np.concatenate([np.zeros(10), np.ones(300)])
    assert np.allclose(hypothetical_stabiliser(theta, 30.0, 0.0), 0.0)                 # pure lock cancels everything
    recentring = hypothetical_stabiliser(theta, 30.0, 0.5)
    assert abs(recentring[10]) < 0.15 and recentring[-1] == pytest.approx(1.0, abs=1e-3)  # cancels, then re-centres
    assert np.allclose(hypothetical_stabiliser(theta, 30.0, 0.5, gain=0.0), theta)       # gain 0 = no stabiliser


def test_video_roundtrip_reports_frames_and_timestamps(tmp_path):
    items, centres = _sequence([0.0, 0.5, 1.0, 1.5, 2.0, 1.0, 0.0, -1.0])
    path = str(tmp_path / "clip.avi")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (256, 256), False)
    if not writer.isOpened():
        pytest.skip("no MJPG encoder in this OpenCV build")
    for _, _, f in items:
        writer.write(f)
    writer.release()
    meta = probe_video(path)
    assert (meta["width"], meta["height"]) == (256, 256)
    got = list(iter_frames(path))
    assert len(got) == len(items)
    times = np.array([g[1] for g in got])
    assert np.diff(times) == pytest.approx(1 / 30.0, abs=2e-3)
    recs = track_frames((i, t, img) for i, t, img, _ in got)
    _, _, xy = valid_arrays(recs)
    assert np.abs(xy - centres).max() < 0.1                                # MJPG-compressed, still sub-pixel
