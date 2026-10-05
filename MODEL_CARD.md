# Model Card

**No machine-learning model exists in SIGHTLINE (version 0.1.0).** This is deliberate (ARCHITECTURE.md D-008): the
deterministic baseline must be characterised first, and a model must pass the gates in
`docs/ml/RECONSTRUCTION_RESEARCH_PLAN.md` §4 before it is added.

When a model is added, this file is completed for it:

| Field | Content |
|---|---|
| Model id / version | |
| Task | e.g. sub-pixel aiming-mark centre regression from an ROI |
| Architecture and size | parameters, FLOPs, input resolution |
| Training data | manifest ids and categories (SYNTHETIC / TEAM_COLLECTED / EXTERNAL), sizes, licences |
| Evaluation data | held-out device/session; synthetic seeds |
| Metrics | impact error (RMS, p95, bias), score agreement, detection rate — versus the deterministic baseline and the CRLB |
| Conditions where it helps / hurts | per preset and degradation |
| Known failure modes | |
| On-device cost | latency, memory, model size, energy per frame on named devices |
| Compute used for training | GPU, hours, cost (EXPERIMENT_LOG.md id) |
| Licence of weights and of any pretrained base | |
| Intended use / out-of-scope use | Training feedback only; not competition scoring |
