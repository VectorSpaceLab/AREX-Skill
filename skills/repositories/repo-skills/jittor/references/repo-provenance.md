# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a Jittor checkout or an installed package snapshot. If the current commit, working tree, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T18:09:15Z",
  "repository": {
    "name": "jittor",
    "remote_url": "https://github.com/Jittor/jittor.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "06f5d3d271555682c95aa3505518f47eeab2bd9c",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "jittor",
      "version": "1.3.11.0",
      "import_names": [
        "jittor",
        "jittor_utils"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "python/jittor",
      "python/jittor_utils"
    ],
    "docs": [
      "README.md",
      "README.src.md",
      "README.cn.md",
      "doc/source"
    ],
    "examples": [
      "python/jittor/notebook",
      "python/jittor/demo",
      "python/jittor/script"
    ],
    "tests": [
      "python/jittor/test"
    ],
    "configs": [
      "setup.py",
      "MANIFEST.in",
      ".github/workflows/main.yml",
      ".gitlab-ci.yml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale and refresh it.
- If the working tree dirty paths change materially from this snapshot, refresh it.
- If the package version or public entry points change, refresh it even if the commit is the same.
- If the repo no longer looks like public Jittor, do not reuse this skill without a fresh review.