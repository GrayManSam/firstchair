---
name: firstchair-check
description: Verify Firstchair CLI and workflow changes with local synthetic providers.
---

Run `PYTHONPATH=src python -m unittest discover -s tests -v` from the repository root.
Run `PYTHONPATH=src python -m firstchair doctor` to confirm CLI discovery.
Use temporary directories for workflow runs and verify persisted status with
`firstchair status`. Avoid invoking real provider accounts in routine checks.
