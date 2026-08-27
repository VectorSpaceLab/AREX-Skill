# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a RoboCasa checkout.
If the commit, dirty state, package version, or major evidence paths differ,
refresh the repo skill before relying on detailed behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T18:10:36Z",
  "repository": {
    "name": "robocasa",
    "remote_url": "https://github.com/robocasa/robocasa.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "921c9a5736a8d0ea5589657898aadcfa55a6a195",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "robocasa",
      "version": "1.0.1",
      "import_names": ["robocasa"]
    },
    {
      "name": "robosuite",
      "version": "1.5.2-or-newer",
      "import_names": ["robosuite"]
    }
  ],
  "evidence": {
    "source_roots": [
      "robocasa/",
      "robocasa/environments/",
      "robocasa/models/",
      "robocasa/utils/",
      "robocasa/wrappers/"
    ],
    "docs": [
      "README.md",
      "docs/introduction/",
      "docs/tasks/",
      "docs/assets/",
      "docs/datasets/",
      "docs/use_cases/",
      "docs/benchmarking/"
    ],
    "examples": ["robocasa/demos/"],
    "tests": ["tests/test_env_determinism.py", "tests/test_datasets.py", "tests/test_dataset_playback.py", "tests/test_tasks_validity.py"],
    "configs": ["setup.py", "requirements.txt", "robocasa/models/assets/", "robocasa/demo_style_mapping.json"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `921c9a5736a8d0ea5589657898aadcfa55a6a195`, treat this graph as potentially stale.
- If the checkout is clean or its dirty paths differ from the snapshot, review
  generated content before use; `skills/` is construction output and is not a
  source-code baseline.
- Refresh when `setup.py`, public environment registration, dataset registries,
  wrapper signatures, asset registries, or the documented dataset layout
  changes.
- The full kitchen assets and datasets were not part of this snapshot. A future
  refresh should repeat a small asset/data readiness probe rather than silently
  promoting constructor-only verification to full reset or playback coverage.
