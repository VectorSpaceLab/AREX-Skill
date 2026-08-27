# Repository Provenance

## Purpose

Read this before deciding whether the skill matches a checkout of EdgeConnect. If the commit, dirty state, package layout, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:22:02Z",
  "repository": {
    "name": "edge-connect",
    "remote_url": "https://github.com/knazeri/edge-connect.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3142579785c5c8cc92ad655616d40f4f52fc7ec1",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/edge-connect/",
      "skills/tests/edge-connect/"
    ]
  },
  "packages": [
    {
      "name": "edge-connect",
      "version": null,
      "import_names": [
        "src.config",
        "src.dataset",
        "src.edge_connect",
        "src.loss",
        "src.metrics",
        "src.models",
        "src.networks",
        "src.utils"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "train.py",
      "test.py"
    ],
    "configs": [
      "config.yml.example"
    ],
    "scripts": [
      "scripts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale.
- If the dirty paths differ, treat the skill as potentially stale.
- If the package layout or public entry points change, refresh the skill even when the commit is the same.
