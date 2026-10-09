# hardware/imu

Optional grip-mounted IMU and phone-IMU integration notes.

Status: **not started** (Phase 7). See `docs/hardware/BLE_TRIGGER_AND_IMU.md` §3 and
`docs/calibration/CALIBRATION_STRATEGY.md` §2.3. Platform device-frame axis conventions must be verified and
documented here before any IMU data is fused.

Raw gyroscope characterisation (rate, jitter, bias, noise, Allan deviation, axis convention) is experiment
CAL-EXP-6: code in `app/imu/gyro.py`, protocol in `docs/experiments/CAL-EXP-6_GYRO_PROTOCOL.md`. No device has been
measured yet; the axis table below is therefore empty.

| Device | Physical rotation | Device axis and sign | Source |
|---|---|---|---|
| — | — | — | to be measured |
