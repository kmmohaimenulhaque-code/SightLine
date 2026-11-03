# Graph Report - SightLine  (2026-11-03)

## Corpus Check
- 212 files · ~146,540 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 106 file(s) not represented in the graph (top: .stl 97, .gz 4, .graphify-bak 1)

## Summary
- 1362 nodes · 3585 edges · 81 communities (69 shown, 12 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 169 edges (avg confidence: 0.87)
- Token cost: 515,580 input · 0 output

## Community Hubs (Navigation)
- Aiming Mark Measurement
- Ellipse Fitting
- Time-Series Analysis
- G1 CAD Reports
- G1 Assembly & Mass
- G1 Part Geometry
- Synthetic Sequences
- Image Characterisation
- E-004b Android Probe
- Angular Calibration
- Camera Render & CRLB
- Experiment Log & Decisions
- Per-Frame Motion
- OIS Clip Analysis
- Android Probe Imports
- Target Pose & Impact
- Architecture Decisions
- Camera Model
- Mission 2 Research
- G1 CAD Tests
- Capture Templates
- Capture Manifest CLI
- Grip Requirements
- Dataset Provenance
- ISSF Scoring
- Gyro Log Loading
- Android Runnables
- Video I/O
- Dataset Spec
- G1 Assembly Config
- E-004a Harness
- G1 CAD Checks
- Allan Deviation
- G1 Renders
- Temporal Reconstruction Research
- Analytics Requirements
- Camera2 Callbacks
- Mobile App Platform
- Pellet Ballistics
- BLE Trigger & IMU
- Coordinate Frames
- Multi-device Calibration
- Reconstruction Gates
- Baseline Estimators E-001
- AMD-NR / DLSS Licensing
- Sources & Licences
- Research Log
- Project Spec
- Error Budget
- ML Gate & Model Card
- Target Geometry Docs
- E-001 Experiment Script
- Print Target Script
- Scoring Tests
- Display Geometry
- CAD Export Manifest
- Baseline Vision Pipeline
- Test Target SL-T1
- Data Folders
- Camera Stabilisation APIs
- Gyro Self-Calibration Lit
- Mission 2 Research Refs
- Trigger Timing Prior Art
- ML Inference/Training Gate
- Print Target Tests
- graphify Config
- Probe UI Buttons
- CAD Folder Docs
- Rolling Shutter & OIS
- External Datasets
- Angular Size
- Param Attribute Access
- build_apk Script
- Model Docs
- Root Package

## God Nodes (most connected - your core abstractions)
1. `CameraModel` - 54 edges
2. `MainActivity` - 34 edges
3. `render()` - 32 edges
4. `SIGHTLINE Mission 2 Research Report (camera stabilisation, localisation limits, sight geometry, licensing)` - 32 edges
5. `build()` - 30 edges
6. `Ellipse` - 29 edges
7. `SIGHTLINE Architecture` - 28 edges
8. `main()` - 25 edges
9. `Degradation` - 25 edges
10. `analyse()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `SIGHTLINE test target SL-T1-A4` --implements--> `ISSF 10 m air-pistol target geometry`  [INFERRED]
  docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf → research/RESEARCH_LOG.md
- `SIGHTLINE test target SL-T1-A4` --conceptually_related_to--> `E-004a/b stabilisation experiment`  [INFERRED]
  docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf → research/RESEARCH_LOG.md
- `Android-first Camera2 platform proposal` --semantically_similar_to--> `D-012 Android-first native Camera2 platform`  [INFERRED] [semantically similar]
  app/mobile/README.md → ARCHITECTURE.md
- `ANA-01 Deterministic hold/trigger metrics` --semantically_similar_to--> `Planned hold/trigger metrics (time in zone, trace speed, displacement)`  [INFERRED] [semantically similar]
  REQUIREMENTS.md → app/analytics/README.md
- `Single-Frame Upscaling Cannot Add Information` --semantically_similar_to--> `Single-Frame Processing Cannot Add Information (Data-Processing Inequality)`  [INFERRED] [semantically similar]
  research/AMD_FIDELITYFX_ANALYSIS.md → docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Mission 2 physical experiments awaiting data** — experiment_log_e_004a, experiment_log_e_004b, experiment_log_e_002, experiment_log_e_003, experiment_log_cal_exp_6 [EXTRACTED 1.00]
- **Evidence required to decide the vision+gyro split** — architecture_d_019_vision_gyro_split, experiment_log_e_004a, experiment_log_e_002, experiment_log_cal_exp_6, validation_c_063 [EXTRACTED 1.00]
- **Stabilisation risk: OIS, Android OIS samples, Ultra Wide control** — sightline_mission_2__iphone_15_and_android_camera_stabilisation__localisation_limits__sight_geometry_and_licensing_iphone15_main_sensor_shift_ois, sightline_mission_2__iphone_15_and_android_camera_stabilisation__localisation_limits__sight_geometry_and_licensing_iphone15_ultra_wide_control, sightline_mission_2__iphone_15_and_android_camera_stabilisation__localisation_limits__sight_geometry_and_licensing_oissample, sightline_mission_2__iphone_15_and_android_camera_stabilisation__localisation_limits__sight_geometry_and_licensing_lens_optical_stabilization_mode, architecture_d_010_stabilisation_off_requirement [INFERRED 0.85]
- **G1 per-configuration checks and mass reports** — cad_exports_g1_g1_and163_rh_checks_checks_report, cad_exports_g1_g1_and163_rh_mass_report_mass_report, cad_exports_g1_g1_ip15_lh_checks_checks_report, cad_exports_g1_g1_ip15_lh_mass_report_mass_report, cad_exports_g1_g1_ip15_rh_checks_checks_report, cad_exports_g1_g1_ip15_rh_mass_report_mass_report [INFERRED 0.95]
- **Physical experiment protocols awaiting data** — docs_experiments_cal_exp_6_gyro_protocol_cal_exp_6_protocol, docs_experiments_e_002_e_003_protocol_e002_e003_protocol, docs_experiments_e_004a_protocol_e004a_protocol, docs_calibration_calibration_strategy_cal_exp_1 [EXTRACTED 1.00]
- **Data category folders with provenance** — data_raw_readme_data_raw, data_interim_readme_data_interim, data_processed_readme_data_processed, data_synthetic_readme_synthetic_v0_1_0, data_manifests_readme_provenance_manifests, data_manifests_captures_readme_capture_manifests [INFERRED 0.85]
- **Mission 2 device experiments awaiting physical data** — docs_experiments_mission_2_experimental_report_e_004a, docs_experiments_e_004b_protocol_e_004b, docs_experiments_mission_2_experimental_report_e_002, docs_experiments_mission_2_experimental_report_e_003, docs_experiments_mission_2_experimental_report_cal_exp_6 [EXTRACTED 1.00]
- **Temporal estimation attacks E1, E7, E8 together** — docs_ml_reconstruction_research_plan_temporal_arm, docs_science_error_budget_e1, docs_science_error_budget_e7, docs_science_error_budget_e8 [EXTRACTED 1.00]
- **Deterministic RAW baseline estimators** — ml_evaluation_results_e_001_summary_moments_estimator, ml_evaluation_results_e_001_summary_edges_estimator, ml_evaluation_results_e_001_summary_hybrid_estimator, app_vision_aiming_mark [INFERRED 0.85]
- **Stabilisation detection and measurement chain** — research_research_log_r_006, research_research_log_r_009, research_research_log_r_013, research_research_log_r_014, research_research_log_e_004_stabilisation_experiment [INFERRED 0.85]
- **Concept document claim checks** — research_research_log_r_000, research_research_log_r_001, research_research_log_r_002, research_research_log_r_003 [EXTRACTED 1.00]
- **Excluded upscaler/denoiser technologies** — research_research_log_r_004, research_research_log_r_005, research_research_log_amd_nr_optiscaler, research_research_log_amd_fidelityfx_fsr [EXTRACTED 1.00]

## Communities (81 total, 12 thin omitted)

### Community 0 - "Aiming Mark Measurement"
Cohesion: 0.07
Nodes (32): local_mm_per_px(), AimingMarkMeasurement, bilinear(), Candidate, EdgeResult, find_candidates(), linearize(), measure_aiming_mark() (+24 more)

### Community 1 - "Ellipse Fitting"
Cohesion: 0.10
Nodes (17): algebraic_residuals(), conic_to_ellipse(), Ellipse, ellipse_from_covariance(), fit_ellipse_direct(), pose_from_aim(), apply_affine(), ellipse_to_target_affine() (+9 more)

### Community 2 - "Time-Series Analysis"
Cohesion: 0.09
Nodes (23): amplitude_spectrum(), _block_sem(), _exposure_average(), find_plateaus(), gyro_referenced_gain(), fit(), _hilbert(), integrate_rate() (+15 more)

### Community 3 - "G1 CAD Reports"
Cohesion: 0.11
Nodes (38): G1-AND163-RH CAD Checks Report, G1-AND163-RH Mass Report, G1-IP15-LH CAD Checks Report, G1-IP15-LH Mass Report, G1-IP15-RH CAD Checks Report, G1-IP15-RH Mass Report, CAD Physical Measurements Folder, build.py (CAD regeneration) (+30 more)

### Community 4 - "G1 Assembly & Mass"
Cohesion: 0.10
Nodes (26): combine(), frames_report(), load_params(), mass_summary(), mass_table(), part_mass(), export_assembly(), export_shape() (+18 more)

### Community 5 - "G1 Part Geometry"
Cohesion: 0.17
Nodes (31): angle_dial_parts(), _axis_dir(), _axis_pt(), box(), cradle_parts(), cyl(), ellipse(), fixed_bars() (+23 more)

### Community 6 - "Synthetic Sequences"
Cohesion: 0.11
Nodes (20): render_sequence(), Appearance, Degradation, expected_canvas(), _motion_kernel(), _overlap(), target_reflectance(), crlb_covariance() (+12 more)

### Community 7 - "Image Characterisation"
Cohesion: 0.09
Nodes (18): blockiness(), edge_metrics(), radial_profile(), temporal_noise(), characterise(), _gyro_manifest(), test_blockiness_detects_an_8_px_grid(), test_characterisation_recovers_the_generator_parameters() (+10 more)

### Community 8 - "E-004b Android Probe"
Cohesion: 0.08
Nodes (31): Camera2 Capability Dump, E-004b Android Probe Protocol, e004b_android_probe analysis module, E-004b Android Camera2/OIS Experiment, SIGHTLINE Probe Android App, C-052 Design Finding, C-053 Design Finding, C-054 Inter-frame Encoders Repeat Static Content (+23 more)

### Community 9 - "Angular Calibration"
Cohesion: 0.14
Nodes (15): angle_from_image_shift_rad(), expected_image_shift_px(), exposure_response(), focal_px_from_target(), lever_angle_rad(), Measured, _expected_steps_px(), test_expected_shift_matches_exact_pinhole_projection() (+7 more)

### Community 10 - "Camera Render & CRLB"
Cohesion: 0.13
Nodes (17): E-005 Cramér–Rao Bound Experiment, random_spec(), render(), SceneSpec, SyntheticSample, baseline_without_compression(), main(), run() (+9 more)

### Community 11 - "Experiment Log & Decisions"
Cohesion: 0.14
Nodes (28): Camera2 capability probe and OIS/gyro logger app, Version 0.2.0 Mission 2 experimental validation, CAL-EXP-6 Raw gyroscope characterisation, Experiment Log, E-002 Real iPhone 15 static repeatability capture, E-003 Synthetic to real domain gap, E-004a iPhone 15 OIS/EIS transfer function (Main vs Ultra Wide), E-004b Android Camera2 capability probe and OIS-sample validation (+20 more)

### Community 12 - "Per-Frame Motion"
Cohesion: 0.12
Nodes (12): FrameRecord, valid_arrays(), write_frames_csv(), positions(), scope(), static_analysis(), track(), analyse() (+4 more)

### Community 13 - "OIS Clip Analysis"
Cohesion: 0.13
Nodes (15): _bandpass(), git_commit(), utc_now(), analyse(), _step_profile(), synthetic_sanity(), run(), _through_codec() (+7 more)

### Community 14 - "Android Probe Imports"
Cohesion: 0.13
Nodes (3): MainActivity, Runnable, ImageReader.OnImageAvailableListener

### Community 15 - "Target Pose & Impact"
Cohesion: 0.16
Nodes (11): bore_impact_mm(), rot_x(), rot_y(), rot_z(), target_rotation(), TargetPose, _bbox(), _jacobian() (+3 more)

### Community 16 - "Architecture Decisions"
Cohesion: 0.10
Nodes (18): SIGHTLINE Architecture, Progress tracker (~38% readiness), Technical debt list, Version 0.1.0 foundation release, CAL-EXP-1 Stabilisation detection (same as E-004a), E-007 Temporal fusion of N frames, SIGHTLINE README, Findings that changed the design (+10 more)

### Community 17 - "Camera Model"
Cohesion: 0.16
Nodes (4): CameraModel, test_focal_length_from_hfov(), test_pose_from_aim_places_the_bore_ray_on_the_requested_impact(), test_projection_roundtrip_with_distortion()

### Community 18 - "Mission 2 Research"
Cohesion: 0.13
Nodes (23): Alignment Trainer (simulated visual alignment and hold-training interface), E-006 Screen-sight geometry and eye position, Main camera ≈3.46 mm/px at 10 m (4K), Angular vs parallel sight-alignment error (E ≈ δ·D/r), AVCaptureVideoStabilizationMode.off (undocumented OIS effect), iPhone 15 vs Android Camera2 capability matrix, SIGHTLINE Mission 2 Research Report (camera stabilisation, localisation limits, sight geometry, licensing), Google Pixel Fused Video Stabilization (+15 more)

### Community 19 - "G1 CAD Tests"
Cohesion: 0.13
Nodes (15): test_active_sight_geometry(), test_collision_matrix(), test_deterministic_geometry(), test_front_sight_travel(), test_grip_is_sculpted(), test_manifest_matches_files(), test_mirrored_grip(), test_no_bore_or_muzzle() (+7 more)

### Community 21 - "Capture Templates"
Cohesion: 0.15
Nodes (13): finalise(), _measured_ok(), new_capture_template(), validate_capture(), evidence_class(), _filled(), test_derived_data_is_experimental_only_if_all_parents_are(), test_incomplete_or_implausible_manifests_are_rejected() (+5 more)

### Community 22 - "Capture Manifest CLI"
Cohesion: 0.20
Nodes (10): check_against_video(), load_capture(), main(), focal_length_px(), frame_columns(), analyse(), main(), table() (+2 more)

### Community 23 - "Grip Requirements"
Cohesion: 0.13
Nodes (20): Capture Manifests (TEAM_COLLECTED), ml.datasets.capture CLI, CAD Gate after Mission 2, Grip Freeze List, ISSF 1500 g Air-Pistol Mass Limit, Passive Training Grip Requirements, Prototype Path G0-G3, CAL-EXP-1 Stabilisation vs Body Motion (+12 more)

### Community 24 - "Dataset Provenance"
Cohesion: 0.17
Nodes (11): make_record(), read_jsonl(), sha256_bytes(), sha256_file(), validate_record(), write_jsonl(), emit(), test_invalid_records_are_rejected() (+3 more)

### Community 25 - "ISSF Scoring"
Cohesion: 0.18
Nodes (9): decimal_score(), decimal_score_tenths(), integer_score(), integer_score_from_rings(), is_inner_ten(), score_shot(), ShotScore, _validate_distance() (+1 more)

### Community 26 - "Gyro Log Loading"
Cohesion: 0.19
Nodes (9): GyroLog, load_gyro_csv(), _pick_axis(), sampling_report(), static_report(), CAL-EXP-6 Gyroscope Characterisation, analyse(), main() (+1 more)

### Community 27 - "Android Runnables"
Cohesion: 0.14
Nodes (6): Runnable, Runnable, Runnable, Runnable, Runnable, Runnable

### Community 28 - "Video I/O"
Cohesion: 0.20
Nodes (7): _ffprobe(), iter_frames(), presentation_timestamps(), probe_video(), _ratio(), expected_table(), main()

### Community 29 - "Dataset Spec"
Cohesion: 0.13
Nodes (14): Experiment lifecycle and status vocabulary, Capture manifest for physical recordings, Data categories (EXTERNAL, TEAM_COLLECTED, SYNTHETIC, DERIVED, MODEL_OUTPUT, SIMULATION_OUTPUT), Dataset Specification, Sample record schema, Team-collected capture protocol, External Dataset Survey, Rules for adding an external dataset (+6 more)

### Community 30 - "G1 Assembly Config"
Cohesion: 0.15
Nodes (12): Assembly, build(), frames(), load_config(), load_profile(), Ry(), T(), camera_keepouts() (+4 more)

### Community 31 - "E-004a Harness"
Cohesion: 0.16
Nodes (12): classify(), compare(), _conditions(), _steps(), _summary(), test_classification_uses_uncertainty(), test_comparison_reading_follows_the_stated_rules_and_is_scoped(), test_comparison_refuses_runs_that_are_not_complete() (+4 more)

### Community 32 - "G1 CAD Checks"
Cohesion: 0.26
Nodes (12): _bb(), common(), empty_regions(), interferences(), markdown(), moving_checks(), _overlap(), run_all() (+4 more)

### Community 33 - "Allan Deviation"
Cohesion: 0.22
Nodes (10): allan_deviation(), allan_summary(), dominant_axis(), _static_log(), test_allan_minimum_detects_a_bias_instability_floor(), test_dominant_axis_and_sign(), test_load_infers_columns_units_and_reports_the_mapping(), test_load_rejects_what_it_cannot_interpret() (+2 more)

### Community 34 - "G1 Renders"
Cohesion: 0.19
Nodes (6): sight_geometry(), _label(), _mesh(), render_all(), Scene, sight_dims()

### Community 35 - "Temporal Reconstruction Research"
Cohesion: 0.16
Nodes (11): CLASSICAL Arm, Wronski et al. 2019 Handheld Multi-frame Super-Resolution, AMD FidelityFX / FSR SDK Analysis, FidelityFX Licence Analysis (MIT list vs binary-only default), FSR Frame Generation, FSR 1 Spatial EASU/RCAS, FSR 2/3 Temporal Upscaler, FSR 4 ML Upscaler (+3 more)

### Community 36 - "Analytics Requirements"
Cohesion: 0.23
Nodes (3): CameraDevice.StateCallback, CameraCaptureSession.StateCallback, CameraCaptureSession.CaptureCallback

### Community 37 - "Camera2 Callbacks"
Cohesion: 0.14
Nodes (14): app/analytics README (hold and trigger analytics), Planned hold/trigger metrics (time in zone, trace speed, displacement), ANA-01 Deterministic hold/trigger metrics, ANA-02 No AI coaching until metrics validated, CAL-01 Scoring independent of intrinsics, Requirements, MEA-02 Integer-score agreement ≥ 99%, MEA-03 Systematic bias ≤ 0.1 mm (+6 more)

### Community 38 - "Mobile App Platform"
Cohesion: 0.15
Nodes (13): build_apk.sh (no Gradle), Android Camera2 probe app README, Android-first Camera2 platform proposal, app/mobile README (phone application), Shared measurement core port (C++ or Kotlin MP), APPLY: Mission 2 branch substitution files, Branch mission-2-experimental-validation, SightLine_mission-2 git bundle (+5 more)

### Community 39 - "Pellet Ballistics"
Cohesion: 0.20
Nodes (8): drop_relative_to_zeroed_sight_line_mm(), free_fall_drop_mm(), speed_for_drop_mps(), time_of_flight_s(), test_concept_claim_of_2_mm_drop_is_not_plausible(), test_free_fall_drop_at_160_mps(), test_invalid_inputs(), test_net_drop_is_zero_at_the_zero_distance_and_negligible_within_range_tolerance()

### Community 40 - "BLE Trigger & IMU"
Cohesion: 0.19
Nodes (14): BLE HID Option (Rejected), BLE Trigger (input device only), NTP-style Clock Synchronisation over GATT, Custom GATT Service with Notifications (Option B), BLE Trigger and IMU Requirements, EXP-HW-1 LED-in-Frame Latency Experiment, Optional Grip IMU, HW-02 Trigger Timing <= 5 ms (+6 more)

### Community 41 - "Coordinate Frames"
Cohesion: 0.15
Nodes (12): Bore Pixel p_b / Simulated Bore Axis, Coordinate Systems and Sight Geometry, Camera Frame C, Device Frame D, Grip Frame G, Image Frame I, Screen Frame S, Target Frame T (+4 more)

### Community 42 - "Multi-device Calibration"
Cohesion: 0.19
Nodes (14): Bore Pixel p_b, CAL-EXP-2 Camera-IMU Time Offset, CAL-EXP-3 BLE Trigger Latency, CAL-EXP-4 Print-Scale Tolerance, CAL-EXP-5 Focus Breathing, Multi-device Calibration Strategy, Per-Device Calibration Profile Schema, Gyro-Camera Self-Calibration (Karpenko et al. 2011) (+6 more)

### Community 43 - "Reconstruction Gates"
Cohesion: 0.19
Nodes (14): Cramér–Rao Lower Bound (CRLB), Computational Reconstruction Research Plan, Gate G2 CRLB Gap Known, Gate G3 Temporal Arm, Gate G4 ML Justification, Gate G5 On-Device Cost, HYBRID Arm, ML Arm (+6 more)

### Community 44 - "Baseline Estimators E-001"
Cohesion: 0.21
Nodes (13): Gate G1 Baseline Characterised, RAW Arm, E1 Target-Centre Localisation, ml/configs README, E-001 Single-Frame Localisation Experiment, Camera Presets (wide_1080p, wide_2160p, wide_12mp, tele3x_1080p), E-001 Results Summary, Edge-Ellipse Estimator (+5 more)

### Community 45 - "AMD-NR / DLSS Licensing"
Cohesion: 0.23
Nodes (12): AMDNR Neural Rendering Mod, AMDNR Launcher, Device-Tiered Hash-Pinned Model Packs, NVIDIA DLSS Neural Rendering Model, AMD-NR / OptiScaler Analysis, GPL-3.0 Licence, Hartley 1997 Rotating-Camera Self-Calibration, Karpenko et al. 2011 Gyro-based Stabilisation (+4 more)

### Community 46 - "Sources & Licences"
Cohesion: 0.24
Nodes (11): GOV-01 No third-party code without verified licence, AMD-NR---OptiScaler (S-12), Sources and Licences Ledger, ffprobe/ffmpeg external tool, AMD FidelityFX SDK (S-11), NumPy dependency, OpenCV dependency, S-01 ISSF Rule Book 2026 General Technical Rules (+3 more)

### Community 47 - "Research Log"
Cohesion: 0.21
Nodes (10): Research literature notes, AMD-NR / OptiScaler, Pellet ballistic drop, R-000 Existing SIGHTLINE repository, R-002 Concept document 0.891 degree claim, R-003 Pellet drop at 10 m claim, R-004 AMD-NR / OptiScaler, R-011 Licences of the Python toolchain (+2 more)

### Community 48 - "Project Spec"
Cohesion: 0.20
Nodes (11): D-019 Vision + gyroscope measurement split (PROPOSED), SIGHTLINE training instrument, System pipeline (camera→capture→vision→calibration→scoring→UI), Core thesis: does computational reconstruction improve smartphone measurements, SIGHTLINE Project Specification, MVP: detection + calibration + sight geometry + shot geometry + scoring, Not 'DLSS for shooting' (internal analogy only), Principal risks (stabilisation, trigger timing, ISP, imitation-firearm law) (+3 more)

### Community 49 - "Error Budget"
Cohesion: 0.20
Nodes (9): CAL-EXP-4 Print Measurement, CAL-EXP-5 Focus, Measurement Error Budget, E10 Motion Blur, E12 Print Scale and Distance, E2 Scale from the Black, E3 Weak-Perspective Model Error, E4 Lens Distortion (+1 more)

### Community 51 - "ML Gate & Model Card"
Cohesion: 0.24
Nodes (9): Reconstruction research gates G1-G5 (RAW→CLASSICAL→TEMPORAL→ML→HYBRID), E-001 Single-frame localisation and scoring error (SIMULATED), E-005 Theoretical localisation limit (Cramér–Rao bound), ML gate closed, Model Card, MEA-01 Image-term impact error p95 ≤ 0.4 mm (EST-grade), C-037 ML improves on baseline (UNVERIFIED), C-055 Cramér–Rao bound 0.012–0.235 mm RMS (+1 more)

### Community 52 - "Target Geometry Docs"
Cohesion: 0.29
Nodes (8): Fit-to-FOV Unity Magnification, Black Aiming Mark (59.5 mm), Decimal Scoring Model (0.8 mm step), Target Geometry, Angular Sizes and Scoring, EST-Grade Accuracy Target 0.4 mm (MEA-01), ISSF 10 m Air Pistol Target, Pellet Drop Analysis, Pixel Budget at 10 m

### Community 53 - "E-001 Experiment Script"
Cohesion: 0.36
Nodes (6): _cell_seed(), _degradation(), main(), run(), summarise(), to_markdown()

### Community 54 - "Print Target Script"
Cohesion: 0.31
Nodes (7): build_pdf(), _circle(), content(), _line(), main(), _text(), Scripts index

### Community 55 - "Scoring Tests"
Cohesion: 0.22
Nodes (6): test_decimal_score_boundaries_touching_scores_higher(), test_inner_ten(), test_invalid_distance_rejected(), test_ring_pitch_is_exactly_8_mm_everywhere(), test_score_shot(), test_scoring_zone_radii()

### Community 56 - "Display Geometry"
Cohesion: 0.28
Nodes (4): on_screen_size_mm(), target_anchored_scale(), unity_magnification_scale(), test_unity_magnification_and_target_anchored_scale_agree()

### Community 57 - "CAD Export Manifest"
Cohesion: 0.22
Nodes (8): components, configurations, files, generator, note, parameters, parameters_sha256, source_commit

### Community 58 - "Baseline Vision Pipeline"
Cohesion: 0.36
Nodes (8): Target-Anchored Scale, Deterministic Baseline Vision Pipeline, Black Aiming Mark (59.5 mm), Experiment E-001 Characterisation, Edge Refinement and Direct Ellipse Fit (Fitzgibbon / Halir-Flusser), Moments / Edges / Hybrid Estimators, Moments Refinement, Rectification to Target mm (rectify.py)

### Community 59 - "Test Target SL-T1"
Cohesion: 0.22
Nodes (9): Black aiming disc nominal 59.5 mm, 170 mm card corner marks, 100 mm / 150 mm print-scale verification bars, SIGHTLINE test target SL-T1-A4, Decimal scoring, ISSF 10 m air-pistol target geometry, ISSF Pistol Rules 2026 (S-02), ISSF Rule Book 2026 (S-01) (+1 more)

### Community 60 - "Data Folders"
Cohesion: 0.25
Nodes (8): data/interim (DERIVED intermediates), Provenance Manifests, sample_record.schema.json, synthetic_v0.1.0.jsonl Manifest, data/processed (frozen splits), data/raw (immutable raw captures), Synthetic Dataset v0.1.0 (13 samples), E-003 Synthetic-to-Real Domain Gap

### Community 61 - "Camera Stabilisation APIs"
Cohesion: 0.36
Nodes (7): Android Camera2 API (S-03), Apple AVFoundation (S-04), Requirement CAM-01, Electronic image stabilisation (EIS), OisSample per-frame OIS data, Optical image stabilisation (OIS), R-006 Camera stabilisation, per-frame metadata and timestamps

### Community 62 - "Gyro Self-Calibration Lit"
Cohesion: 0.38
Nodes (5): AMD FidelityFX / FSR SDK, Karpenko et al., Stanford CTSR 2011-03 (S-07), R-005 AMD FidelityFX / FSR SDK, R-009 Reconstruction and calibration literature, Wronski et al., Handheld Multi-Frame Super-Resolution (S-06)

### Community 63 - "Mission 2 Research Refs"
Cohesion: 0.29
Nodes (5): Apache-2.0 licence plan (D-013), E-004a/b stabilisation experiment, SIGHTLINE Mission 2 research report, R-013 Mission 2 research report filed, R-014 Stabilisation experiment without laboratory equipment

### Community 64 - "Trigger Timing Prior Art"
Cohesion: 0.29
Nodes (7): Apple Technical Q&A QA1931 (S-05), BLE connection interval, Cleanness of triggering (DA, DA250), Mon-Lopez et al., PLOS ONE 2022 (S-08), R-007 Trigger timing: BLE connection intervals, R-008 Prior art: optoelectronic shooting trainers and hold metrics, SCATT optoelectronic trainer

### Community 65 - "ML Inference/Training Gate"
Cohesion: 0.33
Nodes (4): Least-Squares Blurred-Disc Model Fit, E11 ISP Non-linearity, ml/inference README, ml/training README

### Community 67 - "graphify Config"
Cohesion: 0.60
Nodes (4): Claude config: graphify skill, graphify knowledge-graph skill, CLAUDE.md graphify rules, graphify-out/graph.json

### Community 69 - "CAD Folder Docs"
Cohesion: 0.40
Nodes (5): cad/drawings README, cad/exports README, Parametric CAD (cad/parametric) as source of truth, CAD gate closed, iPhone 15 dimensional drawing and camera keep-outs

### Community 70 - "Rolling Shutter & OIS"
Cohesion: 0.40
Nodes (5): Observed-vs-Reported OIS Image Recorder (PLANNED), OIS Log (ON/OFF, 10 s), Android OIS Samples (Camera2), CAL-EXP-2 Rolling Shutter, E9 Rolling Shutter

### Community 71 - "External Datasets"
Cohesion: 0.50
Nodes (4): Roboflow KNSA dataset (S-14), R-010 External datasets, SIDD smartphone noise dataset (S-13), Synthetic reference set data/synthetic/v0.1.0

### Community 72 - "Angular Size"
Cohesion: 0.67
Nodes (3): angular_size_deg(), angular_size_rad(), test_angular_sizes_and_the_0891_degree_claim()

## Knowledge Gaps
- **96 isolated node(s):** `sightline`, `Claude config: graphify skill`, `cad/drawings README`, `cad/exports README`, `Progress tracker (~38% readiness)` (+91 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 380 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MainActivity` connect `Android Probe Imports` to `Analytics Requirements`, `Probe UI Buttons`, `Gyro Sensor Callbacks`, `Probe MainActivity`, `Android Runnables`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `CameraModel` (e.g. with `bore_impact_mm()` and `pose_from_aim()`) actually correct?**
  _`CameraModel` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sightline`, `Claude config: graphify skill`, `cad/drawings README` to the rest of the system?**
  _96 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Aiming Mark Measurement` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
- **Why does `E-004a iPhone 15 OIS Transfer Protocol` connect `Grip Requirements` to `Multi-device Calibration`, `Video I/O`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Should `Ellipse Fitting` be split into smaller, more focused modules?**
  _Cohesion score 0.09619450317124736 - nodes in this community are weakly interconnected._
- **Why does `Research Log` connect `Research Log` to `Trigger Timing Prior Art`, `External Datasets`, `Test Target SL-T1`, `Camera Stabilisation APIs`, `Gyro Self-Calibration Lit`, `Mission 2 Research Refs`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._