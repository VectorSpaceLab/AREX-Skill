# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of scispaCy. If the repository commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T16:36:46Z",
  "repository": {
    "name": "scispacy",
    "remote_url": "https://github.com/allenai/scispacy",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "eacccd4ef3e7ef13d4aa35700e718bd4318ded17",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "scispacy",
      "version": "0.6.2",
      "import_names": ["scispacy"]
    }
  ],
  "evidence": {
    "source_roots": ["scispacy"],
    "docs": ["README.md", "docs/index.md"],
    "examples": ["scripts", "evaluation"],
    "tests": ["tests", "tests/custom_tests"],
    "configs": ["configs", "project.yml", "requirements.in", "pyproject.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale and refresh it.
- If the working tree is dirty and this snapshot was clean, or the dirty paths differ, refresh it.
- If package metadata, supported Python versions, or public model/package behavior changes, refresh it.
