# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of LMFlow. If the repository commit, dirty state, package version, or evidence paths differ materially from this snapshot, run a refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:29:17Z",
  "repository": {
    "name": "LMFlow",
    "remote_url": "https://github.com/OptimalScale/LMFlow.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e9b1da012f08d17fadad698278f505800d30a8af",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/lmflow/**",
      "skills/tests/lmflow/**",
      ".pytest_cache/**"
    ]
  },
  "packages": [
    {
      "name": "lmflow",
      "version": "1.1.0",
      "import_names": ["lmflow"]
    }
  ],
  "evidence": {
    "source_roots": ["src/lmflow"],
    "docs": ["README.md", "docs/source/examples", "docs/readme"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["configs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the working tree dirty set changes in a way that affects the source evidence above, refresh the skill.
- If package metadata, optional extras, or public entry points change, refresh the skill even on the same commit.
