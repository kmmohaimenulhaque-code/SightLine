# data/manifests

Provenance manifests: one JSON Lines file per dataset version, one record per sample. Schema:
`schema/sample_record.schema.json`; enforced by `ml/datasets/provenance.py`; specified in `DATASET_SPEC.md` §2.

| Manifest | Category | Samples | Produced by |
|---|---|---|---|
| `synthetic_v0.1.0.jsonl` | SYNTHETIC | 13 | `scripts/generate_synthetic_samples.py` |
| `captures/<capture_id>.json` | TEAM_COLLECTED | none yet | `python -m ml.datasets.capture new …` then filled in by the operator (`DATASET_SPEC.md` §2a) |
