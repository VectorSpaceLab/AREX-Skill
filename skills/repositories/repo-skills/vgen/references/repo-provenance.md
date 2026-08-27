# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of VGen. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:46:38Z",
  "repository": {
    "name": "VGen",
    "remote_url": "https://github.com/ali-vilab/VGen.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4014d1fae4ac4a35e8e8442123611e913001399e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "VGen",
      "version": null,
      "import_names": ["tools", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["tools", "utils", "metric"],
    "docs": ["README.MD", "doc"],
    "examples": ["data"],
    "tests": ["test_func"],
    "configs": ["configs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
