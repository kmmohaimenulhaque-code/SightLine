# Coordinate Systems and Sight Geometry

Implementation: `app/calibration/camera.py`, `app/calibration/pose.py`, `app/calibration/rectify.py`,
`app/calibration/display.py`. Status labels follow `VALIDATION.md`.

## 1. Frames

| Frame | Origin | Axes | Units | Status |
|---|---|---|---|---|
| **T** target | Centre of the 10 ring (GTR 6.4.6 defines target centre this way) | x right, y up, z out of the target face toward the shooter | mm | Defined |
| **C** camera | Optical centre of the active camera | OpenCV convention: x right, y down, z forward along the optical axis | mm | Defined |
| **I** image | Top-left pixel centre is (0, 0) | u right, v down; principal point (cx, cy) | px | Defined |
| **S** screen | Display pixel grid | Platform display coordinates | px | Mapping I→S must be recorded per frame (crop, scale, rotation of the preview) — OPEN |
| **D** device | Platform motion-sensor frame | Platform-specific (Android sensor frame vs. iOS Core Motion) | — | UNVERIFIED in this session; define per platform before using IMU data |
| **G** grip | Mechanical datum on the phone clamp | x along the grip's longitudinal axis | mm | Defined by CAD (not started) |

Fronto-parallel reference: a target facing the camera has rotation R₀ = diag(1, −1, −1) from T to C
(target x → camera x, target y up → camera y down, target z → camera −z).

## 2. The simulated bore axis and the point of impact

* **Bore axis B** — a ray fixed in frame C: origin at the camera's optical centre, direction
  b̂ = normalise(K⁻¹ [p_b, 1]ᵀ), where **p_b is the "bore pixel"** (default: the principal point).
* **Simulated impact P** — the intersection of B with the target plane. Because B passes through the camera
  centre, its image is the single pixel p_b at every distance: **no parallax and no distance dependence**.
* **Impact in target units** — the image→target-plane mapping of the observed black aiming mark, applied to p_b
  (§6). The score follows from |P| in millimetres (`docs/science/TARGET_GEOMETRY_AND_SCORING.md` §2).

**Why not a physical "barrel axis" offset from the camera?** If the simulated barrel were a line parallel to the
optical axis but displaced by e (say 30 mm), the impact would shift by e on the target at every distance: 30 mm is
more than five times the 10-ring diameter. There is no physical barrel, so the bore is defined through the camera
centre (ARCHITECTURE.md D-002).

## 3. The digital front sight and zeroing

* The front-sight overlay is drawn at **S(p_b)**: the bore pixel mapped through the current preview transform.
  Hence "front sight centred on the bull" ⇔ "bore on target". This is the reproducible geometric relationship the
  master prompt requires (§14): the overlay is not placed by eye.
* **Zeroing** is the choice of p_b. Moving p_b is equivalent to adjusting real sights. A user-facing "sight
  adjustment" can move p_b in fixed angular clicks.
* **Error mode:** if the overlay is drawn at S(p_b) + e (display-mapping error), the shooter's sight picture and the
  bore disagree by a constant — a sight-misadjustment bias, correctable by zeroing, but it must be kept below the
  shooter's resolution (REQUIREMENTS.md FUN-04).
* **Error mode:** if p_b moves relative to the phone body during a shot (optical image stabilisation), the bore is no
  longer fixed. See `docs/science/ERROR_BUDGET.md` term E6.

## 4. Finding: a video see-through sight does not train sight *alignment* — DERIVED

On a real pistol, the eye, rear notch, front post and target must line up. If the post sits laterally off-centre
in the notch by δ while the post is held on the bull, the bore is rotated by ≈ δ / L_sight. With a sight radius of
about 0.33 m, δ = 0.1 mm gives 0.3 mrad, which is **3 mm at 10 m**. Sight alignment is a core pistol skill.

On SIGHTLINE, the shooter sees the target as an image on an opaque phone screen. Both the front-sight overlay and the
target image live on that screen; the target image moves only when the *camera* rotates. So the relationship
"front sight on bull" depends only on where the camera points — **not on where the shooter's eye is**. The
physical rear-sight marker therefore cannot influence the score.

| Option | Description | Status |
|---|---|---|
| O1 | Accept and state it: SIGHTLINE trains sight picture, hold, trigger control and follow-through, not alignment | Chosen for the MVP (D-011, PROPOSED) |
| O2 | Track the eye with the front camera, compute the eye → rear-marker → front-sight line, and penalise misalignment (or render the scene as a head-tracked "window") | EXPERIMENTAL research item |
| O3 | Optical see-through | Not possible with an opaque phone |

This changes what the product can honestly claim. It should be stated in user-facing material.

## 5. "Fit to FOV" — unity magnification, derived properly

Goal: the target on screen should subtend the same visual angle as the real target, so the sight picture looks like
the real one. An object at angle θ spans θ·f_px camera pixels. If the preview shows *s* screen pixels per camera
pixel on a screen of density *ppi*, viewed from distance D_eye:

  displayed size = θ · f_px · s · 25.4 / ppi (mm)  should equal  θ · D_eye (mm)

  ⇒  **s = D_eye · ppi / (25.4 · f_px)**   (DERIVED)

Example (ASSUMED D_eye = 700 mm, 460 ppi): f_px = 1450 → s = 8.8; f_px = 4330 → s = 2.9. In every case the black
appears **4.17 mm** wide on screen (59.5 mm × 0.7 m / 10 m) and the 10 ring 0.8 mm.

**Target-anchored variant (preferred, D-003 family):** measure the black's diameter in camera pixels and scale the
preview so that it is drawn 59.5 mm × D_eye / L_target wide. This needs neither f_px nor zoom metadata; it does need
D_eye (from the grip geometry), the screen ppi (device specification, to be verified per device) and the target
distance (assumed 10 m).

## 6. Image → target-plane mapping (rectification) — DERIVED

The whole target subtends < 1° at 10 m. Across the target the perspective projection is therefore extremely close to
an affine map (weak perspective), and lens distortion — smooth on the scale of a few dozen pixels — is also locally
affine. The imaged black is then an ellipse, and the map that turns that ellipse back into a 29.75 mm-radius circle is
the image→target map for every point near the target, including the bore pixel when the shooter is on target.

Construction (`app/calibration/rectify.py`): with ellipse centre c, semi-axes a ≥ b and major-axis angle φ,

  M = R(φ) · diag(29.75/a, 29.75/b) · R(φ)ᵀ   (symmetric "un-stretch", px → mm)
  x_target = F · R(−roll) · M · (p − c),  F = diag(1, −1) (image v down → target y up)

Properties:

* **Exact under weak perspective** when the target is tilted about a single in-plane axis (the foreshortening matrix
  is then symmetric). For compound yaw + pitch tilts a small residual in-plane rotation of about yaw·pitch/2 appears
  (≈0.9° at 10° × 10°). It changes the *direction* of the plotted shot slightly, never the radial score.
* **Intrinsic calibration is not needed for scoring.** Focal length, principal point and distortion all cancel
  locally, because the target itself is the ruler. Calibration is needed for angular metrics and display (D-003).
* Camera roll rotates the image of the target but does not change the radial score; the shot direction uses the
  roll angle from the phone's gravity vector (D-015, PROPOSED).
* Residual perspective and distortion errors are quantified in `tests/test_rectify.py`.
