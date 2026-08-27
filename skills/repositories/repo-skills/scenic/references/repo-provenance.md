# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Scenic. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:42:59Z",
  "repository": {
    "name": "scenic",
    "remote_url": "https://github.com/google-research/scenic.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a179cefc7fd0a48676c15aa45b31c469e0dfc07d",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "scenic",
      "version": "0.0.1",
      "import_names": [
        "scenic"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "scenic/common_lib",
      "scenic/dataset_lib",
      "scenic/model_lib",
      "scenic/train_lib",
      "scenic/projects",
      "scenic/app.py",
      "scenic/main.py"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md",
      "scenic/projects/README.md",
      "scenic/model_lib/README.md",
      "scenic/projects/*/README.md"
    ],
    "examples": [
      "scenic/common_lib/colabs/scenic_playground.ipynb",
      "project README commands and configs"
    ],
    "tests": [
      "scenic/common_lib/tests",
      "scenic/dataset_lib/tests",
      "scenic/model_lib/tests",
      "scenic/model_lib/base_models/tests",
      "scenic/model_lib/layers/tests",
      "scenic/model_lib/matchers/tests",
      "scenic/train_lib/tests",
      "scenic/projects/**/tests and *test*.py"
    ],
    "configs": [
      "scenic/projects/**/configs/*.py"
    ],
    "tools": [
      "scenic/projects/*/tools/*.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ materially, run `refresh-repo-skill`.
- If package metadata, public run/config contracts, project requirements, or registry entry points changed even on the same commit, run `refresh-repo-skill`.
- This snapshot records only relative evidence paths and public source metadata; it intentionally omits local environment and checkout paths.
