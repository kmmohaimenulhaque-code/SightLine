# Feasibility Study

This feasibility study addresses key mechanical and architectural challenges for the SIGHTLINE project.

## 1. Modular Architecture Evaluation

We evaluate three adapter alternatives for mounting different phones to the chassis:

| Option | Description | Print Cost | Part Count | Phone-Change Time | Compatibility | Rigidity | Calibration Repeatability | Wear |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **(a)** | Fully adjustable cradle with hard adjustable datum stops | High | High | Slow | Very High | Low | Low | High |
| **(b)** | Common adjustable cradle + phone-specific locator inserts | Medium | Medium | Medium | High | Medium/High | High | Low/Medium |
| **(c)** | Common chassis accepting separate phone-specific cradle modules | Low (per phone), High (total) | Low | Fast | High | High | Very High | Low |

**Recommendation:** Option (b) is recommended as the best hybrid approach. It minimizes large structural prints while maintaining rigid, phone-specific datum engagement for repeatability.

## 2. Mass Tuning Feasibility
Achieving the target mass and Center of Mass (COM) requires adjustable ballast:
- **X-axis (Longitudinal):** A single 120mm ballast rail loaded with 100-200g of steel washers can shift the COM by approximately ±25mm longitudinally.
- **Z-axis (Vertical):** Providing indexed weight positions at 3 different heights allows for approximately ±15mm of vertical COM shift.

## 3. FDM Printability
- **Locating Pins:** 3-2-1 locating principles using 3mm diameter pins are subject to standard FDM tolerances of approximately ±0.15mm.
- **Recommendation:**
  - For **G0** prototyping, printed pins are acceptable with manual reaming/post-processing.
  - For **G2/G3** production, steel dowel pins pressed into the printed chassis are required to achieve the necessary repeatability.

## 4. Compatibility Levels
Phone compatibility is defined across three discrete levels:
- **Level 1 (Physical Fit):** The phone successfully fits into the cradle/adapter without interference.
- **Level 2 (Mechanical Seating):** The phone seats repeatably against the defined mechanical datums. Verified via indicator measurement.
- **Level 3 (Calibrated Optical Operation):** The observed bore-to-pixel mapping remains stable across reseating cycles. Verified via optical testing.

## 5. 0.05-Pixel Repeatability Assessment
The `GRIP_REQUIREMENTS.md` sets an aspirational target of 0.05-pixel repeatability.
- At a resolution scale of 3.45 mm/px (assuming a main camera at 2160p resolution targeting at 10m), a 0.05 px shift equates to a 0.17mm physical displacement on the target.
- To achieve this, the phone must reseat within approximately **0.03mm translational** and **0.003° angular** repeatability.
- **Conclusion:** This level of precision is potentially achievable with steel dowel pins and rigid chassis design, but is **NOT** achievable with printed plastic interfaces alone.
- We separate the evaluation into **Metric A (Mechanical Pose)** and **Metric B (Observed Optical)** to independently verify the mechanical interface and the optical outcome.
