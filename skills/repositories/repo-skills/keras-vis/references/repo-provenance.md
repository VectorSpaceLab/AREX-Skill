# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, request the repository-skill refresh through the upper-layer tooling; this bundle does not contain a refresh executable.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T06:37:43Z",
  "repository": {
    "name": "keras-vis",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "90ae5565951b5e6a90d706b8205c2c4dfc271505",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "keras-vis",
      "version": "0.5.0",
      "import_names": ["vis"]
    }
  ],
  "evidence": {
    "source_roots": ["vis"],
    "docs": ["README.md", "docs/templates/visualizations", "docs/README.md"],
    "examples": ["examples", "applications/self_driving"],
    "tests": ["tests"],
    "configs": ["setup.py", "setup.cfg", "pytest.ini", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and ask the upper-layer repository-skill tooling to refresh it.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the dirty paths differ materially, ask the upper-layer repository-skill tooling to refresh it.
- If package metadata or public entry points changed even on the same commit, ask the upper-layer repository-skill tooling to refresh it.
