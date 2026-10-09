# ml/evaluation

Experiment harnesses and their results (`results/<experiment id>/`: `trials.csv`, `summary.json`, `summary.md`,
`config.json`). Every experiment is logged in `EXPERIMENT_LOG.md`.

| Module | Experiment | Input |
|---|---|---|
| `e001_localisation_budget.py` | E-001 | synthetic |
| `e004a_ois_transfer.py` | E-004a | capture manifest + clip (+ gyro log) |
| `e004b_android_probe.py` | E-004b | JSON files written by the probe app |
| `e002_static_capture.py` | E-002 | capture manifest + static clip |
| `e003_domain_gap.py` | E-003 | the same clips |
| `e005_localisation_limit.py`, `crlb.py` | E-005 | synthetic model |
| `cal_exp6_gyro.py` | CAL-EXP-6 | gyro manifest + CSV |
| `capture_analysis.py`, `status.py` | shared | tracking, f_px, static analysis; status vocabulary and evidence class |
