# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run a refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:49:28Z",
  "repository": {
    "name": "aws-sdk-pandas",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "fef16bb0c18092169d893aacf2a767513e776b95",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "awswrangler",
      "version": "3.17.1",
      "import_names": ["awswrangler"]
    }
  ],
  "evidence": {
    "source_roots": ["awswrangler"],
    "docs": ["README.md", "docs/source", "CONTRIBUTING.md", "CONTRIBUTING_COMMON_ERRORS.md", "adr"],
    "examples": ["tutorials", "tests/glue_scripts"],
    "tests": ["tests/unit", "tests/load", "tests/benchmark"],
    "configs": ["pyproject.toml", "tox.ini", "docs/environment.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, the skill may be stale.
- If the working tree becomes dirty, compare the dirty paths to this snapshot.
- If package metadata or public imports change on the same commit, refresh the skill.
