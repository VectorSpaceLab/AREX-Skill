# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T19:49:25Z",
  "repository": {
    "name": "CenterNet",
    "remote_url": "https://github.com/Duankaiwen/CenterNet.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3ad3a1062f809dd808aa53b02fb07b74530bb640",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/CenterNet.log",
      "skills/disco/centernet",
      "skills/tests/centernet"
    ]
  },
  "packages": [
    {
      "name": "CenterNet",
      "version": null,
      "import_names": [
        "config",
        "db",
        "models",
        "nnet",
        "sample",
        "test",
        "utils",
        "external"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "config.py",
      "db",
      "models",
      "nnet",
      "sample",
      "test",
      "utils",
      "external",
      "data/coco/PythonAPI/pycocotools"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "sample",
      "test"
    ],
    "tests": [
      "test.py",
      "test"
    ],
    "configs": [
      "config.py",
      "config",
      "conda_packagelist.txt"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
