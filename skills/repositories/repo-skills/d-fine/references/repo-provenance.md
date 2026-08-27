# Repository Provenance

## Purpose

Read this before deciding whether the D-FINE repo skill is current for a checkout of the repository. If the current commit, dirty state, package surface, or evidence paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:43:39Z",
  "repository": {
    "name": "D-FINE",
    "remote_url": "https://github.com/Peterande/D-FINE.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "267a6da6d04c8ad52e54120692896515b9e55981",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "D-FINE",
      "version": null,
      "import_names": [
        "src"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src",
      "configs",
      "tools",
      "reference",
      "train.py"
    ],
    "docs": [
      "README.md",
      "README_cn.md",
      "README_ja.md"
    ],
    "examples": [],
    "tests": [],
    "configs": [
      "configs/dataset",
      "configs/dfine",
      "configs/runtime.yml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the working tree dirty paths change meaningfully, refresh the skill.
- If the repo adds packaging metadata, new public entry points, or different config families, refresh the skill.
- If the user asks about a newer checkout, compare the current evidence against this snapshot before reusing the skill.
