# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of CVNets. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T17:09:00Z",
  "repository": {
    "name": "ml-cvnets",
    "remote_url": "https://github.com/apple/ml-cvnets.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "77717569ab4a852614dae01f010b32b820cb33bb",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "cvnets",
      "version": "0.3",
      "import_names": ["cvnets"]
    }
  ],
  "evidence": {
    "source_roots": ["common", "cvnets", "data", "engine", "loss_fn", "metrics", "optim", "options", "utils"],
    "docs": ["README.md", "docs/source"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["config"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
