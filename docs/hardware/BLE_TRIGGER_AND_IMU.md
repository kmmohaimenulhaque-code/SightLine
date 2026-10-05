# BLE Trigger and IMU — Requirements and Architecture (Phase 7, not started)

**Scope and safety.** The trigger is an **input device only**: a switch that reports a timestamped event. It contains
no mechanism that stores energy to launch anything, and nothing in SIGHTLINE may be adapted to do so (REQUIREMENTS.md
SAF-01). The grip is a passive phone and sensor holder.

## 1. Requirements

| ID | Requirement | Status |
|---|---|---|
| HW-01 | Report each press with a device-side timestamp (µs resolution, MCU timer captured on the switch edge) and a sequence counter | DESIGN TARGET |
| HW-02 | End-to-end trigger-to-app timing known to ≤ 5 ms (1σ) after compensation | DESIGN TARGET (from error term E7) |
| HW-03 | Debounce in hardware (RC) and firmware; no double events within 50 ms | DESIGN TARGET (value is an ASSUMPTION, to tune) |
| HW-04 | Survive reconnection without losing or duplicating events (sequence counter + replay buffer) | DESIGN TARGET |
| HW-05 | Battery life ≥ 20 training sessions; low-battery reporting | DESIGN TARGET |
| HW-06 | Works with Android and iOS without custom OS drivers | DESIGN TARGET |
| HW-07 | Adjustable pull weight with a reference setting ≥ 500 g (ISSF 10 m air pistol minimum trigger weight, Pistol Rules 8.12) and an optional two-stage feel | DESIGN TARGET; ISSF value VERIFIED |
| HW-08 | Uses a pre-certified BLE module (radio compliance) | DESIGN TARGET |

## 2. Architecture options

| Option | Pros | Cons | Status |
|---|---|---|---|
| A. BLE HID (keyboard / consumer control) | No pairing app logic; iOS may accept intervals down to 11.25 ms with HID (Apple QA1931) | OS consumes HID events; no device timestamp; latency unobservable | Rejected for measurement |
| **B. Custom GATT service with notifications** | Carries device timestamp + counter; supports a clock-sync handshake; latency measurable | Needs app-side BLE code | **Proposed** |
| C. Wired (USB-C) | Lowest, most stable latency | Cable on a hand-held instrument | Fallback for lab validation |

**Clock synchronisation (option B):** NTP-style ping–pong over GATT (app sends t1, device replies t2/t3, app records
t4) repeated during the session; estimate offset and round-trip, keep the minimum-delay samples. Apple's accessory
rules (Interval Min ≥ 15 ms, sometimes scaled to 30 ms) imply up to one interval of delivery delay, so raw arrival
time is not a usable shot time.

## 3. IMU

* **Phone IMU** (gyroscope + accelerometer): angular motion for calibration (`docs/calibration/CALIBRATION_STRATEGY.md`
  §2.3), roll for shot-direction display, and an independent motion trace around the trigger.
* **Optional grip IMU** (high-rate, e.g. ≥ 400 Hz — ASSUMPTION) for trigger-jerk analysis, synchronised like the trigger.
* Axis conventions of each platform's device frame must be verified and documented before IMU data is fused (OPEN).

## 4. Latency measurement — EXP-HW-1 (planned)

An LED on the trigger board lights on the same interrupt that timestamps the press, positioned inside the camera's
view. The first frame (and row, accounting for rolling shutter) showing the LED, versus the BLE event's device
timestamp mapped to the app clock, gives the end-to-end latency distribution per phone. 200 presses per device;
report mean, standard deviation and maximum.

## 5. Firmware notes (to be specified in `hardware/ble-trigger/`)

Interrupt on switch edge → capture timer → debounce window → enqueue {seq, t_device} → notify; ring buffer of the
last N events for replay after reconnection; battery measurement characteristic; firmware version characteristic.
