# G0 Bill of Materials

Prices below are **planning allowances**, not confirmed local prices or availability. Replace them with a quote or receipt before procurement. Quantities are for one instrument and assume the iPhone adapter configuration.

| Item | Qty | Material / specification | Evidence / source | Planning cost status |
|---|---:|---|---|---|
| Common chassis, grip and mounts | 1 set | PETG or tough PLA+, bright colour | G0 CAD output | filament allowance only; unpriced locally |
| iPhone 15 adapter module | 1 | PETG/nylon; replaceable pads | `iphone_adapter` export | filament allowance only |
| Optional Android adapter | 0–1 | PETG/nylon; only after device selection | `android_adapter` export | not a supported-device purchase |
| Captive X ballast weight stack | 1 | measured steel washers or purpose-made captive weights, nominal 180 g | solver input is provisional | source and price TBD |
| Captive Z ballast weight stack | 1 | measured steel washers or purpose-made captive weights, nominal 125 g | solver input is provisional | source and price TBD |
| M4-scale chassis/adapter fasteners | provisional set | screw/washer/nut or heat-set insert selected from supplier | G0 placeholders only | exact quantity/spec TBD |
| M3/M4 insert test coupon hardware | 1 set | matching inserts and screws | manufacturing test | source/price TBD |
| Replaceable soft contact pads | 4–8 | thin TPU, silicone or closed-cell foam; non-datum | G0 pad placeholders | material and compression TBD |
| Passive fiducial marker | 1 | printed high-contrast marker / plate | optical reference interface | marker design TBD |
| Optional input-only BLE switch | 0–1 | pre-certified BLE module/switch | `docs/hardware/BLE_TRIGGER_AND_IMU.md` | not selected |
| Optional IMU board | 0–1 | selected sensor board, rigid mount | CAL-EXP-6 path | not selected |

## Hardware safety notes

Use captive, enclosed or positively retained weights. No loose weight may be able to fall onto the phone or user. The input switch is passive and reports events; it must not actuate any launching or pressure mechanism. Avoid exposed sharp edges and magnetic materials near an untested phone camera/compass/IMU.

## Procurement completion

The BOM becomes procurement-ready only after the following are filled:

* selected printer/material and filament mass;
* fastener thread, length, head and insert supplier dimensions;
* measured ballast mass and retention method;
* phone/case used for each adapter;
* local supplier, availability date, unit price, currency and receipt/quote reference.

Until quotes are available, use these clearly marked estimate formulas rather than an invented local price:

| Cost group | Estimate formula | Current value |
|---|---|---|
| Printed parts | measured post-processing filament mass × quoted filament price per kg + failed-print allowance | `TBD — no printer/material mass or local quote` |
| Fasteners/inserts | quantity × supplier unit price + 10% spare allowance | `TBD — thread and supplier not selected` |
| Ballast | measured weight-stack mass × quoted steel/washer unit rate + retention hardware | `TBD — weight form not selected` |
| Optional BLE/IMU | selected board/module quote + enclosure hardware | `TBD — electronics not selected` |
