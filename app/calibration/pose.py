"""Target pose relative to the camera, and the simulated bore-axis geometry.

Frames: target T (x right, y up, z toward the shooter, mm), camera C (OpenCV, mm). ``R`` maps T vectors into C and
``t`` is the target origin expressed in C, so X_C = R @ X_T + t.

The simulated bore axis is the ray through the camera centre and the bore pixel p_b (ARCHITECTURE.md D-002).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .camera import CameraModel

R_FRONTAL = np.diag([1.0, -1.0, -1.0])  # fronto-parallel target: T x->C x, T y(up)->C -y(down), T z->C -z


def rot_x(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def rot_y(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rot_z(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


@dataclass(frozen=True)
class TargetPose:
    R: np.ndarray  # 3x3, target -> camera
    t: np.ndarray  # (3,), target origin in camera frame, mm

    @property
    def normal_c(self) -> np.ndarray:
        """Target plane normal (target +z, toward the shooter) expressed in the camera frame."""
        return self.R[:, 2]

    def target_to_camera(self, xy_mm: np.ndarray) -> np.ndarray:
        xy = np.atleast_2d(np.asarray(xy_mm, dtype=float))
        pts = np.concatenate([xy, np.zeros((xy.shape[0], 1))], axis=1)
        return pts @ self.R.T + self.t

    def intersect_rays(self, rays_c: np.ndarray) -> np.ndarray:
        """Intersect rays from the camera centre with the target plane; return target-frame (x, y) in mm."""
        rays = np.atleast_2d(np.asarray(rays_c, dtype=float))
        n = self.normal_c
        denom = rays @ n
        if np.any(np.abs(denom) < 1e-12):
            raise ValueError("ray parallel to the target plane")
        s = (n @ self.t) / denom
        pts_c = rays * s[:, None]
        pts_t = (pts_c - self.t) @ self.R  # R^T (X - t)
        return pts_t[:, :2]

    def project(self, camera: CameraModel, xy_mm: np.ndarray) -> np.ndarray:
        return camera.project(self.target_to_camera(xy_mm))


def target_rotation(yaw_deg: float = 0.0, pitch_deg: float = 0.0, roll_deg: float = 0.0) -> np.ndarray:
    """Rotation T -> C for a target tilted by yaw (about target y) and pitch (about target x), seen with an apparent
    in-image rotation ``roll_deg`` (equivalent to rolling the phone by -roll_deg about the optical axis)."""
    return rot_z(math.radians(roll_deg)) @ R_FRONTAL @ rot_y(math.radians(yaw_deg)) @ rot_x(math.radians(pitch_deg))


def pose_from_aim(
    camera: CameraModel,
    bore_px: tuple[float, float],
    impact_xy_mm: tuple[float, float],
    distance_mm: float,
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    roll_deg: float = 0.0,
) -> TargetPose:
    """Place the target so that the bore ray through ``bore_px`` hits target point ``impact_xy_mm`` at a range of
    ``distance_mm`` along that ray. This is how the synthetic generator creates exact ground truth."""
    R = target_rotation(yaw_deg, pitch_deg, roll_deg)
    b = camera.pixel_rays(np.asarray(bore_px, dtype=float)[None, :])[0]
    p_hit = distance_mm * b
    t = p_hit - R @ np.array([impact_xy_mm[0], impact_xy_mm[1], 0.0])
    return TargetPose(R=R, t=t)


def bore_impact_mm(camera: CameraModel, pose: TargetPose, bore_px: tuple[float, float]) -> np.ndarray:
    """Exact simulated impact (target mm) of the bore ray — the geometric ground truth."""
    ray = camera.pixel_rays(np.asarray(bore_px, dtype=float)[None, :])
    return pose.intersect_rays(ray)[0]
