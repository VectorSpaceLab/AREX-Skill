# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a cleanlab checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill before trusting it.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-09T23:26:59Z",
  "repository": {
    "name": "cleanlab",
    "remote_url": "https://github.com/cleanlab/cleanlab.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v2.9.0",
    "commit": "750625747de1b26d8530954f51f0530bd0b51d3c",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "cleanlab",
      "version": "2.9.0",
      "import_names": [
        "cleanlab"
      ]
    },
    {
      "name": "cleanvision",
      "version": "0.3.7",
      "import_names": [
        "cleanvision"
      ]
    },
    {
      "name": "datasets",
      "version": "5.0.1",
      "import_names": [
        "datasets"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "cleanlab",
      "cleanlab/datalab",
      "cleanlab/multilabel_classification",
      "cleanlab/object_detection",
      "cleanlab/regression",
      "cleanlab/segmentation",
      "cleanlab/token_classification",
      "cleanlab/experimental"
    ],
    "docs": [
      "README.md",
      "docs/source",
      "docs/source/tutorials",
      "docs/source/cleanlab"
    ],
    "tests": [
      "tests",
      "tests/datalab"
    ],
    "metadata": [
      "pyproject.toml",
      "setup.py",
      "setup.cfg",
      "requirements-dev.txt",
      "requirements-test-core.txt",
      ".pre-commit-config.yaml",
      ".mypy.ini"
    ],
    "scripts_and_tools": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the current working tree has source, docs, metadata, or test changes not represented here, refresh before relying on the guidance.
- If cleanlab package metadata, optional extras, public APIs, or major module layout change, refresh even when the commit is unchanged.
- The generated `skills/` output is not part of the upstream source baseline.
