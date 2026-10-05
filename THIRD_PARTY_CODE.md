# Third-Party Code Register

SIGHTLINE may reuse third-party code when it is legally reusable and technically appropriate. Procedure (master
prompt §7):

INSPECT → IDENTIFY LICENCE → CHECK COMPATIBILITY → CHECK DEPENDENCIES → CHECK ATTRIBUTION → REUSE IF PERMITTED →
PRESERVE NOTICES → DOCUMENT PROVENANCE (this file).

If a licence is absent or ambiguous: **stop and flag it**. An absent licence is never read as permission.

Compatibility baseline: SIGHTLINE's own licence is undecided (ARCHITECTURE.md D-013). Until decided, compatibility is
assessed as if SIGHTLINE were proprietary software distributed through app stores. Under that assumption, permissive
licences (MIT, BSD, Apache-2.0) are compatible with notice; strong copyleft (GPL-3.0) is not.

## 1. Incorporated third-party source code

**None.** All source code in this repository at version 0.1.0 is original SIGHTLINE work. Algorithms implemented from
published literature (e.g. the direct least-squares ellipse fit) were written from the mathematics, not copied from
any implementation; the literature is cited in `SOURCES_AND_LICENSES.md` S-15.

## 2. Dependencies (linked at runtime, not copied)

NumPy and OpenCV (runtime), pytest (development). Licences and versions: `SOURCES_AND_LICENSES.md` §2.

## 3. Evaluated and not incorporated

| Project | Decision | Classification summary | Analysis |
|---|---|---|---|
| AMD-NR---OptiScaler (3zwr1) | Not incorporated | GPL-3.0 + additional terms; NVIDIA-owned network weights; launcher all rights reserved; Windows/DX12/HIP only | `research/AMD_NR_OPTISCALER_ANALYSIS.md` |
| AMD FidelityFX / FSR SDK 2.3.0 | Not incorporated | FSR 2/3 MIT but technically mismatched; FSR 4 signed binary with ambiguous terms | `research/AMD_FIDELITYFX_ANALYSIS.md` |

## 4. Entry template (copy for each incorporated component)

```
### <component name>
- Project / URL:
- Commit or version:
- Files / component:
- Original author(s):
- Licence (exact SPDX id + link to licence text at that commit):
- Copyright notice requirements:
- Dependencies pulled in (and their licences):
- Reason for reuse (what problem, what alternatives were compared):
- SIGHTLINE modifications (list, with commit ids):
- Redistribution implications (binary/app-store, source, attribution placement):
- Notice preserved at: <path>
- Reviewed by / date:
```
