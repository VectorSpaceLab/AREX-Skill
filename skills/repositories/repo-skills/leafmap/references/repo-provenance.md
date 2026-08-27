# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of leafmap. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:39:33Z",
  "repository": {
    "name": "leafmap",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "18df7ee48cb27a194d89568c389a3f98443b8e8b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "leafmap",
      "version": "0.63.1",
      "import_names": ["leafmap"]
    }
  ],
  "evidence": {
    "source_roots": ["leafmap"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "environment.yml", "requirements.txt", "requirements_dev.txt", "requirements_docs.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
