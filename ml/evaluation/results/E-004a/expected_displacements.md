# E-004a — expected image displacement for known rotations (DERIVED, not measured)

Δu = f_px · tan θ. The focal lengths below are **prior estimates** used only to plan the experiment (`ml/configs/e004a.json` states where each comes from). The analysis never uses them: it measures f_px from the printed target in each clip.

| Camera mode (prior f_px) | 0.1 mrad | 0.25 mrad | 0.5 mrad | 1 mrad | 2 mrad |
|---|---|---|---|---|---|
| iPhone 15 Main 1x, 2160p (2890 px, DERIVED from SECONDARY sensor data (Mission 2 research report Q1: 0.346 mrad/px); planning value only) | 0.29 px | 0.72 px | 1.45 px | 2.89 px | 5.78 px |
| iPhone 15 Main 1x, 1080p (1445 px, DERIVED (half of the 2160p prior); planning value only) | 0.14 px | 0.36 px | 0.72 px | 1.45 px | 2.89 px |
| iPhone 15 Ultra Wide, 2160p (1445 px, DERIVED (half the Main focal length; research report Q1); planning value only) | 0.14 px | 0.36 px | 0.72 px | 1.45 px | 2.89 px |
| iPhone 15 Main 2x, 2160p (5780 px, UNVERIFIED (assumes a native-pitch sensor crop; readout behaviour undocumented)) | 0.58 px | 1.45 px | 2.89 px | 5.78 px | 11.56 px |

Lever displacement needed, d = r · tan θ:

| Lever radius | 0.1 mrad | 0.25 mrad | 0.5 mrad | 1 mrad | 2 mrad |
|---|---|---|---|---|---|
| 300 mm | 0.030 mm | 0.075 mm | 0.150 mm | 0.300 mm | 0.600 mm |
| 400 mm | 0.040 mm | 0.100 mm | 0.200 mm | 0.400 mm | 0.800 mm |
| 500 mm | 0.050 mm | 0.125 mm | 0.250 mm | 0.500 mm | 1.000 mm |
| 1000 mm | 0.100 mm | 0.250 mm | 0.500 mm | 1.000 mm | 2.000 mm |

