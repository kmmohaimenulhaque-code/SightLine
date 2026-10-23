# G1 CAD checks — G1-AND163-RH (placeholder-android-163x76, right hand)

Automated, no hardware. PASS = the CAD model satisfies the rule; it is **not** a physical test.

| Check | Status | Detail |
|---|---|---|
| solids_valid | PASS | 78 parts; invalid: none |
| collision_matrix | PASS | 159 pairs tested (bounding boxes overlap); 0 interferences |
| camera_keepout | PASS | 2 keep-out solids; 0 hits |
| sight_line_clear | PASS | 0 parts in the sight corridor |
| active_sights | PASS | radius 218.25 mm; height 20.0 mm; rear elev ±1.0 mm, wind ±1.5 mm; front shim [0.0, 2.0] mm |
| transform_chain | PASS | phone centroid error 0.0 mm |
| phone_orientation | PASS | long axis [0.0, 1.0, 0.0], screen [-1.0, -0.0, -0.0], camera [1.0, 0.0, 0.0]; 34.0 mm above the sight line |
| printability | PASS | bed 256.0 mm; too large: none |
| moving_interfaces_summary | PASS |  |
| solver_cad_consistency | PASS |  |
| moving: phone_angle_positions | PASS | 3 cases |

Summary: 10 PASS · 0 FAIL · runtime 76.5 s
