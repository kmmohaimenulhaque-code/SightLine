# E-004a — synthetic sanity check of the analysis harness

**SYNTHETIC SANITY CHECK - software verification on simulated frames. NOT a measurement of any phone and NOT experimental evidence.**

Experiment status: **PHYSICAL_DATA_REQUIRED**. Evidence class of this file: **SIMULATED**. Codec path: libx264 crf 18. Seed 20261006.

The "hypotheses" are invented stabiliser behaviours injected into simulated frames. They exist only to check that the harness reports what was injected. They are not models of an iPhone.

| Camera scale | Test | Injected behaviour | Quantity | Injected | Recovered | Tolerance | Harness check |
|---|---|---|---|---|---|---|---|
| main_scale | A_static | none | RMS (px) | 0.000 | 0.008 | — | ok |
| main_scale | B_step | none | settled ratio @ 0.10 mrad (0.29 px) | 1.000 | 1.021 | ±0.207 | ok |
| main_scale | B_step | none | settled ratio @ 0.25 mrad (0.72 px) | 1.000 | 0.970 | ±0.083 | ok |
| main_scale | B_step | none | settled ratio @ 0.50 mrad (1.45 px) | 1.000 | 0.994 | ±0.050 | ok |
| main_scale | B_step | none | settled ratio @ 1.00 mrad (2.89 px) | 1.000 | 0.992 | ±0.050 | ok |
| main_scale | B_step | none | settled ratio @ 2.00 mrad (5.79 px) | 1.000 | 0.995 | ±0.050 | ok |
| main_scale | B_step | lock | settled ratio @ 0.10 mrad (0.29 px) | 0.300 | 0.327 | ±0.207 | ok |
| main_scale | B_step | lock | settled ratio @ 0.25 mrad (0.72 px) | 0.300 | 0.318 | ±0.083 | ok |
| main_scale | B_step | lock | settled ratio @ 0.50 mrad (1.45 px) | 0.300 | 0.305 | ±0.050 | ok |
| main_scale | B_step | lock | settled ratio @ 1.00 mrad (2.89 px) | 0.300 | 0.299 | ±0.050 | ok |
| main_scale | B_step | lock | settled ratio @ 2.00 mrad (5.79 px) | 0.300 | 0.299 | ±0.050 | ok |
| main_scale | B_step | recentring | settled ratio @ 0.10 mrad (0.29 px) | 1.000 | 1.007 | ±0.207 | ok |
| main_scale | B_step | recentring | settled ratio @ 0.25 mrad (0.72 px) | 1.000 | 0.920 | ±0.083 | ok |
| main_scale | B_step | recentring | settled ratio @ 0.50 mrad (1.45 px) | 1.000 | 0.966 | ±0.050 | ok |
| main_scale | B_step | recentring | settled ratio @ 1.00 mrad (2.89 px) | 1.000 | 0.994 | ±0.050 | ok |
| main_scale | B_step | recentring | settled ratio @ 2.00 mrad (5.79 px) | 1.000 | 0.990 | ±0.050 | ok |
| main_scale | D_oscillation | none | gain 0.5-2 Hz | 1.000 | 0.996 | ±0.070 | ok |
| main_scale | D_oscillation | none | gain 2-5 Hz | 1.000 | 0.998 | ±0.070 | ok |
| main_scale | D_oscillation | none | gain 5-10 Hz | 1.000 | 1.008 | ±0.070 | ok |
| main_scale | D_oscillation | lock | gain 0.5-2 Hz | 0.300 | 0.299 | ±0.070 | ok |
| main_scale | D_oscillation | lock | gain 2-5 Hz | 0.300 | 0.296 | ±0.070 | ok |
| main_scale | D_oscillation | lock | gain 5-10 Hz | 0.300 | 0.281 | ±0.070 | ok |
| uw_scale | A_static | none | RMS (px) | 0.000 | 0.011 | — | ok |
| uw_scale | B_step | none | settled ratio @ 0.10 mrad (0.15 px) | 1.000 | 0.899 | ±0.413 | ok |
| uw_scale | B_step | none | settled ratio @ 0.25 mrad (0.36 px) | 1.000 | 0.959 | ±0.165 | ok |
| uw_scale | B_step | none | settled ratio @ 0.50 mrad (0.73 px) | 1.000 | 1.011 | ±0.083 | ok |
| uw_scale | B_step | none | settled ratio @ 1.00 mrad (1.45 px) | 1.000 | 0.992 | ±0.050 | ok |
| uw_scale | B_step | none | settled ratio @ 2.00 mrad (2.90 px) | 1.000 | 0.995 | ±0.050 | ok |
| uw_scale | B_step | lock | settled ratio @ 0.10 mrad (0.15 px) | 0.300 | 0.294 | ±0.413 | ok |
| uw_scale | B_step | lock | settled ratio @ 0.25 mrad (0.36 px) | 0.300 | 0.280 | ±0.165 | ok |
| uw_scale | B_step | lock | settled ratio @ 0.50 mrad (0.73 px) | 0.300 | 0.280 | ±0.083 | ok |
| uw_scale | B_step | lock | settled ratio @ 1.00 mrad (1.45 px) | 0.300 | 0.293 | ±0.050 | ok |
| uw_scale | B_step | lock | settled ratio @ 2.00 mrad (2.90 px) | 0.300 | 0.305 | ±0.050 | ok |
| uw_scale | B_step | recentring | settled ratio @ 0.10 mrad (0.15 px) | 1.000 | 1.032 | ±0.413 | ok |
| uw_scale | B_step | recentring | settled ratio @ 0.25 mrad (0.36 px) | 1.000 | 0.890 | ±0.165 | ok |
| uw_scale | B_step | recentring | settled ratio @ 0.50 mrad (0.73 px) | 1.000 | 0.933 | ±0.083 | ok |
| uw_scale | B_step | recentring | settled ratio @ 1.00 mrad (1.45 px) | 1.000 | 0.971 | ±0.050 | ok |
| uw_scale | B_step | recentring | settled ratio @ 2.00 mrad (2.90 px) | 1.000 | 0.988 | ±0.050 | ok |
| uw_scale | D_oscillation | none | gain 0.5-2 Hz | 1.000 | 0.998 | ±0.070 | ok |
| uw_scale | D_oscillation | none | gain 2-5 Hz | 1.000 | 0.996 | ±0.070 | ok |
| uw_scale | D_oscillation | none | gain 5-10 Hz | 1.000 | 0.995 | ±0.070 | ok |
| uw_scale | D_oscillation | lock | gain 0.5-2 Hz | 0.300 | 0.292 | ±0.070 | ok |
| uw_scale | D_oscillation | lock | gain 2-5 Hz | 0.300 | 0.285 | ±0.070 | ok |
| uw_scale | D_oscillation | lock | gain 5-10 Hz | 0.300 | 0.266 | ±0.070 | ok |
