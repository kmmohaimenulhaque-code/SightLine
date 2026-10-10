# Mechanical Tolerance Budget

This document outlines the tolerance budget and repeatability targets for the phone-to-chassis mechanical interface.

## Engineering Coordinate System
- **X:** Longitudinal, pointing toward the target (forward)
- **Y:** Lateral (left/right)
- **Z:** Vertical (up)
- **Handedness:** Right-handed coordinate system
- **Chassis Datum Origin:** The intersection of the adapter mating plane with the grip's longitudinal axis.

## Transformation Chain
The mechanical stack-up follows this transformation chain:
`PHONE BODY → PHONE ADAPTER → COMMON CHASSIS → GRIP DATUM`

## Interface Specifications

| Interface | Locating Method | Nominal Clearance | Expected FDM Tolerance | Steel Dowel Tolerance (G2/G3) | Resulting Translational Uncertainty (RSS) | Resulting Angular Uncertainty |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Phone to Adapter | Friction fit / hard stops | 0.10mm | ±0.15mm | N/A | ±0.18mm | ±0.1° |
| Adapter to Chassis | 3-2-1 Locating Pins | 0.05mm | ±0.15mm | ±0.02mm | ±0.05mm | ±0.02° |
| Chassis to Grip | Rigid bolted joint | 0.00mm | ±0.10mm | N/A | ±0.10mm | ±0.05° |

*(Note: Values above are illustrative estimates for the stack-up analysis)*

## Performance Metrics

### Metric A: Mechanical Pose Repeatability
- **Target:** ≤ 0.05mm translation, ≤ 0.01° rotation (G0 aspiration)
- **Method:** Dial indicator measurement against the phone body after 20 complete reseat cycles (remove and replace).
- *Note:* These values represent design aspirations and are not yet verified.

### Metric B: Observed Optical Repeatability
- **Target:** ≤ 0.05 px image displacement
- **Method:** Fixed camera and physical target setup. Perform 20 reseat cycles. Capture image after each cycle and perform sub-pixel image registration to determine displacement.
- *Note:* This metric relies on the optical system and cannot be proven by CAD analysis alone. It is the ultimate validation of the mechanical design.

## Stack-up Analysis
The total mechanical uncertainty (Metric A) is the Root Sum Square (RSS) of the individual interface uncertainties.
- **Translational (RSS):** `sqrt(0.18^2 + 0.05^2 + 0.10^2) ≈ 0.21mm` (FDM only). With steel dowels, the Adapter to Chassis interface improves, but the primary driver remains the Phone to Adapter interface. Achieving the 0.05mm target will require precise, tuned fits or active clamping mechanisms rather than passive clearance fits.
