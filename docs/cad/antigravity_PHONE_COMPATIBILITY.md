# Phone Compatibility Registry

This document defines the architecture for tracking phone compatibility and provides reference profiles.

## Phone Configuration Registry Architecture

- **Location:** `cad/parametric/phone_profiles/`
- **Format:** JSON (one file per phone model)
- **Required Fields:**
  - `id`: Unique identifier (e.g., `iphone_15`)
  - `model`: Human-readable name
  - `variant`: Specific variant (if applicable)
  - `body_dims_mm`: [X, Y, Z]
  - `body_dims_tolerance_mm`: [X, Y, Z]
  - `case_dims_mm`: (Optional)
  - `mass_g`: Float
  - `mass_source`: String
  - `mass_confidence`: High/Medium/Low
  - `camera_island_dims_mm`: [X, Y, Z]
  - `camera_island_protrusion_mm`: Float
  - `cameras`: Array of objects
    - `id`: Identifier
    - `type`: Main/Wide/Tele/etc.
    - `position_body_mm`: [X, Y, Z] relative to phone origin
    - `fov_deg`: Float
    - `aperture`: Float
  - `button_positions`: Array of bounding boxes
  - `connector_position`: Bounding box
  - `installed_orientation`: String/Enum
  - `adapter_id`: Reference to the required cradle insert
  - `adapter_to_chassis_transform`: 4x4 Matrix or Translation/Rotation arrays
  - `calibration_metadata`: Object
  - `data_provenance`: String
  - `measurement_confidence`: High/Medium/Low

## Reference Profiles

### 1. iPhone 15 (Initial Reference)
- **Body:** 147.6 × 71.6 × 7.80 mm (VERIFIED from Apple spec)
- **Mass:** 171g (VERIFIED from Apple spec)
- **Camera positions:** ESTIMATED from Apple dimensional drawing interpretation
- **Main camera:** Estimated position relative to phone body datum
- **Ultra Wide:** Estimated position relative to phone body datum
- *Note:* Which camera the grip must leave unobstructed depends on the outcome of the OIS experiment (E-004a).

### 2. Android Reference (Placeholder)
- **Body:** 160.0 × 75.0 × 8.5 mm (PLACEHOLDER)
- **Mass:** 190g (PLACEHOLDER)
- *All values marked UNVERIFIED.*
- This profile serves to demonstrate that a second phone can be supported via an adapter swap without requiring a full chassis redesign.

## Compatibility Levels

Compatibility is assessed at three levels:
1. **Physical fit:** The phone physically fits within the designated adapter/cradle.
2. **Mechanical seating:** The phone can be repeatably seated against the defined datums (verified mechanically).
3. **Calibrated optical:** The seated phone maintains a stable optical bore sight across reseat cycles (verified optically).
