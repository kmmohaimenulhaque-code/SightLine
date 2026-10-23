# Owner concept render → G0 CAD: what is adopted, what is different, and why

The owner supplied a concept image of the "demo final product" on 2026-10-10
(`docs/cad/reference/owner_concept_render.jpg`). It is an **illustration**, not a drawing: it carries no dimensions,
masses or tolerances, and nothing in the CAD was measured from it. This document maps each visible feature to the G0
design so the two can be compared feature by feature, and records the features that are deliberately not copied.

## 1. Feature map

| Concept render | G0 CAD (Mission 3) | Status |
|---|---|---|
| Sculpted match grip (laminated-wood look) with a thumb shelf and a palm swell | A-CORE anatomical grip: superellipse sections, palm swell peaking at s = 45 mm, lofted thumb shelf up to 13 mm proud (`ERGONOMIC_GRIP.md` §2) | **Adopted** (own geometry; finish is a print/finish choice, see §3) |
| Adjustable heel rest on a slotted plate with two screws | A-POMMEL-CAP heel rest at 90° to the grip, 35° end bevel; height set by grip-length variants 98 / 105 / 112 mm | **Adopted in function**; a slotted, screw-adjustable heel-rest plate is the G1 upgrade if the fitting trials need finer steps than 7 mm |
| Ballast window with a row of steel weights and a millimetre scale | C-CARRIAGE-1 + C-CASSETTE-1 on two Ø6 rods, moulded 2 mm scale with a 0.5 mm vernier, friction lock, washers clamped in a closed capsule | **Adopted** — and made measurable: every setting maps to a predicted mass/COM (`MASS_BALANCE_GUIDE.md`) |
| Lower thumbscrew on the ballast | H-CARRIAGE-LOCK-1 M3 thumbscrew (friction lock) | **Adopted** |
| Phone in a clamp with knurled screws at the rear, screen toward the shooter | B-CRADLE with model-specific 3-2-1 insert, spring jaw and pusher with nylon thumbscrews, on a kinematic coupling; phone back toward the target, screen toward the shooter | **Adopted** — with exact constraint instead of a friction clamp (D-027) |
| Angular dial at the phone mount | Not a CAD feature: the camera pose is fixed by the coupling and calibrated in software (D-002 bore pixel); an adjustable angle would break the calibration after every touch | **Different on purpose** |
| Long upper housing with sights and an orange nose | A-SPINE: an **open-frame** box beam carrying the ballast, with an orange (high-visibility) closed nose cap; no tube, no bore, no muzzle | **Adapted** (§2) |
| Front and rear sights on the housing | Not built: the sight is the phone screen (Alignment Trainer, D-011). Physical iron sights would not affect the measurement, because the camera — not the eye — defines the bore (C-022) | **Not adopted** (scientific reason) |
| Trigger guard and trigger blade | D-BLE-POD: a training **button** (switch only, SAF-01) with ±4 mm reach; press force ≥ 500 g required at G2 (MEC-15). A blade-style switch actuator and a guard can be added at G2 with the module choice | **Deferred to G2** (needs the switch module) |
| Engraved "SIGHTLINE — PASSIVE TRAINING INSTRUMENT / NOT A FIREARM" | Moulded "TRAINING INSTRUMENT - NOT A FIREARM" on the spine (SAF-02) | **Adopted** |

## 2. Why the outline stays deliberately less pistol-like than the render

SIGHTLINE trains hold and trigger control; how it **feels in the hand** (grip shape, mass, balance) is what transfers to
a match pistol, and that is where the G0 design follows the concept. How it **looks from a distance** does not affect
any measurement, and an object that reads as a real pistol carries legal and safety risk that has not been assessed
(imitation-firearm rules were not researched, including Bangladesh — `GRIP_REQUIREMENTS.md` §2). So:

* no tube, bore or muzzle anywhere — the forward beam is an open frame whose windows show the ballast;
* a high-visibility orange nose cap and bright chassis colour;
* the phone visibly on top and the moulded "NOT A FIREARM" marking;
* nothing in the instrument stores energy or moves anything except a switch (SAF-01).

If the owner wants the closer silhouette of the render, that is an owner decision **after** a local legal check;
it changes only cosmetic shells, not the chassis, adapter, ballast or grip.

## 3. Finishing the grip like the render

The render's grip is laminated wood. G0 prints the grip in PETG so that its geometry can be iterated cheaply in G1.
Once a shape is fitted to a shooter, the same STEP surface (`cad/exports/parts/A-CORE.step`, `A-BACKSTRAP*.step`,
`A-POMMEL-CAP.step`) can be CNC-machined from a laminated-wood or birch-plywood blank; the electronics bay, pommel
cavity and inserts stay as modelled. A wooden grip changes the mass (re-weigh, `MASS_BALANCE_GUIDE.md` §2) and must
not use compressible material on the hand surfaces (ISSF 8.4.1.1 b, applied as a realism rule).

## 3a. G1: the closer silhouette (owner decision, 2026-10-11)

The owner chose the render's silhouette and said the local rules had been checked. G1
(`docs/cad/G1_DESIGN.md`, source `cad/parametric/sightline_g1/`) adds the following:

* an enclosed housing with a solid orange nose and no bore;
* an orange scaled rail and a side service plate;
* an adjustable rear notch (elevation and windage) and a shimmed front blade, with a sight radius of 218 mm;
* a trigger guard around a contact-switch blade;
* a landscape phone cradle on an indexed ±10° pivot yoke that straddles the sight line;
* a cylindrical X-ballast cassette and a Z cassette in the grip heel;
* a lofted grip core with replaceable panels, a backstrap with beavertail and an indexed palm shelf.

The rows "Different on purpose", "Not adopted" and "Deferred to G2" in §1 apply to G0 only. The G0 files are unchanged.

## 4. What would make the render "scientifically functional"

The render shows a product; SIGHTLINE's claims rest on measurements. The path from the CAD to a functional
instrument is the validation plan, in order: P0 coupons → P1 fit → P3/P4 masses → P5 COM → P6 slider → P7 Metric A
(≤ 1 mrad p95, PROPOSED) → P8 Metric B → P9 wear/creep/magnetics → P10 stored configuration → G1 fitting with ≥ 3
shooters → G2 button and IMU → G3 (`PHYSICAL_VALIDATION_PLAN.md`). None of these has been run.
