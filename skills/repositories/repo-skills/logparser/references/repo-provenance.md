# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T17:03:01Z",
  "repository": {
    "name": "logparser",
    "remote_url": "https://github.com/logpai/logparser.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d9d4180784cde9afef990eeeb458591011933f9b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "logparser3",
      "version": "1.0.4",
      "import_names": ["logparser"]
    }
  ],
  "evidence": {
    "source_roots": ["logparser"],
    "docs": ["README.md", "docs"],
    "examples": ["example"],
    "tests": ["tests"],
    "configs": [".github/workflows/ci.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale.
- If the dirty path set changes in a meaningful way, refresh the skill.
- If package metadata or public entry points change, refresh the skill.
- If the parser catalog or backend requirements change, re-run the extraction
  workflow before reusing this skill.
