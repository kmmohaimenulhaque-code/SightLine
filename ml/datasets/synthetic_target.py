"""Synthetic ISSF 10 m air-pistol target images with exact ground truth (category SYNTHETIC).

Physical model (ARCHITECTURE.md D-014):

* Geometry: analytic ray casting through ``CameraModel`` (pinhole + radial distortion) onto the target plane placed by
  ``pose_from_aim`` so that the bore ray hits a chosen point — the simulated impact is exact by construction.
* Appearance: ISSF ring geometry with analytic area coverage for the black edge, ring lines and card edge, averaged
  over a supersampled pixel aperture (thin 0.15 mm lines are integrated, not point-sampled).
* Optics: Gaussian PSF; linear motion blur (approximation: image-plane translation over the exposure — valid because
  the target region is small relative to the frame). The ground truth is the mid-exposure geometry.
* Sensor: shot noise (Poisson in electrons) + Gaussian read noise, ADC quantisation, power-law gamma, optional JPEG.

Everything here is SIMULATED. Outputs must never be presented as real measurements (DATASET_SPEC.md §1).

``expected_canvas`` exposes the noise-free model mean (used by the Cramer-Rao analysis, E-005) and ``bounds`` fixes
the canvas window so that frame sequences share one pixel grid (used by the E-004a synthetic sanity check).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import cv2
import numpy as np

from app.calibration.camera import CameraModel
from app.calibration.ellipse import fit_ellipse_direct
from app.calibration.pose import TargetPose, bore_impact_mm, pose_from_aim
from app.scoring.issf import (
    BLACK_LINE_RADII_MM,
    BLACK_RADIUS_MM,
    RING_RADII_MM,
    WHITE_LINE_RADII_MM,
    score_shot,
)

GENERATOR_NAME = "sightline.synthetic_target"
GENERATOR_VERSION = "0.1.1"  # 0.1.1: fixed canvas bounds + noise-free expectation; output bit-identical to 0.1.0


@dataclass(frozen=True)
class Appearance:
    white: float = 0.85                 # card reflectance (ASSUMPTION)
    black: float = 0.04                 # print black reflectance (ASSUMPTION)
    wall: float = 0.35                  # background reflectance (ASSUMPTION)
    ring_line_mm: float = 0.15          # ISSF allows 0.1-0.2 mm (VERIFIED range; value ASSUMPTION)
    card_half_mm: float = 85.0          # 170 mm card = ISSF minimum visible size


@dataclass(frozen=True)
class Degradation:
    psf_sigma_px: float = 0.7           # lens + demosaic blur (ASSUMPTION)
    motion_blur_px: float = 0.0         # blur length over the exposure
    motion_blur_angle_deg: float = 0.0
    electrons_per_unit: float = 3000.0  # electrons collected for reflectance 1.0 (exposure x illumination; SNR knob)
    read_noise_e: float = 2.0
    adc_bits: int = 10
    gain_headroom: float = 0.95         # reflectance 1.0 maps to this fraction of full scale
    gamma: float = 2.2
    jpeg_quality: int | None = 90


@dataclass(frozen=True)
class SceneSpec:
    camera: CameraModel
    bore_px: tuple[float, float]
    impact_xy_mm: tuple[float, float]
    distance_mm: float = 10000.0
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    appearance: Appearance = field(default_factory=Appearance)
    degradation: Degradation = field(default_factory=Degradation)

    def to_dict(self) -> dict:
        return {
            "camera": self.camera.to_dict(),
            "bore_px": list(self.bore_px),
            "impact_xy_mm": list(self.impact_xy_mm),
            "distance_mm": self.distance_mm,
            "yaw_deg": self.yaw_deg,
            "pitch_deg": self.pitch_deg,
            "roll_deg": self.roll_deg,
            "appearance": asdict(self.appearance),
            "degradation": asdict(self.degradation),
        }


@dataclass
class SyntheticSample:
    image: np.ndarray            # uint8, gamma-encoded grayscale
    origin_px: tuple[int, int]   # (u0, v0) of the canvas in full-image coordinates
    bore_px_canvas: tuple[float, float]
    ground_truth: dict
    parameters: dict


# ----------------------------------------------------------------------------------------------------------------------
def _overlap(r: np.ndarray, footprint: float, centre: float, width: float) -> np.ndarray:
    lo = np.maximum(r - footprint / 2.0, centre - width / 2.0)
    hi = np.minimum(r + footprint / 2.0, centre + width / 2.0)
    return np.clip(hi - lo, 0.0, None) / footprint


def target_reflectance(x: np.ndarray, y: np.ndarray, app: Appearance, footprint_mm: float) -> np.ndarray:
    """Reflectance at target-plane points with analytic coverage over a sample footprint of ``footprint_mm``."""
    s = max(footprint_mm, 1e-4)
    r = np.hypot(x, y)
    cov_black = np.clip((BLACK_RADIUS_MM - r) / s + 0.5, 0.0, 1.0)
    refl = app.white * (1.0 - cov_black) + app.black * cov_black
    t = app.ring_line_mm
    for rl in WHITE_LINE_RADII_MM:   # white lines inside the black
        cov = _overlap(r, s, rl, t) * cov_black
        refl = refl * (1.0 - cov) + app.white * cov
    for rl in BLACK_LINE_RADII_MM:   # black lines outside the black
        cov = _overlap(r, s, rl, t)
        refl = refl * (1.0 - cov) + app.black * cov
    cov_card = (np.clip((app.card_half_mm - np.abs(x)) / s + 0.5, 0.0, 1.0)
                * np.clip((app.card_half_mm - np.abs(y)) / s + 0.5, 0.0, 1.0))
    return app.wall + (refl - app.wall) * cov_card


def _motion_kernel(length_px: float, angle_deg: float) -> np.ndarray | None:
    if length_px < 1e-3:
        return None
    size = int(math.ceil(length_px)) + 3
    size += (size + 1) % 2
    k = np.zeros((size, size), dtype=np.float64)
    c = (size - 1) / 2.0
    n = max(16, int(math.ceil(length_px * 8)))
    ca, sa = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    for tt in np.linspace(-0.5, 0.5, n):
        x, y = c + tt * length_px * ca, c + tt * length_px * sa
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        dx, dy = x - x0, y - y0
        k[y0, x0] += (1 - dx) * (1 - dy)
        k[y0, x0 + 1] += dx * (1 - dy)
        k[y0 + 1, x0] += (1 - dx) * dy
        k[y0 + 1, x0 + 1] += dx * dy
    return k / k.sum()


def _jacobian(camera: CameraModel, pose: TargetPose) -> tuple[np.ndarray, np.ndarray]:
    """Image-space derivatives of the target's x and y axes at the target centre (pixels per mm)."""
    pts = np.array([[-0.5, 0.0], [0.5, 0.0], [0.0, -0.5], [0.0, 0.5]])
    uv = pose.project(camera, pts)
    return uv[1] - uv[0], uv[3] - uv[2]


def _local_mm_per_px(camera: CameraModel, pose: TargetPose) -> float:
    ju, jv = _jacobian(camera, pose)
    det = abs(ju[0] * jv[1] - ju[1] * jv[0])
    return 1.0 / math.sqrt(det)


def _up_direction_px(camera: CameraModel, pose: TargetPose) -> list[float]:
    """Unit image direction of the target's +y axis — what an ideal gravity reference would give for a plumb target."""
    _, jv = _jacobian(camera, pose)
    jv = jv / np.hypot(*jv)
    return [float(jv[0]), float(jv[1])]


def _ring_ellipses(camera: CameraModel, pose: TargetPose) -> dict:
    out = {}
    s = np.linspace(0.0, 2.0 * math.pi, 90, endpoint=False)
    radii = {f"ring_{n}": r for n, r in RING_RADII_MM.items()}
    radii["black_edge"] = BLACK_RADIUS_MM
    for name, rad in radii.items():
        uv = pose.project(camera, np.stack([rad * np.cos(s), rad * np.sin(s)], axis=1))
        out[name] = fit_ellipse_direct(uv).to_dict()
    return out


def _bbox(camera: CameraModel, pose: TargetPose, half_mm: float, margin_px: int):
    corners = np.array([[-half_mm, -half_mm], [half_mm, -half_mm], [half_mm, half_mm], [-half_mm, half_mm]])
    edge = np.concatenate([np.linspace(corners[i], corners[(i + 1) % 4], 9) for i in range(4)])
    uv = pose.project(camera, edge)
    u0 = max(0, int(math.floor(uv[:, 0].min())) - margin_px)
    v0 = max(0, int(math.floor(uv[:, 1].min())) - margin_px)
    u1 = min(camera.width, int(math.ceil(uv[:, 0].max())) + margin_px + 1)
    v1 = min(camera.height, int(math.ceil(uv[:, 1].max())) + margin_px + 1)
    return u0, v0, u1, v1


def expected_canvas(
    spec: SceneSpec,
    mode: str = "roi",
    context_mm: float = 140.0,
    supersample: int = 4,
    bounds: tuple[int, int, int, int] | None = None,
) -> tuple[np.ndarray, TargetPose, tuple[int, int, int, int]]:
    """Noise-free expected image in reflectance units (after PSF and motion blur, before the sensor model).

    Returns ``(canvas, pose, (u0, v0, u1, v1))``. ``bounds`` fixes the canvas window in full-image pixel coordinates
    (needed for frame sequences and for finite-difference derivatives, where the window must not move with the
    target); when given it overrides ``mode``. This is the model mean used by the Cramer-Rao analysis (E-005).
    """
    cam, app, deg = spec.camera, spec.appearance, spec.degradation
    pose = pose_from_aim(cam, spec.bore_px, spec.impact_xy_mm, spec.distance_mm,
                         spec.yaw_deg, spec.pitch_deg, spec.roll_deg)
    margin = int(math.ceil(4.0 * deg.psf_sigma_px + deg.motion_blur_px)) + 3
    if bounds is not None:
        u0, v0, u1, v1 = (int(b) for b in bounds)
        if not (0 <= u0 < u1 <= cam.width and 0 <= v0 < v1 <= cam.height):
            raise ValueError("bounds must lie inside the sensor and be non-empty")
    elif mode == "full":
        u0, v0, u1, v1 = 0, 0, cam.width, cam.height
    elif mode == "roi":
        u0, v0, u1, v1 = _bbox(cam, pose, max(context_mm, app.card_half_mm), margin)
    else:
        raise ValueError("mode must be 'roi' or 'full'")
    canvas = np.full((v1 - v0, u1 - u0), app.wall, dtype=np.float64)

    # Ray-cast only where the card can be (the rest is uniform wall).
    cu0, cv0, cu1, cv1 = _bbox(cam, pose, app.card_half_mm + 1.0, 2)
    cu0, cv0, cu1, cv1 = max(cu0, u0), max(cv0, v0), min(cu1, u1), min(cv1, v1)
    if cu1 > cu0 and cv1 > cv0:
        ss = int(supersample)
        offs = (np.arange(ss) + 0.5) / ss - 0.5
        vv, uu = np.mgrid[cv0:cv1, cu0:cu1].astype(np.float64)
        shape = uu.shape + (ss, ss)
        su = np.broadcast_to(uu[..., None, None] + offs[None, None, None, :], shape).reshape(-1)
        sv = np.broadcast_to(vv[..., None, None] + offs[None, None, :, None], shape).reshape(-1)
        rays = cam.pixel_rays(np.stack([su, sv], axis=1))
        xy = pose.intersect_rays(rays)
        footprint = _local_mm_per_px(cam, pose) / ss
        refl = target_reflectance(xy[:, 0], xy[:, 1], app, footprint)
        block = refl.reshape(cv1 - cv0, cu1 - cu0, ss * ss).mean(axis=2)
        canvas[cv0 - v0:cv1 - v0, cu0 - u0:cu1 - u0] = block

    if deg.psf_sigma_px > 0:
        canvas = cv2.GaussianBlur(canvas, (0, 0), deg.psf_sigma_px, borderType=cv2.BORDER_REPLICATE)
    kernel = _motion_kernel(deg.motion_blur_px, deg.motion_blur_angle_deg)
    if kernel is not None:
        canvas = cv2.filter2D(canvas, -1, kernel, borderType=cv2.BORDER_REPLICATE)
    return canvas, pose, (u0, v0, u1, v1)


def render(
    spec: SceneSpec,
    rng: np.random.Generator,
    mode: str = "roi",
    context_mm: float = 140.0,
    supersample: int = 4,
    bounds: tuple[int, int, int, int] | None = None,
) -> SyntheticSample:
    """Render one synthetic frame. ``mode="roi"`` renders a canvas of +/- ``context_mm`` around the target (fast);
    ``mode="full"`` renders the whole sensor frame; ``bounds=(u0, v0, u1, v1)`` renders a fixed window (sequences)."""
    cam, deg = spec.camera, spec.degradation
    canvas, pose, (u0, v0, u1, v1) = expected_canvas(spec, mode, context_mm, supersample, bounds)

    electrons = rng.poisson(np.clip(canvas, 0.0, None) * deg.electrons_per_unit).astype(np.float64)
    electrons += rng.normal(0.0, deg.read_noise_e, size=electrons.shape)
    signal = np.clip(electrons / deg.electrons_per_unit * deg.gain_headroom, 0.0, 1.0)
    levels = 2 ** deg.adc_bits - 1
    signal = np.round(signal * levels) / levels
    image = np.round(np.power(signal, 1.0 / deg.gamma) * 255.0).astype(np.uint8)
    if deg.jpeg_quality is not None:
        ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(deg.jpeg_quality)])
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        image = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)

    impact = bore_impact_mm(cam, pose, spec.bore_px)
    centre_full = pose.project(cam, np.zeros((1, 2)))[0]
    ellipses = _ring_ellipses(cam, pose)
    sc = score_shot(float(impact[0]), float(impact[1]))
    gt = {
        "target_centre_px": [float(centre_full[0]), float(centre_full[1])],
        "target_centre_px_canvas": [float(centre_full[0] - u0), float(centre_full[1] - v0)],
        "bore_px": [float(spec.bore_px[0]), float(spec.bore_px[1])],
        "sight_px": [float(spec.bore_px[0]), float(spec.bore_px[1])],
        "impact_xy_mm": [float(impact[0]), float(impact[1])],
        "impact_score": sc.as_dict(),
        "local_mm_per_px": _local_mm_per_px(cam, pose),
        "up_direction_px": _up_direction_px(cam, pose),
        "ring_ellipses_px": ellipses,
        "canvas_origin_px": [u0, v0],
        "canvas_size_px": [u1 - u0, v1 - v0],
        "pose": {"R": pose.R.tolist(), "t_mm": pose.t.tolist()},
    }
    params = spec.to_dict() | {"mode": mode, "context_mm": context_mm, "supersample": supersample,
                               "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION}}
    if bounds is not None:
        params["bounds_px"] = [u0, v0, u1, v1]
    return SyntheticSample(image, (u0, v0), (spec.bore_px[0] - u0, spec.bore_px[1] - v0), gt, params)


def random_spec(
    rng: np.random.Generator,
    camera: CameraModel,
    degradation: Degradation,
    impact_radius_mm: float = 20.0,
    distance_range_mm: tuple[float, float] = (9950.0, 10050.0),
    max_tilt_deg: float = 10.0,
    max_roll_deg: float = 3.0,
    appearance: Appearance | None = None,
) -> SceneSpec:
    """Random scene: impact uniform in a disc, range within the ISSF tolerance, mild tilt and roll."""
    rad = impact_radius_mm * math.sqrt(rng.uniform())
    ang = rng.uniform(0.0, 2.0 * math.pi)
    return SceneSpec(
        camera=camera,
        bore_px=(camera.cx, camera.cy),
        impact_xy_mm=(rad * math.cos(ang), rad * math.sin(ang)),
        distance_mm=float(rng.uniform(*distance_range_mm)),
        yaw_deg=float(rng.uniform(-max_tilt_deg, max_tilt_deg)),
        pitch_deg=float(rng.uniform(-max_tilt_deg, max_tilt_deg)),
        roll_deg=float(rng.uniform(-max_roll_deg, max_roll_deg)),
        appearance=appearance or Appearance(),
        degradation=degradation,
    )
