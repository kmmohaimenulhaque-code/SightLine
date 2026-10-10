How to use the mass-balance system:
1. Weigh the printed chassis, adapter, and grip handle individually
2. Record masses in cad/measurements/ templates
3. Update component masses in the solver script
4. Select target mass and COM from MASS_REFERENCE.md (Steyr LP10: ~1060g, COM TBD)
5. Run solver: `python scripts/antigravity_cad_mass_properties.py --phone <profile> --target-mass 1060 --target-com-x 50 --target-com-z 15`
6. Solver reports optimal ballast positions and residual error
7. Set X-axis carriage to the reported position using the printed scale
8. Lock with thumb screw
9. For Z-axis: install weight cassette at the indexed position closest to the solver's recommendation
10. Verify total mass with a kitchen scale (±1g)
11. Verify COM by balance-point method: support the instrument on a thin rod and find the balance point along X and Z
12. Record results in cad/measurements/antigravity_balance_measurements.csv
