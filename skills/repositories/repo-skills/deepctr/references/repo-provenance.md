# Repository Provenance

## Purpose

Read this before deciding whether the skill matches the current DeepCTR checkout. If the repository commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:39:05Z",
  "repository": {
    "name": "DeepCTR",
    "remote_url": "https://github.com/shenweichen/DeepCTR.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "1b5fe40e158d1ee6af8b1d9df217a5ed5aea9136",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "deepctr",
      "version": "0.9.4",
      "import_names": ["deepctr"]
    }
  ],
  "evidence": {
    "source_roots": ["deepctr/"],
    "docs": ["README.md", "docs/source/"],
    "examples": ["examples/"],
    "tests": ["tests/"],
    "configs": ["setup.py", "setup.cfg", ".github/workflows/ci.yml", ".github/workflows/ci2.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the working tree becomes clean after this snapshot was dirty, or if the dirty paths change materially, refresh the skill.
- If package metadata or public entry points change on the same commit, refresh the skill.
