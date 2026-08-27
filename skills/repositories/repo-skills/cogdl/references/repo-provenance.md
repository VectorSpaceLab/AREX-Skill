# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the commit, dirty state, package version, or major evidence paths
change, refresh the skill instead of assuming it is still aligned.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T20:57:04Z",
  "repository": {
    "name": "CogDL",
    "remote_url": "https://github.com/THUDM/CogDL.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "281f47424d58844b167ccbe41d9829c1f77689f8",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/cogdl",
      "skills/tests/cogdl"
    ]
  },
  "packages": [
    {
      "name": "cogdl",
      "version": "0.6",
      "import_names": [
        "cogdl"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "cogdl"
    ],
    "docs": [
      "README.md",
      "docs/source"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "tests"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "cogdl/configs.py",
      "scripts/train.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale.
- If the working tree is no longer dirty in the same way, or the generated skill
  tree changes substantially, refresh the skill.
- If CogDL's public package version or entry points change, refresh the skill.
