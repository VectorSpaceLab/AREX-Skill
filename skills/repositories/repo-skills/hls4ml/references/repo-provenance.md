# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current hls4ml checkout. If the commit, dirty state, package version, or major evidence paths differ, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:08:23Z",
  "repository": {
    "name": "hls4ml",
    "remote_url": "https://github.com/fastmachinelearning/hls4ml.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b90fb06736baa0908a8995fc1cf4ac4a7d1c241f",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "hls4ml",
      "version": "0.1.0.dev1+gb90fb0673",
      "import_names": ["hls4ml"]
    }
  ],
  "evidence": {
    "source_roots": ["hls4ml", "hls4ml/templates"],
    "docs": ["README.md", "docs"],
    "examples": ["test/pytest"],
    "tests": ["test/pytest"],
    "configs": ["pyproject.toml", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale.
- If `skills/` changes materially, refresh the skill.
- If package metadata or public entry points change, refresh the skill.
