# AMD FidelityFX / FSR SDK — Research and Licence Analysis

| Field | Value |
|---|---|
| Date | 2026-10-05 |
| Analyst | Claude (Opus 5.5) research session |
| Repository | <https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK> |
| Commit inspected | `60f4ea81909200d8542eca14dccb2628b763a9a3` (2026-06-24, "AMD FSR SDK 2.3.0") on `main` |
| Tags present | `v1.0.0` … `v1.1.4`, `v2.0.0`, `v2.1.0`, `v2.1.1`, `v2.2.0`, `v2.3.0`, `fsr3-v3.0.3`, `fsr3-v3.0.4` |
| Method | Read-only blobless clone outside the SIGHTLINE repository; docs, licence and tree listings read with `git show` / `git ls-tree`. **No file was copied into SIGHTLINE.** |
| Overall verdict | Nothing incorporated. FSR 2/3 sources are MIT-licensed but technically mismatched; FSR 4 is a signed DX12 binary with an ambiguous licence position. The *principles* of multi-frame reconstruction transfer; the code does not. |

---

## 1. SDK architecture (2.x)

The repository README now brands the product "AMD FSR™ SDK 2.3.0 — Redstone". Layout:

| Path | Role |
|---|---|
| `Kits/FidelityFX/api`, `…/upscalers/include`, `…/framegeneration`, `…/denoisers`, `…/radiancecache` | FFX API headers (`ffxCreateContext`, `ffxDispatch`, `ffxQuery`) and per-technique headers |
| `Kits/FidelityFX/signedbin/` | Signed Windows DLLs: `amd_fidelityfx_upscaler_dx12.dll`, `…_framegeneration_dx12.dll`, `…_denoiser_dx12.dll`, `…_radiancecache_dx12.dll`, `…_loader_dx12.dll/.lib` |
| `Kits/FidelityFX/upscalers/fsr3/` | Source (C++ host code + HLSL shaders) for FSR 2 and FSR 3 temporal upscalers |
| `Kits/Cauldron2/` | Sample framework (DX12) |
| `Kits/OpenSource/` | Third-party code: imgui, nlohmann json, stb, vectormath, AMD AGS/ACS/Anti-Lag 2, memory allocator |
| `Samples/`, `Tools/` | Sample applications; media download tool |

Host integration is through the FFX API; techniques are loaded from the signed DLLs. The README's known-issues
table states that Vulkan is not currently supported in the SDK.

### Techniques in 2.3.0 (from `readme.md`)

| Technique | Version | Kind |
|---|---|---|
| FSR Super Resolution (Temporal) | 2.3.4 | Hand-designed temporal accumulation |
| FSR Super Resolution (Upscaler) | 3.1.5 | Hand-designed temporal accumulation |
| FSR Upscaling (ML-Upscaler) | 4.1.1 | Machine-learning upscaler |
| FSR Frame Generation / Swapchain | 3.1.6 / 3.1.7 | Frame interpolation |
| FSR Frame Generation (ML) | 4.0.1 | ML frame interpolation |
| FSR Ray Regeneration (ML-Denoiser) | 1.2.0 | ML denoiser for ray tracing |
| FSR Radiance Caching | Preview | ML radiance cache |

## 2. FSR 2/3 temporal reconstruction (hand-designed)

From `docs/techniques/super-resolution-temporal.md` at tag `v1.1.4` ("The technique" section) and the 2.3.0 docs:

1. **Luminance pyramid** — automatic exposure estimate.
2. **Reconstruct and dilate** — dilates depth and motion vectors so thin geometry keeps correct motion.
3. **Depth clip** — detects disocclusion (history that is no longer valid).
4. **Create locks** — protects thin features from being averaged away.
5. **Reproject and accumulate** — resamples history with the motion vectors (Lanczos-based kernel) and
   blends it with the new jittered sample.
6. **RCAS** — robust contrast-adaptive sharpening.

**Required inputs:** jittered colour, depth, per-pixel motion vectors, exposure, optional reactive and
transparency masks. The application must apply sub-pixel camera jitter; the SDK provides a Halton(2,3)
sequence for it (2.3.0 docs, "Camera jitter").

## 3. FSR 4 (ML upscaler)

From `Kits/FidelityFX/docs/techniques/super-resolution-ml.md` (2.3.0):

* "requires integration using the AMD FSR™ API and use of the signed binary distribution"; shader model HLSL `CS_6_6`.
* Inputs: colour, depth, motion vectors, exposure; reactive and transparency masks are optional ("FSR4 no
  longer requires the title to generate" them).
* Quality modes: 1.0× (NativeAA) to 3.0× (Ultra performance) per dimension.
* **No FSR 4 source in the public tree.** Verified by listing the trees of `v2.0.0`, `v2.1.0`, `v2.2.0` and
  `v2.3.0`: FSR 4 appears only as documentation and media files.

**Accidental publication (2025).** Press reports dated 2025-08-21 (Tom's Hardware) describe AMD briefly
publishing FSR 4 source code during the SDK 2.0 launch, with FP8 and INT8 variants, and then removing it. That
material is not in the repository history as fetched. Any copies circulating elsewhere are
**LICENCE UNCLEAR — DO NOT INCORPORATE**.

## 4. Licensing (exact findings)

* `docs/license.md` (identical to `Kits/FidelityFX/docs/license.md`) opens with a **default licence for
  "all files except as noted below"**: redistribution in **binary form only**, and "No reverse engineering,
  decompilation, or disassembly of this Software is permitted."
* It then lists files that "are subject to" an **MIT** licence. At 2.3.0 that list has **845 entries, and the
  public tree has 845 files; every file in the tree is on the MIT list**, including the signed DLLs in
  `signedbin/` (verified by comparing the two lists).
* **Ambiguity:** binary DLLs listed under MIT while the default terms forbid reverse engineering. For the
  signed binaries SIGHTLINE treats this as **LICENCE UNCLEAR — DO NOT INCORPORATE**.
* FSR 2/3 source (`Kits/FidelityFX/upscalers/fsr3/**`) is on the MIT list. At `v1.1.4`, `LICENSE.txt` is a
  plain MIT licence (Copyright 2024 AMD).
* `3rdpartynotice.md` lists vcpkg, DX12 Agility SDK, DirectX headers, DXC, imgui (MIT), nlohmann json (MIT),
  PIX, stb (MIT) and vectormath, each under its own licence.

This is an engineering licence review, not legal advice.

## 5. Transferability to a mobile-camera measurement problem

| FSR assumption | SIGHTLINE reality | Consequence |
|---|---|---|
| The renderer applies known sub-pixel jitter (Halton) | Jitter comes from uncontrolled hand tremor | Sub-pixel diversity exists but must be estimated, not commanded |
| Exact per-pixel motion vectors and depth from the engine | Nothing provided; motion must be estimated from images (and gyroscope) | Registration error becomes part of the measurement error |
| Goal: perceived quality (stability, sharpness) | Goal: unbiased geometry (target centre, scale) | Visual upscaling ≠ measurement reconstruction |
| Desktop GPU, DX12 compute, signed DLLs | Phone SoC: Metal / Vulkan / NPU | No code path transfers |

**Why single-frame upscaling cannot be the answer (DERIVED).** Any single-frame upscaler (FSR 1 EASU/RCAS,
bicubic, a learned SR network) is a deterministic function of the observed pixels. By the data-processing
inequality it cannot add information about the target's position. It can only help an estimator that was
sub-optimal on the raw pixels (for example a threshold-based detector), and sharpening kernels with overshoot
(Lanczos, RCAS) can shift edge positions and so *bias* a geometric measurement. Phase 5 therefore treats
single-frame processing as a hypothesis to test for bias and benefit against the specific baseline estimator,
never as a default.

**What does transfer (principles):**

1. *Multi-frame accumulation with sub-pixel diversity* is the genuine information source. Handheld multi-frame
   super-resolution (Wronski et al., ACM TOG 2019) shows natural hand tremor supplies that diversity in real
   phone bursts.
2. *For SIGHTLINE, fuse in the parameter domain, not the image domain.* The hand motion is the signal being
   measured, so averaging images would blur it. Instead: estimate the static target shape (scale, ellipse)
   pooled over many frames, and the dynamic target-centre trajectory with a temporal filter (ARCHITECTURE.md D-009).
3. *History rejection and disocclusion handling* map to outlier rejection and occlusion detection (a hand or
   object passing in front of the target).
4. *Locked exposure* across a shot sequence (FSR's exposure handling is a reminder that auto-exposure changes
   break temporal consistency).
5. *Quality modes and debug checkers* map to device tiers and built-in measurement validators.

## 6. Component classification

| Component | Classification | Reason |
|---|---|---|
| FSR 4 ML upscaler (signed DLL) | LICENCE UNCLEAR — DO NOT INCORPORATE; TECHNICALLY INCOMPATIBLE | Ambiguous binary terms; DX12/Windows; no source |
| FSR 4 source from the 2025 accidental publication | LICENCE UNCLEAR — DO NOT INCORPORATE | Withdrawn by AMD; provenance of copies unknown |
| FSR 2/3 temporal upscaler source (`upscalers/fsr3/**`) | REFERENCE ONLY | MIT permits reuse with notice, but inputs and goal do not match a camera measurement |
| FSR 1 spatial EASU/RCAS (MIT in SDK 1.x) | REQUIRES FURTHER INVESTIGATION | Candidate "classical processing" arm for Phase 5; adopt only if it measurably helps without bias, and then record it in THIRD_PARTY_CODE.md |
| Halton(2,3) jitter utilities | REFERENCE ONLY | Cannot command jitter on a camera; a low-discrepancy sequence is useful for sampling sub-pixel phases in synthetic data (implemented independently) |
| FFX API, loader, Cauldron2 framework | TECHNICALLY INCOMPATIBLE | Windows / DX12 host framework |
| Frame Generation (3.x and ML 4.x) | TECHNICALLY INCOMPATIBLE; measurement hazard | Interpolated frames are fabricated observations |
| Ray Regeneration, Radiance Caching | TECHNICALLY INCOMPATIBLE | Rendering-specific |
| Anything DIRECTLY REUSABLE | — | **None** |

## 7. Decision and confidence

* **Decision (ARCHITECTURE.md D-007):** no FidelityFX/FSR code, binary or shader is incorporated. The
  principles above inform Phase 5. If a spatial sharpener is ever adopted, its exact file, commit and MIT notice
  go into THIRD_PARTY_CODE.md first.
* **Confidence:** High for licence text and repository structure (read directly). Medium for the algorithm
  descriptions (documentation only, source not studied). The FSR 4 accidental-publication facts rest on press
  reporting (one article read).
