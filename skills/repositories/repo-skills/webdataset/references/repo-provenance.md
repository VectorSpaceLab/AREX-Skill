# Repository Provenance

## Purpose

Read this before deciding whether the generated skill is current for a checkout of the repository. If the commit, dirty state, package version, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:05:15Z",
  "repository": {
    "name": "webdataset",
    "remote_url": "https://github.com/webdataset/webdataset.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e0953f9bba17b416d5792d5a263b171c266e78be",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "webdataset",
      "version": "1.0.2",
      "import_names": ["webdataset"]
    }
  ],
  "evidence": {
    "source_roots": ["src/webdataset"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "Makefile", "mkdocs.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the dirty paths differ materially from this snapshot, refresh the skill.
- If package metadata or public entry points change without a commit change, refresh the skill.
- If a later checkout no longer contains the evidence paths above, refresh before using the skill.
