# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Norfair. If the commit, dirty state, package version, or evidence paths differ materially from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T18:35:58Z",
  "repository": {
    "name": "norfair",
    "remote_url": "https://github.com/tryolabs/norfair.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v2.3.0",
    "commit": "e517b4236f6b67a6ecf342f5df1fccb7788dbc54",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/norfair",
      "skills/tests/norfair"
    ]
  },
  "packages": [
    {
      "name": "norfair",
      "version": "2.3.0",
      "import_names": ["norfair"]
    }
  ],
  "evidence": {
    "source_roots": ["norfair"],
    "docs": ["README.md", "docs"],
    "examples": ["demos/reid", "demos/camera_motion", "demos/motmetrics4norfair"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "mkdocs.yml", "tox.ini"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the tracked evidence shifts materially, refresh the skill.
- If the package version or public API surface changes, refresh the skill even on the same commit.
