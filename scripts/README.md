# scripts

| Script | Purpose |
|---|---|
| `generate_synthetic_samples.py` | Regenerate the committed synthetic reference set `data/synthetic/v0.1.0/` and its manifest |
| `make_print_target.py` | Write the true-scale printable test target `docs/experiments/print/SIGHTLINE_target_SL-T1_A4.pdf` |

Experiments are run as modules, e.g. `python -m ml.evaluation.e001_localisation_budget` (see `EXPERIMENT_LOG.md`).
