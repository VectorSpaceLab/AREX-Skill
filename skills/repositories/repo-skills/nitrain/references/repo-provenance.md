# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current Nitrain checkout. If the commit, dirty state, package version, or main evidence paths have changed, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T18:48:51Z",
  "repository": {
    "name": "nitrain",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ecd3547c79643687412cb24aa872b4923a4fb865",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "nitrain",
      "version": "0.3.1",
      "import_names": ["nitrain"]
    }
  ],
  "evidence": {
    "source_roots": ["nitrain"],
    "docs": ["README.md"],
    "examples": [],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "requirements.txt", "requirements_extra.txt", ".github/workflows/test.yml", ".github/workflows/code-coverage.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, this skill may be stale.
- If the working tree becomes dirty or the package version changes, refresh the skill.
- If public exports, install requirements, or optional backend expectations change, refresh the skill even on the same commit.
