# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:34:11Z",
  "repository": {
    "name": "tslearn",
    "remote_url": "https://github.com/tslearn-team/tslearn.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d4864da3687a0685efa3b73ee7ad5ac3c46f4702",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/tslearn",
      "skills/tests/tslearn"
    ]
  },
  "packages": [
    {
      "name": "tslearn",
      "version": "0.10.0.dev0",
      "import_names": ["tslearn"]
    }
  ],
  "evidence": {
    "source_roots": ["tslearn"],
    "docs": ["README.md", "docs"],
    "examples": ["docs/examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "conftest.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
