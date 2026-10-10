# Mass Reference Document

This document defines the mass and inertial targets for the SIGHTLINE grip, using the Steyr LP10 as the primary benchmark.

## Reference Model
- **Model:** Steyr LP10 (Standard mechanical trigger variant)
- **Manufacturer-reported mass:**
  - Steyr LP10 E: ~0.90 kg (empty), ~0.95 kg (with cylinder).
  - The standard LP10 with mechanical trigger is generally heavier.
  - *Note:* Published weights vary by source and specific configuration. Source reference: Steyr Sport official product specifications (when available).
- **Configuration assumptions:** Published mass values typically include the air cylinder, standard barrel weights, and the standard walnut grip panel.

## SIGHTLINE Targets
- **ISSF legal maximum:** 1500g (Pistol Rules 8.12, VERIFIED)
- **SIGHTLINE working band:** 0.95 - 1.20 kg (ASSUMED, adopted from `GRIP_REQUIREMENTS.md`)
- **Centre of mass (COM):** UNKNOWN — no published data exists for the reference model. Mark as PROVISIONAL/TBD.
- **Moment of inertia (MOI):** UNKNOWN — mark as TBD.

*Important Note:* Ergonomic inspiration, mass-property matching, and regulatory compliance are three separate concepts. SIGHTLINE aims to match the mass-properties of a target pistol while maintaining its own ergonomic identity and adhering to ISSF regulations.

## Target Parameter Model

| Parameter | Value | Status |
| :--- | :--- | :--- |
| `reference_id` | Steyr LP10 (Mech) | Defined |
| `reference_mass_g` | ~1000g | Estimated |
| `target_mass_g` | 950 - 1200g | Target Band |
| `target_com_x_mm` | TBD | Pending Measurement |
| `target_com_y_mm` | TBD | Pending Measurement |
| `target_com_z_mm` | TBD | Pending Measurement |
| `target_inertia_tensor` | TBD | Pending Measurement |
| `mass_tolerance_g` | TBD | Pending |
| `com_tolerance_mm` | TBD | Pending |
| `inertia_tolerance` | TBD | Pending |

*All COM and inertia values remain TBD until physical measurement of a reference pistol can be conducted.*
