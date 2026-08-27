# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current `imagen-pytorch` checkout. If the repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:16:47Z",
  "repository": {
    "name": "imagen-pytorch",
    "remote_url": "https://github.com/lucidrains/imagen-pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": "2.1.0",
    "commit": "192f8b924ba8ebd7b5d2b02422d6b2755e123b1d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "imagen-pytorch",
      "version": "2.1.0",
      "import_names": ["imagen_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["imagen_pytorch"],
    "docs": ["README.md"],
    "tests": ["imagen_pytorch/test"],
    "configs": ["imagen_pytorch/default_config.json"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If the current working tree dirty paths differ materially from the snapshot, refresh it.
- If package metadata or public entry points change on the same commit, refresh it.
