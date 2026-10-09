# SIGHTLINE — branch mission-2-experimental-validation: full substitution files

Every file here is complete. Put each at the same path in the repository, on a new branch
`mission-2-experimental-validation` created from `main` (commit 03ce07e). Do not commit to main.

On GitHub (browser): switch branch → type the new branch name → "Create branch"; then Add file → Upload files,
drag the folders, commit to that branch.

With git on a computer, the bundle is simpler and keeps the seven commits:

    git fetch /path/to/SightLine_mission-2.bundle mission-2-experimental-validation:mission-2-experimental-validation
    git push origin mission-2-experimental-validation

| Action | File |
|---|---|
| NEW | `.gitignore` |
| REPLACE | `ARCHITECTURE.md` |
| REPLACE | `CHANGELOG.md` |
| REPLACE | `DATASET_SPEC.md` |
| REPLACE | `EXPERIMENT_LOG.md` |
| REPLACE | `PROJECT_SPEC.md` |
| REPLACE | `README.md` |
| REPLACE | `SOURCES_AND_LICENSES.md` |
| REPLACE | `VALIDATION.md` |
| REPLACE | `app/__init__.py` |
| REPLACE | `app/analytics/__init__.py` |
| NEW | `app/analytics/timeseries.py` |
| NEW | `app/calibration/angular.py` |
| NEW | `app/imu/__init__.py` |
| NEW | `app/imu/gyro.py` |
| REPLACE | `app/mobile/README.md` |
| NEW | `app/mobile/android-probe/AndroidManifest.xml` |
| NEW | `app/mobile/android-probe/README.md` |
| NEW | `app/mobile/android-probe/build_apk.sh` |
| NEW | `app/mobile/android-probe/src/org/sightline/probe/MainActivity.java` |
| NEW | `app/vision/characterise.py` |
| NEW | `app/vision/motion.py` |
| NEW | `app/vision/video.py` |
| REPLACE | `data/manifests/README.md` |
| NEW | `data/manifests/captures/README.md` |
| REPLACE | `docs/cad/GRIP_REQUIREMENTS.md` |
| REPLACE | `docs/calibration/CALIBRATION_STRATEGY.md` |
| NEW | `docs/experiments/CAL-EXP-6_GYRO_PROTOCOL.md` |
| NEW | `docs/experiments/E-002_E-003_PROTOCOL.md` |
| NEW | `docs/experiments/E-004A_PROTOCOL.md` |
| NEW | `docs/experiments/E-004B_PROTOCOL.md` |
| NEW | `docs/experiments/MISSION_2_EXPERIMENTAL_REPORT.md` |
| NEW | `docs/experiments/README.md` |
| NEW | `docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf` |
| REPLACE | `docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md` |
| REPLACE | `docs/science/ERROR_BUDGET.md` |
| REPLACE | `hardware/imu/README.md` |
| REPLACE | `ml/configs/README.md` |
| NEW | `ml/configs/e004a.json` |
| NEW | `ml/configs/e005.json` |
| NEW | `ml/datasets/capture.py` |
| NEW | `ml/datasets/synthetic_sequence.py` |
| REPLACE | `ml/datasets/synthetic_target.py` |
| REPLACE | `ml/evaluation/README.md` |
| NEW | `ml/evaluation/cal_exp6_gyro.py` |
| NEW | `ml/evaluation/capture_analysis.py` |
| NEW | `ml/evaluation/crlb.py` |
| NEW | `ml/evaluation/e002_static_capture.py` |
| NEW | `ml/evaluation/e003_domain_gap.py` |
| NEW | `ml/evaluation/e004a_ois_transfer.py` |
| NEW | `ml/evaluation/e004b_android_probe.py` |
| NEW | `ml/evaluation/e005_localisation_limit.py` |
| NEW | `ml/evaluation/results/E-004a/expected_displacements.md` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/main_scale__A_static__none/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/main_scale__B_step__lock/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/main_scale__B_step__none/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/main_scale__B_step__recentring/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/main_scale__D_oscillation__lock/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/main_scale__D_oscillation__none/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/summary.md` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/uw_scale__A_static__none/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/uw_scale__B_step__lock/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/uw_scale__B_step__none/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/uw_scale__B_step__recentring/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/uw_scale__D_oscillation__lock/summary.json` |
| NEW | `ml/evaluation/results/E-004a/synthetic_sanity/uw_scale__D_oscillation__none/summary.json` |
| NEW | `ml/evaluation/results/E-005/config.json` |
| NEW | `ml/evaluation/results/E-005/summary.json` |
| NEW | `ml/evaluation/results/E-005/summary.md` |
| NEW | `ml/evaluation/status.py` |
| REPLACE | `pyproject.toml` |
| REPLACE | `research/RESEARCH_LOG.md` |
| REPLACE | `scripts/README.md` |
| NEW | `scripts/make_print_target.py` |
| NEW | `tests/test_angular.py` |
| NEW | `tests/test_capture_and_status.py` |
| NEW | `tests/test_crlb.py` |
| NEW | `tests/test_e002_e003_gyro.py` |
| NEW | `tests/test_e004a.py` |
| NEW | `tests/test_e004b.py` |
| NEW | `tests/test_gyro.py` |
| NEW | `tests/test_motion.py` |
| NEW | `tests/test_print_target.py` |
| NEW | `tests/test_timeseries.py` |

Nothing is deleted. 142 tests pass on this tree (`python -m pytest`).
