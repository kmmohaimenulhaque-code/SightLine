# AMD-NR / OptiScaler — Research and Licence Analysis

| Field | Value |
|---|---|
| Date | 2026-10-05 |
| Analyst | Claude (Opus 5.5) research session |
| URL as given in the master prompt | `https://github.com/3zwr1/AMD-NR—OptiScaler` (contains an em dash; not resolvable) |
| Resolved repository | <https://github.com/3zwr1/AMD-NR---OptiScaler> (found by probing spelling variants with `git ls-remote`) |
| Commit inspected | `f0c0232a2384f1fc9ee0167dcabf2dbe34fd7708` (2026-10-04, "Restrict GPU support to rdna2 in manifest.json"); tag `Alpha` → `3995999b25e500a8483314b0de088dc55fb9bd12` |
| Method | Read-only shallow clone (depth 50) into a scratch directory outside the SIGHTLINE repository. Licence files, notices, READMEs and file headers read. **No file was copied into SIGHTLINE.** |
| Overall verdict | **Nothing incorporated.** All code and models: LICENCE INCOMPATIBLE or LICENCE UNCLEAR, and TECHNICALLY INCOMPATIBLE. A small number of concepts are REFERENCE ONLY. |

---

## 1. Purpose (what the repository actually is)

AMDNR is a Windows game modification. Its own notice describes it as a GPL-3.0 fork of OptiScaler that
"runs DLSS 5 Neural Rendering on AMD Radeon GPUs" (`AMDNR_NOTICE.txt`). OptiScaler itself is a DLL that
intercepts a game's upscaler API calls (NVIDIA DLSS/NGX, AMD FSR 2/3.1, Intel XeSS) and reroutes them to a
different upscaler backend.

AMDNR adds, on top of OptiScaler:

* a neural-rendering post-pass that drives NVIDIA's DLSS Neural Rendering model (`nvngx_dlssnr.dll`,
  NGX feature 18) on NVIDIA GPUs, and on AMD GPUs routes to third-party ports of that network
  ("lmxxf" HIP kernels; a closed "danielblnc" runtime);
* an FSR Ray Regeneration path, a screen-space GI effect, frame-generation unlocks;
* "AMDNR Anywhere", a window-capture host mode built on a modified Magpie fork;
* a launcher (separately licensed, see §6).

It operates on **rendered game frames**, using inputs a game engine supplies (colour, depth, motion
vectors, exposure). It does not process camera images.

## 2. Architecture and pipeline (as documented in the repository)

```
Game (DX11/DX12/Vulkan) ──► OptiScaler hooks (NVNGX / FSR / XeSS entry points, GPU spoofing)
                               │
                               ├─► chosen upscaler backend (FSR 2/3.1, XeSS, DLSS)
                               │
                               └─► dlssnr pass (after upscale)
                                      encode (scale + sRGB encode, soft knee) ─► area downsample
                                      ─► neural network (NVIDIA runtime on RTX; lmxxf HIP kernels or
                                         danielblnc runtime on Radeon)
                                      ─► resolve / colour composition (RenoDX two-branch luminance ratio,
                                         OkLab hue correction, gamut compression) ─► temporal stability pass
```

Source: `main/AMDNR-source/optiscaler/dlssnr/README.md`, `AMDNR_NOTICE.txt` §1 and §5.

## 3. ML / reconstruction mechanisms

* The network is described in the notice as including a ViT projection, C512 QKV/mix kernels and
  one-wave-per-head attention — i.e. a transformer-style image network executed by hand-written HIP
  kernels (FP8 matrix instructions on RDNA 4; an F16 path on RDNA 3 per `AMDNR_RDNA3_BACKEND.txt`).
* Model weights are loaded from an assets folder by `LmxxfNrRuntime.dll`
  (`optiscaler/dlssnr/lmxxf/LmxxfBackend.h`, "the weights folder").
* The surrounding temporal machinery (e.g. `dlssnr/gi/shaders/gi_temporal.hlsl`) is written, per its
  header, "from the published ideas": per-pixel history length and luminance moments (SVGF, Schied et al.
  2017), fast/slow history with clamping (after Karis 2014 / Salvi 2016), reprojection with the game's motion
  vectors and a depth-based disocclusion test.

## 4. GPU execution, runtime, optimisation

* Windows only; D3D12 (with D3D11/Vulkan bridges); shaders precompiled to DXBC (`fxc cs_5_0`).
* Neural kernels are AMD HIP code objects for specific `gfx11xx`/`gfx12xx` targets, packaged in a `.pak`
  whose modules are SHA-256 pinned by the runtime DLL.
* Optimisations described: per-GPU kernel variants, network size tiers (360p/576p), dynamic neural-rendering
  resolution (25–100 %), interleaving model runs across frames, cost ceilings, driver-reset back-off.

## 5. Exact files inspected

| File (path at the inspected commit) | What was read |
|---|---|
| `LICENSE` | Header: GNU GPL v3 |
| `AMDNR_NOTICE.txt` | Sections 1–7 in full |
| `AMDNR_RDNA3_BACKEND.txt` | Full text including its MIT licence |
| `FidelityFX_v2_LICENSE.md` | Header and structure |
| `Launcher/OpenSource/LICENSE.txt` | Header and sections 1–2 |
| `main/AMDNR-source/optiscaler/dlssnr/README.md` | Purpose, structure, attribution |
| `main/AMDNR-source/optiscaler/dlssnr/lmxxf/runtime/LICENSE.lmxxf` | Full MIT text (Copyright 2026 Kien) |
| `main/AMDNR-source/optiscaler/dlssnr/lmxxf/LmxxfBackend.h` | Weight-path declarations |
| `main/AMDNR-source/optiscaler/dlssnr/gi/shaders/gi_temporal.hlsl` | Licence header and design comment |
| `main/AMDNR-source/optiscaler/dlssnr/amd/AmdBridge.cpp`, `AmdBridge.h` | Licence headers |
| `main/AMDNR-source/Config.cpp` | Licence header |
| Whole tree | Directory and file-type inventory (704 files: 295 `.h`, 197 `.cpp`, 111 `.cs`, 7 `.hlsl`, …) |

Not read in detail: `XeSS_LICENSE.txt`, `DirectX_LICENSE.txt`, `RenoDX_ATTRIBUTION.txt`,
`danielblnc_ATTRIBUTION.txt`, `dlssg-to-fsr3_ATTRIBUTION.txt`, the multilingual READMEs, `CHANGELOG.md`,
the bundled `Anywhere/Magpie.exe`.

## 6. Exact licences found

| Component | Licence found | Evidence |
|---|---|---|
| Repository as a whole (OptiScaler fork) | GPL-3.0, plus additional terms under GPL-3.0 §7(b),(c),(e): mandatory credit in README/About, no presenting as own work, no rights to the AMDNR name | `LICENSE`; `AMDNR_NOTICE.txt` §3–4 |
| AMDNR-authored source files | `SPDX-License-Identifier: GPL-3.0-or-later` | e.g. `gi_temporal.hlsl`, `AmdBridge.cpp` |
| Upstream OptiScaler and DLSS-NR lineage code | GPL-3.0 | Notice §5 |
| AMDNR Launcher | **Source-available, all rights reserved**; copying, adapting or reusing any part is prohibited without written permission | `Launcher/OpenSource/LICENSE.txt` |
| lmxxf network port, kernels, runtime | Claimed MIT ("Copyright (c) 2026 Kien") | `LICENSE.lmxxf`; `AMDNR_RDNA3_BACKEND.txt` |
| NVIDIA DLSS Neural Rendering model — design and weights | Proprietary to NVIDIA; the NVIDIA runtime is not redistributed | Notice §5: "DLSS and the neural network's design and weights belong to NVIDIA"; `dlssnr/README.md` |
| danielblnc runtime | Closed; shipped "with his permission and under its author's own terms" | Notice §5 |
| Magpie fork (window-capture host) | GPL-3.0; one modified binary shipped | Notice §5 |
| AMD FidelityFX (v2), Intel XeSS, Microsoft DirectX | Their own licences (bundled licence files) | Repository root |

## 7. Licence uncertainties (flagged — not interpreted as permission)

1. **Conflicting provenance of the network weights.** The AMDNR notice says the network's design and
   weights belong to NVIDIA; the lmxxf files claim MIT for "network, weights and kernels". A third party
   cannot grant a licence to another company's weights. Status: **LICENCE UNCLEAR — DO NOT INCORPORATE**
   (and very likely incompatible).
2. **Source completeness.** Notice §6 states the AMDNR source "will be published on GitHub with AMDNR 0.5.0",
   yet `main/AMDNR-source/` already contains source. Whether it is complete is unknown.
3. **Additional GPL §7 terms** would bind SIGHTLINE (credits in README/About) if any AMDNR material were included.
4. **Bundled and downloaded binaries** (modified `Magpie.exe`, runtime packages fetched from releases) were not inspected.
5. **Legality of running NVIDIA's network on non-NVIDIA hardware** is outside SIGHTLINE's scope and was not assessed.

This is an engineering licence review, not legal advice.

## 8. Component classification

| Component | Classification | Reason |
|---|---|---|
| OptiScaler interception / hook layer | TECHNICALLY INCOMPATIBLE; LICENCE INCOMPATIBLE | Windows game-API interception has no counterpart in a camera app; GPL-3.0 copyleft conflicts with the assumed proprietary app-store distribution (see ARCHITECTURE.md D-013) |
| `dlssnr` pass and HLSL shaders | TECHNICALLY INCOMPATIBLE; REFERENCE ONLY for ideas | DX12 post-process over rendered frames |
| NVIDIA DLSS NR model / weights (and the lmxxf port of it) | LICENCE UNCLEAR — DO NOT INCORPORATE | Proprietary ownership stated by the repository itself |
| lmxxf HIP kernels and runtime | LICENCE UNCLEAR — DO NOT INCORPORATE; TECHNICALLY INCOMPATIBLE | Bound to the network above; desktop Radeon ISA only |
| Temporal stability / history clamping / SVGF-style accumulation | REFERENCE ONLY | Use the published papers (Schied 2017; Karis 2014; Salvi 2016) as sources, never this code |
| Device-tiered model sizes, SHA-256 pinned model packs, fallbacks, cost ceilings | REFERENCE ONLY | Transferable engineering pattern for on-device model deployment |
| AMDNR Launcher | LICENCE INCOMPATIBLE | All rights reserved |
| Magpie capture host | TECHNICALLY INCOMPATIBLE | Desktop window capture |
| Anything classified DIRECTLY REUSABLE or REUSABLE WITH MODIFICATION | — | **None** |

## 9. Relevance to SIGHTLINE

**As a component: none, and partly negative.** AMDNR's networks are generative appearance models: they
synthesise plausible detail to make frames look better. In a measurement instrument, synthesised detail is a
hazard, because it can move an edge or a centre without any evidence in the photons. SIGHTLINE's success
criterion is measurement accuracy, not visual quality.

**Transferable concepts (idea level only):**

1. *History rejection.* Temporal accumulation must reject history that disagrees with the current
   observation. The SIGHTLINE analogue is outlier-robust temporal fusion of per-frame target-centre
   measurements (see `docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md`).
2. *Device tiers.* Ship different model or processing tiers per device class, pinned by hash, with explicit fallbacks.
3. *Budgets.* Dynamic resolution and cost ceilings to hold a latency budget on weak phones.
4. *Literature lead.* The notice cites Hartley (1997), rotating-camera self-calibration. A handheld phone aimed
   at a target mostly rotates, so this line of work is relevant to SIGHTLINE calibration (logged as R-009 in
   `research/RESEARCH_LOG.md`, with the gyroscope-based method of Karpenko et al. 2011 as the more direct fit).

## 10. Decision and confidence

* **Decision (ARCHITECTURE.md D-007):** no code, shader, model, weight or asset from this repository enters SIGHTLINE.
* **Confidence:** High for the licence facts (read directly from files at the stated commit). Medium for the
  architecture description (from documentation and headers, not a full code read). No confidence is claimed for
  any legal conclusion beyond "do not incorporate".
* **Follow-up:** none required. Re-review only if a future proposal wants to use anything from this repository.
