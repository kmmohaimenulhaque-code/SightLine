FDM printing guidelines:

| Part | Material | Orientation | Layer Height | Infill | Supports | Critical Surfaces |
|---|---|---|---|---|---|---|
| Chassis body | PETG | Upright (grip down) | 0.2mm | 40% | Yes (overhangs >45°) | T-slot, pin holes, adapter face |
| Grip handle | PETG | Upright | 0.2mm | 30% | Minimal | Palm surface, fastener bosses |
| Phone adapter (iPhone 15) | PETG | Face down (adapter face on bed) | 0.15mm | 50% | Yes (cradle walls) | Pin holes, phone locating faces |
| Ballast carriage | PLA+ | Flat (platform up) | 0.2mm | 60% | No | T-nut profile, locking screw hole |

Tolerances:
- General FDM: ±0.2-0.3mm
- Pin holes (3mm, 2mm): Print undersize by 0.15mm, ream to size. Or use steel dowel pins pressed into 2.85mm/1.85mm printed holes.
- T-slot: Print a test coupon first — 25mm section of the rail and a matching T-nut. Adjust clearance parameter (default 0.15mm per side) based on actual slider fit.
- Phone cradle: Print a test strip of the phone-locating wall. Verify phone sits against datum faces without excessive force.
- Camera clearance: Verify 2mm minimum gap between printed material and any lens glass.

Calibration prints (print these first):
1. Pin-hole test: 3mm and 2mm holes, verify fit with actual pins
2. T-slot coupon: 25mm rail section + T-nut slider
3. Phone edge strip: 30mm section of phone cradle wall
