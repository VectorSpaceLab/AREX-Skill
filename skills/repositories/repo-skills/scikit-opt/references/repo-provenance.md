# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of `scikit-opt`. If the repo commit, working tree state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T19:26:58Z",
  "repository": {
    "name": "scikit-opt",
    "remote_url": "https://github.com/guofei9987/scikit-opt.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "57d78324e72cd847750e0f4b1f65fdebc24fb524",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "scikit-opt",
      "version": "0.6.6",
      "import_names": ["sko"]
    }
  ],
  "evidence": {
    "source_roots": ["sko"],
    "docs": ["README.md", "docs/en"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["setup.py", "requirements.txt"]
  }
}
```

## Refresh check

- If the current `git rev-parse HEAD` differs from the commit above, the skill may be stale.
- If the dirty paths change materially, refresh the skill.
- If package metadata or verified runtime behavior changes, refresh the skill.
