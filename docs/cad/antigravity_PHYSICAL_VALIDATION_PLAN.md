Physical validation tests (ALL PENDING until printed parts exist):

### PV-01: Phone fit and retention
- Insert phone into adapter 10 times
- Check: seats against all datum faces, no excessive force, camera unobstructed
- Pass: phone held securely with no rattle when inverted and shaken gently

### PV-02: Dimensional verification
- Measure 5 critical dimensions with digital calipers
- Compare to CAD nominal ± tolerance
- Record in cad/measurements/

### PV-03: Component mass
- Weigh each printed part on a 0.1g resolution scale
- Compare to CAD-estimated mass (volume × density)
- Record deviation

### PV-04: Assembled total mass
- Weigh complete assembly with phone and ballast
- Compare to solver prediction

### PV-05: Centre of mass measurement
- Balance-point method along X-axis: support on a rod, find equilibrium
- Balance-point method along Z-axis: suspend from two points
- Compare to solver COM prediction
- Record deviation

### PV-06: Ballast adjustment and locking
- Slide carriage through full travel — must be smooth, no binding
- Lock at 5 positions — verify no slip under 2g static load
- Verify no rattle at any position

### PV-07: Mechanical seating repeatability (Metric A)
- Remove and reinstall phone 20 times
- Measure pose using dial indicator or structured-light scan
- Report: mean, std dev, max displacement (mm and degrees)
- Target (aspiration): ≤ 0.05mm translation, ≤ 0.01° rotation

### PV-08: Optical seating repeatability (Metric B)
- Fixed camera, target at 10m, controlled lighting
- Remove and reinstall phone 20 times
- Capture image each time, measure target centre displacement
- Report: mean, std dev, p95, max displacement (pixels)
- Target (aspiration): ≤ 0.05 px
- Note: this test cannot pass on CAD alone

### PV-09: Structural integrity
- Hold assembled instrument in shooting position for 5 minutes
- Check for creep, looseness, or deformation
- Invert and shake — verify no parts dislodge

### PV-10: Adapter swap test
- Swap between two phone adapters 5 times
- Verify: correct pin engagement, no damage, adapter-specific phone fits correctly
- Run solver for each phone — verify different COM predictions

All results: PENDING. Do not claim any test has passed until measurements exist.
