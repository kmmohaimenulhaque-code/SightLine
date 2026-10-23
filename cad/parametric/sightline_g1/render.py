"""CAD-derived renders of a G1 assembly (VTK, offscreen). Every pixel comes from the B-rep tessellation of the
actual parts; nothing is painted in. Six views: hero, ergonomic side, rear camera/adjustment, sight alignment,
exploded, dimensions."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

EXPLODE = {"phone": (0, 0, 70), "cradle": (0, 0, 40), "sights": (0, 0, 22), "grip": (0, 0, -55),
           "ballast_x": (0, 0, -45), "ballast_z": (0, 0, -95), "interfaces": (0, 0, -18), "housing": (0, 0, 0)}
EXPLODE_PART = {"A-GRIP-PANEL-L": (0, 45, -55), "A-GRIP-PANEL-R": (0, -45, -55), "A-BACKSTRAP": (-45, 0, -55),
                "A-PALM-SHELF": (0, 0, -95), "A-RAIL": (0, 0, 12), "A-NOSE": (30, 0, 0), "A-HOUSING-F": (25, 0, 0),
                "A-HOUSING-COUPLER": (12, 0, -10), "B-YOKE": (0, 0, 22), "A-TRIGGER-GUARD": (0, 0, -30),
                "D-SWITCH-BLADE": (0, 0, -22), "C-X-CHANNEL": (0, 0, -25), "C-X-STOP-F": (20, 0, -25),
                "A-SERVICE-PLATE": (0, -25, 0)}


def _mesh(shape, tol=0.12, ang=0.25):
    import vtk
    v, f = shape.tessellate(tol, ang)
    pts = vtk.vtkPoints()
    for p in v:
        pts.InsertNextPoint(p.x, p.y, p.z)
    polys = vtk.vtkCellArray()
    for t in f:
        polys.InsertNextCell(3)
        for i in t:
            polys.InsertCellPoint(int(i))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(polys)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(32)
    n.SplittingOn()
    n.ConsistencyOn()
    n.Update()
    return n.GetOutput()


class Scene:
    def __init__(self, asm, size=(1600, 1100), offsets=None, keepouts=False, extra=()):
        import vtk
        self.vtk = vtk
        self.asm = asm
        self.size = size
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.93, 0.93, 0.94)
        self.ren.SetBackground2(0.80, 0.81, 0.83)
        self.ren.GradientBackgroundOn()
        self.win = vtk.vtkRenderWindow()
        self.win.SetOffScreenRendering(1)
        self.win.AddRenderer(self.ren)
        self.win.SetSize(size[0] * 2, size[1] * 2)
        offsets = offsets or {}
        for p in asm.parts:
            if p.kind == "display":
                continue
            self._add(p.shape, p.color, offsets.get(p.id, (0, 0, 0)), spec=0.35 if p.kind != "printed" else 0.18)
        if keepouts:
            for k in asm.keepouts:
                self._add(k, (0.95, 0.15, 0.15), (0, 0, 0), opacity=0.28)
        for shape, col, op in extra:
            self._add(shape, col, (0, 0, 0), opacity=op)
        scr = [p for p in asm.parts if p.kind == "display"]
        for p in scr:
            self._add(p.shape, p.color, offsets.get(p.id, (0, 0, 0)), spec=0.6, amb=0.25)
        lk = vtk.vtkLightKit()
        lk.SetKeyLightIntensity(0.95)
        lk.AddLightsToRenderer(self.ren)

    def _add(self, shape, color, off, spec=0.2, opacity=1.0, amb=0.12):
        vtk = self.vtk
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(_mesh(shape))
        a = vtk.vtkActor()
        a.SetMapper(m)
        pr = a.GetProperty()
        pr.SetColor(*color)
        pr.SetSpecular(spec)
        pr.SetSpecularPower(28)
        pr.SetAmbient(amb)
        pr.SetDiffuse(0.85)
        pr.SetOpacity(opacity)
        a.SetPosition(*off)
        self.ren.AddActor(a)

    def camera(self, pos, focal, up=(0, 0, 1), angle=26.0, ortho=None):
        c = self.ren.GetActiveCamera()
        c.SetPosition(*pos)
        c.SetFocalPoint(*focal)
        c.SetViewUp(*up)
        c.SetViewAngle(angle)
        if ortho:
            c.ParallelProjectionOn()
            c.SetParallelScale(ortho)
        self.ren.ResetCameraClippingRange()

    def project(self, p):
        vtk = self.vtk
        co = vtk.vtkCoordinate()
        co.SetCoordinateSystemToWorld()
        co.SetValue(*map(float, p))
        x, y = co.GetComputedDoubleDisplayValue(self.ren)
        return x / 2.0, self.size[1] - y / 2.0

    def image(self):
        from PIL import Image
        from vtk.util.numpy_support import vtk_to_numpy
        vtk = self.vtk
        self.win.Render()
        f = vtk.vtkWindowToImageFilter()
        f.SetInput(self.win)
        f.ReadFrontBufferOff()
        f.Update()
        im = f.GetOutput()
        w, h, _ = im.GetDimensions()
        a = vtk_to_numpy(im.GetPointData().GetScalars()).reshape(h, w, -1)[::-1, :, :3]
        return Image.fromarray(np.ascontiguousarray(a)).resize(self.size, Image.LANCZOS)


def _label(img, lines, title=None):
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 22)
        fs = ImageFont.truetype("DejaVuSans.ttf", 17)
    except Exception:  # pragma: no cover
        f = fs = ImageFont.load_default()
    y = 16
    if title:
        d.text((22, y), title, fill=(25, 25, 30), font=f)
        y += 32
    for ln in lines:
        d.text((22, y), ln, fill=(55, 55, 62), font=fs)
        y += 23
    d.text((22, img.size[1] - 30), "CAD-derived render (B-rep tessellation) — not a photograph, not a physical part. "
           "Passive training instrument: no bore, no muzzle, no projectile path.", fill=(70, 70, 76), font=fs)
    return img


def render_all(asm, out_dir: Path) -> list:
    from PIL import ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    f = asm.frames
    piv = f["pivot_K"]
    made = []
    c0 = (135, 0, -10)
    P = asm.P
    zs = P.sight.line_z

    def save(img, name):
        p = out_dir / name
        img.save(p, optimize=True)
        made.append({"file": name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})

    # 1 hero three-quarter (left side, marking side; phone toward the viewer as in the reference)
    s = Scene(asm)
    s.camera((-330, 610, 190), (115, 0, -35), angle=30)
    save(_label(s.image(), [f"{asm.id}: landscape phone (screen to the shooter), indexed angle dial, enclosed "
                            "housing, orange rail,", "adjustable rear notch and front blade, trigger guard, X ballast "
                            "cassette, sculpted grip with palm shelf"], "Hero three-quarter view"), "01_hero.png")
    # 2 opposite ergonomic side (palm side, right)
    s = Scene(asm)
    s.camera((20, -700, -110), (110, 0, -40), angle=32)
    save(_label(s.image(), ["Palm side (−Y): palm swell panel, finger relief, beavertail on the backstrap,",
                            "adjustable palm shelf with index pin, switch blade in the guard, X lock knob"],
                "Ergonomic side"), "02_ergonomic_side.png")
    # 3 rear camera and adjustment view (from the target side, keep-outs shown)
    s = Scene(asm, keepouts=True)
    s.camera((520, -330, 260), (60, 0, 20), angle=30)
    save(_label(s.image(), ["Phone back toward the target; red = camera keep-out (both short-end zones, empty);",
                            "back plate, +Y datum, retainers, angle dials and lock knobs, X ballast scale and lock"],
                "Rear-camera and adjustment view"), "03_rear_camera.png")
    # 4 sight alignment (eye on the sight line, arm's length behind the notch)
    s = Scene(asm)
    eye = P.sight.eye_distance_mm
    rn = sum(P.sight.rear_notch_x) / 2
    s.camera((rn - eye, 0, zs + 0.8), (rn + 400, 0, zs + 0.8), angle=9.5)
    img = s.image()
    save(_label(img, [f"Eye on the sight line {eye:g} mm behind the notch (ASSUMED hold): front blade centred in the "
                      "rear notch,", "phone screen above the line as the electronic interface; sight line passes "
                      "between the yoke uprights"], "Active-sight alignment view"), "04_sight_alignment.png")
    # 5 exploded
    offs = {}
    for p in asm.parts:
        offs[p.id] = EXPLODE_PART.get(p.id, EXPLODE.get(p.group, (0, 0, 0)))
    s = Scene(asm, offsets=offs)
    s.camera((-200, 640, 160), (140, 0, -30), angle=33)
    save(_label(s.image(), ["phone · cradle/retainers/pads · yoke/dials · sights · rail · housing halves/coupler/nose ·",
                            "guard/switch · grip core/panels/backstrap/shelf · X channel/cassette/slugs · Z cassette"],
                "Exploded engineering assembly"), "05_exploded.png")
    # 6 dimensions (orthographic left side)
    s = Scene(asm)
    s.camera((150, 900, 0), (150, 0, -20), angle=20, ortho=205)
    img = s.image()
    d = ImageDraw.Draw(img)
    try:
        ft = ImageFont.truetype("DejaVuSans.ttf", 17)
    except Exception:  # pragma: no cover
        ft = ImageFont.load_default()
    sg = sight_dims(asm)
    g = asm.extras.get("phone_geom")
    X = P.x_ballast

    def dim(a, b, txt, off=(0, 0), col=(20, 60, 160)):
        pa, pb = s.project(a), s.project(b)
        d.line([pa, pb], fill=col, width=2)
        for q in (pa, pb):
            d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=col)
        mid = ((pa[0] + pb[0]) / 2 + off[0], (pa[1] + pb[1]) / 2 + off[1])
        d.text(mid, txt, fill=col, font=ft)

    rnx = sum(P.sight.rear_notch_x) / 2
    fbx = sum(P.sight.front_blade_x) / 2
    dim((rnx, 30, zs + 12), (fbx, 30, zs + 12), f"sight radius {fbx - rnx:.1f} mm", (-60, -24))
    dim((fbx + 14, 30, 0), (fbx + 14, 30, zs), f"sight height {zs:g} mm", (8, -8))
    zc = -P.housing.height - X.channel_h - X.shoe_clear - X.tube_d / 2
    dim((X.pos_min, 30, zc - 20), (X.pos_max + X.len + X.cap_t, 30, zc - 20),
        f"X cassette travel {X.pos_min:g}…{X.pos_max:g} mm (step {X.pos_step:g})", (-150, 6))
    if g:
        dim((g["x_front"] - 12, 30, g["z_bot"]), (g["x_front"] - 12, 30, g["z_top"]),
            f"phone {g['W']:.1f} (landscape height)", (-215, 0))
    dim((piv[0], 30, piv[2]), (piv[0] + 40 * math.cos(math.radians(10)), 30, piv[2] + 40 * math.sin(math.radians(10))),
        f"angle {P.yoke.angle_range_deg[0]:g}…{P.yoke.angle_range_deg[1]:g}° ({P.yoke.index_step_deg:g}° index)",
        (20, -12), col=(160, 40, 20))
    Z = P.z_ballast
    dim((P.grip.top_x - 30, 30, -P.housing.height - P.grip.length + Z.cass_len + Z.travel),
        (P.grip.top_x - 30, 30, -P.housing.height - P.grip.length),
        f"Z bore: cassette {Z.cass_len:g} + travel {Z.travel:g} mm", (-250, 0))
    dim((P.grip.top_x + 40, 30, -P.housing.height - P.grip.length), (P.grip.top_x + 40, 30,
        -P.housing.height - P.grip.length - max(P.palm_shelf.drop_positions)),
        f"palm shelf drop {'/'.join(f'{v:g}' for v in P.palm_shelf.drop_positions)} mm", (12, 0))
    save(_label(img, [f"Rear elevation ±{P.sight.rear_elev_range_mm:g} mm, windage ±{P.sight.rear_wind_range_mm:g} mm; "
                      f"front shim {P.sight.front_shim_range[0]:g}…{P.sight.front_shim_range[1]:g} mm; "
                      f"backstraps S/M/L; shelf wing ±5°", f"rear notch {P.sight.notch_w:g} mm, front blade "
                      f"{P.sight.blade_w:g} mm; light gap {sg['light_gap']:.2f} mrad each side at the assumed eye "
                      "distance"], "Dimension and adjustment view (orthographic, left side)"), "06_dimensions.png")
    return made


def sight_dims(asm):
    from .assembly import sight_geometry
    g = sight_geometry(asm.P)
    return {"light_gap": g["sight_picture_at_assumed_eye_distance"]["light_gap_each_side_mrad"]}
