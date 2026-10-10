# CAD Gate Audit

This document provides a thorough audit of the 15-item freeze list originally defined in `docs/cad/GRIP_REQUIREMENTS.md`.

## Freeze List Audit Table

| Requirement ID | Requirement Meaning | Current Status | Evidence Available | Missing Measurement/Decision | Blocks G0/G1/G2/G3? | Minimum Action to Resolve |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| FL-01 | Phone model(s) | OPEN | N/A | Exact phone model(s) to support | G0: No, G1: Yes | Select reference phone |
| FL-02 | Phone dimensions | OPEN | N/A | Dimensional data for selected phone | G0: No, G1: Yes | Obtain dimensions for selected phone |
| FL-03 | Camera position on phone | OPEN | N/A | Camera coordinates relative to phone body | G0: No, G1: Yes | Measure/source camera positions |
| FL-04 | Sight-axis geometry | Concept defined (D-002) | D-002 document | Final offset values | G0: No, G1: No, G2: Yes | Determine final offset dimensions |
| FL-05 | Grip angle | OPEN | N/A | Target grip angle for the chassis | G0: No, G1: Yes | Select/measure reference grip angle |
| FL-06 | Target geometry | VERIFIED | ISSF GTR 6.3.4.6 | None | No | None |
| FL-07 | Total mass target | VERIFIED (limit) / ASSUMED (band) | ISSF Rules (1500g max) | Exact target mass within 0.95-1.20 kg band | G0: No, G1: No, G2: Yes | Define final mass target |
| FL-08 | Centre-of-mass target | OPEN | Formula documented | X, Y, Z coordinates for target COM | G0: No, G1: No, G2: Yes | Determine target COM |
| FL-09 | Printer/material | OPEN | N/A | Final material selection (PETG/PLA+ assumed) | G0: No, G1: No, G2: Yes | Select print material |
| FL-10 | Fasteners | OPEN | N/A | Final fastener BOM (heat-set inserts assumed) | G0: No, G1: No, G2: Yes | Define fastener standards |
| FL-11 | BLE trigger position | OPEN | N/A | Physical location for BLE trigger | G0: No, G1: No, G2: Yes | Determine trigger placement |
| FL-12 | IMU position | OPEN | N/A | Physical location for IMU | G0: No, G1: No, G2: Yes | Determine IMU placement |
| FL-13 | Calibration references | Proposal | N/A | Defined physical reference surfaces | G0: No, G1: No, G2: Yes | Define datum surfaces on CAD |
| FL-14 | Adjustable parameters | Proposal | N/A | Final list of adjustable mechanisms | G0: No, G1: No, G2: Yes | Finalize adjustability requirements |
| FL-15 | Manufacturing tolerances | OPEN | N/A | Defined tolerance budget | G0: No, G1: No, G2: Yes | Complete tolerance stack-up analysis |

## IMPORTANT GATE CORRECTION
The OIS experiment (E-004a) is highly relevant to the final measurement architecture. However, it **does NOT block G0 mechanical prototyping**. G0 is focused on testing physical fit, retention, repeatable seating, and gross mechanical alignment. The final camera and IMU architecture remains conditional on experimental evidence, but that must not prevent implementing a mechanically useful prototype for evaluation.

## Verdict
**CAD Gate is OPEN for G0 and G1.** G2 and G3 remain blocked pending physical testing and finalization of open requirements.
