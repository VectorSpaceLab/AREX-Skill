# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a BasicTS checkout. If the commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:13:25Z",
  "repository": {
    "name": "BasicTS",
    "remote_url": "https://github.com/GestaltCogTeam/BasicTS.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c2bb6e31e591167e84459775a21a62e70a5893ce",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "BasicTS",
      "version": "1.1.0",
      "import_names": ["basicts"]
    }
  ],
  "evidence": {
    "source_roots": ["src/basicts"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests/smoke_test"],
    "configs": ["pyproject.toml", "requirements.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, refresh the skill.
- If the working tree becomes dirty and the dirty path set changes, refresh the skill.
- If the package version or public import surface changes, refresh the skill.
