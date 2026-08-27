# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:45:15Z",
  "repository": {
    "name": "folium",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "389aa8c61c37abf24ce33927b0e4e6ddf32a5e81",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "folium",
      "version": "0.1.dev1+g389aa8c61",
      "import_names": ["folium"]
    }
  ],
  "evidence": {
    "source_roots": ["folium"],
    "docs": ["README.rst", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "environment.yml", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the `commit` above, treat the skill as potentially stale and refresh it.
- If the current working tree becomes clean after this snapshot was dirty, or the dirty paths change materially, refresh the skill.
- If package metadata or public entry points change even on the same commit, refresh the skill.
