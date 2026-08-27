# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Fairlearn checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:38:27Z",
  "repository": {
    "name": "fairlearn",
    "remote_url": "https://github.com/fairlearn/fairlearn.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "03e8e15546b90ea7afcab414575a29f2ff7f3c92",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "fairlearn",
      "version": "0.15.0.dev0",
      "import_names": ["fairlearn"]
    }
  ],
  "evidence": {
    "source_roots": ["fairlearn"],
    "docs": [
      "README.rst",
      "docs/quickstart.rst",
      "docs/faq.rst",
      "docs/user_guide/fairness_in_machine_learning.rst",
      "docs/user_guide/assessment",
      "docs/user_guide/mitigation",
      "docs/user_guide/datasets",
      "docs/user_guide/installation_and_version_guide"
    ],
    "examples": [
      "examples/plot_quickstart.py",
      "examples/plot_roc_auc.py",
      "examples/plot_correlationremover_before_after.py",
      "examples/plot_grid_search_census.py",
      "examples/plot_mitigation_pipeline.py",
      "examples/plot_adversarial_basics.py",
      "examples/plot_adversarial_fine_tuning.py"
    ],
    "tests": [
      "test/unit/metrics",
      "test/unit/preprocessing",
      "test/unit/reductions",
      "test/unit/postprocessing",
      "test/unit/adversarial",
      "test/unit/datasets/test_datasets.py",
      "test/install/test_no_ml.py",
      "test/install/test_no_matplotlib.py",
      "test/unit/test_show_versions.py"
    ],
    "configs": [
      "pyproject.toml",
      "requirements-dev.txt",
      "requirements-min.txt"
    ],
    "scripts": [
      "scripts"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If the current working tree is dirty and this snapshot was clean, or if the dirty paths differ from `dirty_paths`, refresh it.
- If package metadata, loader signatures, or public APIs change even on the same commit, refresh it.
