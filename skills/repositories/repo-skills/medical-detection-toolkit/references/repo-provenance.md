# Repository Provenance

Read this before deciding whether the runtime graph is current for a checkout.
If the commit, dirty paths, package metadata, or major evidence paths differ,
run a refresh rather than assuming the graph still matches.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "medicaldetectiontoolkit",
    "remote_url": "https://github.com/MIC-DKFZ/medicaldetectiontoolkit.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "6753237cc4bae558a94b919735d545a2de075e07",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "medicaldetectiontoolkit",
      "version": "0.0.1",
      "import_names": ["models", "utils", "predictor", "evaluator", "exec"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "utils", "cuda_functions", "top-level Python modules"],
    "docs": ["README.md"],
    "examples": ["experiments/toy_exp", "experiments/lidc_exp", "experiments/pet_ct_tnm_classification"],
    "tests": [],
    "configs": ["default_configs.py", "experiments/*/configs.py", "setup.py", "requirements.txt"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- If the checkout is dirty, compare relevant source changes separately from
  generated `skills/` output.
- Recheck `setup.py`, `requirements.txt`, `exec.py`, `models/`, `predictor.py`,
  `evaluator.py`, `utils/`, `experiments/`, and `cuda_functions/` before using
  this graph for a changed revision.
- The project README states that the framework is no longer maintained. A
  successor framework or a modernized fork should receive a separate skill or a
  deliberate refresh, not an implicit API substitution.
