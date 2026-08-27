# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, dependencies, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "segmentation_models.pytorch",
    "remote_url": "https://github.com/qubvel-org/segmentation_models.pytorch",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "18a6197be5a746ce74e46b6fe706784f9b6a35d1",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "segmentation_models_pytorch",
      "version": "0.5.1.dev0",
      "import_names": ["segmentation_models_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["segmentation_models_pytorch"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "requirements", "Makefile"],
    "scripts": ["scripts/models-conversions", "misc"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has changed files outside generated `skills/` artifacts, compare those paths against the evidence list and refresh when they affect public APIs, docs, examples, tests, configs, or scripts.
- If the package version, architecture registry, encoder registry, loss/metric signatures, save/load APIs, or export/test conventions changed, refresh even on the same commit.
