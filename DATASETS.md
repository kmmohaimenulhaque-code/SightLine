# External Dataset Survey

Survey date: 2026-10-05. Licence statuses: **VERIFIED** = read on the dataset's own page this session;
**UNVERIFIED** = not checked; treat as unusable until checked. No external dataset has been downloaded.

## 1. Summary

No public dataset found matches SIGHTLINE's core imaging condition: a printed ISSF target at ~10 m seen by a
hand-held phone camera, with known ground-truth target geometry and aim point. Public "shooting target" datasets are
close-up photographs of shot cards for bullet-hole detection. SIGHTLINE therefore relies on synthetic data with exact
ground truth plus first-party captures (ARCHITECTURE.md D-006; `DATASET_SPEC.md`).

## 2. Candidates

| Dataset | Source / creator | Licence | Size / annotation | Intended use | Commercial / redistribution | Limitations | Relevance to SIGHTLINE | Split strategy if used |
|---|---|---|---|---|---|---|---|---|
| SIDD (Smartphone Image Denoising Dataset) | <https://abdokamel.github.io/sidd/> — Abdelhamed, Lin, Brown (CVPR 2018) | MIT (VERIFIED on project page) | ~30 000 noisy/clean images, 10 scenes, 5 phones; raw-RGB (.MAT) and sRGB (.PNG) | Denoising benchmark | MIT permits both, with notice | Older phones (2016-era); static scenes | **Medium:** calibrate the synthetic noise model (signal-dependent noise per phone) | Use as calibration reference only; no training split needed |
| KNSA-shooting-target | Roboflow Universe, <https://universe.roboflow.com/knsashootingtargets/knsa-shooting-target> | CC BY 4.0 (VERIFIED on page) | 92 images, 11 classes, object detection boxes | Bullet-hole score detection | Allowed with attribution | Close-up cards, holes, not 10 m handheld | **Low:** at most card-appearance robustness tests | Hold-out test only |
| Yolo_Shot_Datasets_with_Annots | Kaggle, <https://www.kaggle.com/datasets/pfrmusic/yolo-shot-datasets-with-annots> | UNVERIFIED | Unknown | Shot/hole detection | UNVERIFIED | Unknown | Low | — |
| Bullet-hole detection data from "Application of YOLOv8 and Detectron2 for Bullet Hole Detection and Score Calculation from Shooting Cards" (AI, MDPI, 2024) | <https://doi.org/10.3390/ai5010005> | UNVERIFIED (availability unknown) | Unknown | Hole detection + scoring | UNVERIFIED | Close-up cards | Low (methods reference only) | — |
| Deblurring / super-resolution sets (e.g. GoPro, RealBlur, DIV2K) | Various | UNVERIFIED — **not investigated** this session | — | Natural-image restoration | UNVERIFIED | Natural images ≠ target imagery; visual metrics ≠ measurement metrics | Only if the ML restoration arm passes gate G4 | — |
| Camera-calibration datasets | — | — | — | — | — | — | **Not needed:** calibration is per device and must use first-party captures | — |
| Human pose datasets | — | — | — | — | — | — | **Out of scope** until AI coaching is technically justified (master prompt §8) | — |

## 3. Rules for adding an external dataset

1. Record source, creator, URL, exact licence text location, version/date, size, annotation format.
2. Verify commercial-use and redistribution terms on the dataset's own page or licence file.
3. Add a manifest entry with category `EXTERNAL` (`DATASET_SPEC.md` §2) before any file enters `data/raw/`.
4. Never mix external samples into synthetic or team-collected sets without provenance fields.
