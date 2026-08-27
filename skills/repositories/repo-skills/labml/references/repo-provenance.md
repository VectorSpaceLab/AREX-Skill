# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
path set differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T12:58:22Z",
  "repository": {
    "name": "labml",
    "remote_url": "https://github.com/labmlai/labml.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "11c6efee6fc98098b8ccb3e8412a007c3c562034",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "labml",
      "version": "0.5.4",
      "import_names": ["labml"]
    },
    {
      "name": "labml-helpers",
      "version": "0.4.89",
      "import_names": ["labml_helpers"]
    },
    {
      "name": "labml-remote",
      "version": "0.1.0",
      "import_names": ["labml_remote"]
    },
    {
      "name": "labml-app",
      "version": "0.5.14",
      "import_names": ["labml_app"]
    }
  ],
  "evidence": {
    "source_roots": [
      "client/labml",
      "helpers/labml_helpers",
      "remote/labml_remote",
      "app/server/labml_app"
    ],
    "docs": [
      "readme.md",
      "client/api_readme.md",
      "client-docs/source",
      "helpers/readme.md",
      "remote/readme.md",
      "app/readme.md",
      "guides"
    ],
    "examples": ["samples"],
    "tests": ["client/test", "app/server/unit_tests", "helpers/labml_helpers/datasets/remote/test"],
    "configs": [
      "client/requirements.txt",
      "helpers/requirements.txt",
      "remote/setup.py",
      "app/server/setup.py",
      "app/server/labml_app/settings.sample.py",
      "app/server/labml_app/analyses_settings.sample.py",
      "app/ui/package.json"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run
  `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.
