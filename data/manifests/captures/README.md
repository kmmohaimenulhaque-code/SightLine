# data/manifests/captures

One validated manifest per physical clip or sensor log (category TEAM_COLLECTED). Empty until the first physical
experiment is run. Create with `python -m ml.datasets.capture new --experiment <id> --video <clip>`, fill in every
`null`, then `python -m ml.datasets.capture validate <file> --video <clip>`. Raw files are not committed.
