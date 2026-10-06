"""Read video files as (frame index, timestamp, image) and report container metadata.

Decoding uses OpenCV (already a dependency). If the ``ffprobe`` command-line tool is installed it is used, as an
external tool, for two things OpenCV does not report reliably: per-frame presentation timestamps (phone video is
often variable-frame-rate) and stream metadata (codec, colour transfer, rotation, device tags). Without ffprobe the
reader falls back to OpenCV's own timestamps and says so in ``timestamp_source``.

Nothing here interprets the image; see ``app/vision/motion.py``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np

HDR_TRANSFERS = ("arib-std-b67", "smpte2084")  # HLG and PQ: not a power-law gamma; violates the capture protocol


def _ffprobe(args: list[str]) -> str | None:
    exe = shutil.which("ffprobe")
    if exe is None:
        return None
    try:
        return subprocess.run([exe, "-v", "error", *args], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def _ratio(text: str | None) -> float | None:
    if not text or text in ("0/0", "N/A"):
        return None
    num, _, den = text.partition("/")
    try:
        return float(num) / float(den) if den else float(num)
    except (ValueError, ZeroDivisionError):
        return None


def probe_video(path: str | Path) -> dict:
    """Container/stream metadata. Keys are present with ``None`` when the information is unavailable."""
    path = str(path)
    meta: dict = {"path": path, "source": "opencv", "codec": None, "width": None, "height": None, "fps_avg": None,
                  "fps_nominal": None, "n_frames": None, "duration_s": None, "rotation_deg": None, "pix_fmt": None,
                  "color_transfer": None, "bit_rate": None, "creation_time": None, "tags": {}}
    out = _ffprobe(["-select_streams", "v:0", "-show_streams", "-show_format", "-of", "json", path])
    if out:
        try:
            info = json.loads(out)
            st = info["streams"][0]
        except (ValueError, KeyError, IndexError):
            st = None
        if st is not None:
            fmt = info.get("format", {})
            rotation = None
            for sd in st.get("side_data_list", []):
                if "rotation" in sd:
                    rotation = float(sd["rotation"])
            tags = {**fmt.get("tags", {}), **st.get("tags", {})}
            if rotation is None and "rotate" in tags:
                rotation = float(tags["rotate"])
            meta.update(
                source="ffprobe", codec=st.get("codec_name"), width=st.get("width"), height=st.get("height"),
                fps_avg=_ratio(st.get("avg_frame_rate")), fps_nominal=_ratio(st.get("r_frame_rate")),
                n_frames=int(st["nb_frames"]) if str(st.get("nb_frames", "")).isdigit() else None,
                duration_s=float(st.get("duration") or fmt.get("duration") or "nan"),
                rotation_deg=rotation, pix_fmt=st.get("pix_fmt"), color_transfer=st.get("color_transfer"),
                bit_rate=int(st["bit_rate"]) if str(st.get("bit_rate", "")).isdigit() else None,
                creation_time=tags.get("creation_time"), tags=tags)
            return meta
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise OSError(f"cannot open video: {path}")
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    meta.update(codec="".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4)).strip("\x00") or None,
                width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                fps_avg=float(cap.get(cv2.CAP_PROP_FPS)) or None,
                n_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or None)
    cap.release()
    return meta


def presentation_timestamps(path: str | Path) -> np.ndarray | None:
    """Presentation timestamps (seconds) of every video frame in display order, from ffprobe; None if unavailable."""
    out = _ffprobe(["-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of", "csv=p=0", str(path)])
    if not out:
        return None
    vals = []
    for line in out.splitlines():
        token = line.strip().strip(",")
        if token and token != "N/A":
            try:
                vals.append(float(token))
            except ValueError:
                return None
    return np.sort(np.asarray(vals)) if vals else None  # packets are in decode order; sorting gives display order


def iter_frames(path: str | Path, start_s: float | None = None, end_s: float | None = None,
                ) -> Iterator[tuple[int, float, np.ndarray, str]]:
    """Yield ``(frame_index, timestamp_s, image_bgr, timestamp_source)`` for frames with start_s <= t <= end_s.

    ``timestamp_source`` is ``"pts"`` (ffprobe presentation timestamps) or ``"opencv"`` (decoder position; less
    reliable for variable-frame-rate files). Frames are never synthesised: a decode failure ends the iteration.
    """
    pts = presentation_timestamps(path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise OSError(f"cannot open video: {path}")
    try:
        idx = 0
        while True:
            pos_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            ok, frame = cap.read()
            if not ok:
                break
            if pts is not None and idx < len(pts):
                t, src = float(pts[idx]), "pts"
            else:
                t, src = float(pos_ms) / 1000.0, "opencv"
            if end_s is not None and t > end_s:
                break
            if start_s is None or t >= start_s:
                yield idx, t, frame, src
            idx += 1
    finally:
        cap.release()
