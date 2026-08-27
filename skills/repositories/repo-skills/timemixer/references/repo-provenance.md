# Repository Provenance

## Purpose

Read this before deciding whether the TimeMixer skill still matches a checkout of the repository. If the current commit, dirty state, package metadata, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T13:21:12Z",
  "repository": {
    "name": "TimeMixer",
    "remote_url": "https://github.com/kwuking/TimeMixer.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e24610583b36fdd8c76cc17a8df4e65759a5f460",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "TimeMixer",
      "version": null,
      "import_names": ["models", "data_provider", "exp", "layers", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["data_provider", "exp", "layers", "models", "utils"],
    "docs": ["README.md"],
    "examples": ["scripts"],
    "tests": [],
    "configs": ["requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, refresh the skill.
- If the working tree dirty state or dirty paths materially differ from this snapshot, refresh the skill.
- If the public CLI, model API, dataset layouts, or benchmark scripts change, refresh the skill even on the same commit.
- If you need the current runtime state for a different checkout, read this file first.
