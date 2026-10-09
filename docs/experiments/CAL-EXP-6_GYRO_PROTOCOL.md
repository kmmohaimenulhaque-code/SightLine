# CAL-EXP-6 — Physical protocol: raw gyroscope characterisation

Status: **PHYSICAL_DATA_REQUIRED**. Analysis: `app/imu/gyro.py`, `ml/evaluation/cal_exp6_gyro.py`.
Deterministic statistics only. No Kalman filter, no fusion, no learning until these numbers exist.

| Log | How | Gives |
|---|---|---|
| Static, 10 min (1 h if possible) | phone at rest on a solid table, screen on, not charging; note room temperature | sample rate, interval jitter, gaps, bias, noise, Allan deviation |
| Axis, 3 short logs | rotate the phone about one physical axis at a time in a stated sense (e.g. "top edge away from me") | which device axis and sign corresponds to which physical rotation |
| Rate request | same static log at each rate the logger offers | what rate the phone actually delivers |

* Android: probe app buttons 5 (60 s) and 6 (10 min) → CSV `timestamp_ns,x,y,z` in rad/s.
* iPhone: any logger that exports CSV with a time column and x/y/z rotation rates. Column layouts differ between
  apps and none was verified here: give the column names and the rate unit in the manifest. Whether a logger keeps
  running while a camera app is in front is an open question (research report Q2f) — test it before relying on it.

Manifest: a provenance record (category TEAM_COLLECTED) whose `parameters` contain `experiment: "CAL-EXP-6"`,
`capture_id`, `device`, `os_version`, `app`, `kind` (`static` or `axis:<physical rotation>`), `placement`,
`requested_rate_hz`, `rate_unit`, and the file's sha256 under `files`.

```sh
python -m ml.evaluation.cal_exp6_gyro --manifest <gyro manifest.json> --log <log.csv>
```

The Allan curve is not evaluated beyond a tenth of the record length; a 10 min log cannot show the bias-instability
floor of a typical MEMS gyroscope and the report says so instead of extrapolating.
