# Repository Provenance

## Purpose

Read this before deciding whether this AutoKeras skill is current for a checkout. If the current commit, package version, public APIs, or major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:23:22Z",
  "repository": {
    "name": "autokeras",
    "remote_url": "https://github.com/keras-team/autokeras.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a2446cf16edcca48ba558d70ac5345e4f30c78e1",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "autokeras",
      "version": "3.0.0",
      "import_names": [
        "autokeras"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "autokeras"
    ],
    "docs": [
      "README.md",
      "docs/templates/install.md",
      "docs/templates/tutorial/overview.md",
      "docs/py"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "autokeras/*_test.py",
      "autokeras/**/*_test.py",
      "autokeras/integration_tests",
      "autokeras/test_utils.py"
    ],
    "configs": [
      "pyproject.toml",
      "setup.cfg",
      ".github/workflows/actions.yml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If package metadata, public task classes, AutoModel signatures, Keras backend assumptions, or docs examples changed, refresh the skill.
- Paths above are relative source evidence paths; no local environment path is part of this public provenance.
- The source baseline was captured before generated runtime and review artifacts were written.
