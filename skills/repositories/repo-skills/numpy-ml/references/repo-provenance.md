# Repository Provenance

## Purpose

Read this before deciding whether this `numpy-ml` repo skill is current for a
checkout. If the current repo commit, source dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:20:49Z",
  "repository": {
    "name": "numpy-ml",
    "remote_url": "https://github.com/ddbourgin/numpy-ml.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b0359af5285fbf9699d64fd5ec059493228af03e",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "numpy-ml",
      "version": "0.1.2",
      "import_names": ["numpy_ml"]
    }
  ],
  "evidence": {
    "source_roots": [
      "numpy_ml/linear_models",
      "numpy_ml/trees",
      "numpy_ml/nonparametric",
      "numpy_ml/factorization",
      "numpy_ml/gmm",
      "numpy_ml/hmm",
      "numpy_ml/lda",
      "numpy_ml/ngram",
      "numpy_ml/neural_nets",
      "numpy_ml/preprocessing",
      "numpy_ml/utils",
      "numpy_ml/bandits",
      "numpy_ml/rl_models"
    ],
    "docs": ["README.md", "numpy_ml/README.md", "docs/"],
    "tests": ["numpy_ml/tests/"],
    "configs": ["setup.py", "requirements.txt", "requirements-dev.txt", "requirements-test.txt", "tox.ini"],
    "scripts": ["numpy_ml/plots/ (reference-only optional plotting demos)"]
  }
}
```

The checkout was otherwise clean at the source commit before generated skill
artifacts were written under `skills/`.

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If source files outside generated `skills/` output are dirty, run
  `refresh-repo-skill` before trusting API or compatibility details.
- If package metadata, public module exports, Python compatibility, or optional
  dependency behavior changed, run `refresh-repo-skill`.
