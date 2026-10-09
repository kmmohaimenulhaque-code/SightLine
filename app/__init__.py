"""SIGHTLINE platform-independent reference implementation (Python).

This package is the numerical ground truth for the mobile ports (ARCHITECTURE.md D-001).
Sub-packages:

* ``app.scoring``     — ISSF target geometry, scoring, pellet-drop arithmetic.
* ``app.calibration`` — camera model, target pose, rectification, display (unity magnification).
* ``app.vision``      — aiming-mark detection and sub-pixel measurement.
* ``app.analytics``   — time-series analysis of tracked positions; hold/trigger metrics (Phase 8) not started.
* ``app.imu``         — raw gyroscope log loading and characterisation (no fusion).
"""

__version__ = "0.2.0"
