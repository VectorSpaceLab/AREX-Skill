# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T19:22:41Z",
  "repository": {
    "name": "autogluon",
    "remote_url": "https://github.com/autogluon/autogluon",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "8d7250d7a429e734583eb1495b3386cd6e5ced9d",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "autogluon",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon"]
    },
    {
      "name": "autogluon.common",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon.common"]
    },
    {
      "name": "autogluon.core",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon.core"]
    },
    {
      "name": "autogluon.features",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon.features"]
    },
    {
      "name": "autogluon.tabular",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon.tabular"]
    },
    {
      "name": "autogluon.timeseries",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon.timeseries"]
    },
    {
      "name": "autogluon.multimodal",
      "version": "1.5.1.dev0",
      "import_names": ["autogluon.multimodal"]
    }
  ],
  "evidence": {
    "source_roots": [
      "autogluon/src/autogluon",
      "common/src/autogluon/common",
      "core/src/autogluon/core",
      "features/src/autogluon/features",
      "tabular/src/autogluon/tabular",
      "timeseries/src/autogluon/timeseries",
      "multimodal/src/autogluon/multimodal"
    ],
    "docs": [
      "README.md",
      "docs/install.md",
      "docs/cheatsheet.md",
      "docs/api",
      "docs/tutorials/tabular",
      "docs/tutorials/timeseries",
      "docs/tutorials/multimodal"
    ],
    "examples": [
      "examples/tabular",
      "examples/automm",
      "examples/image_regression"
    ],
    "tests": [
      "common/tests",
      "core/tests",
      "features/tests",
      "tabular/tests",
      "timeseries/tests",
      "multimodal/tests"
    ],
    "configs": [
      "tabular/src/autogluon/tabular/configs",
      "timeseries/src/autogluon/timeseries/configs",
      "multimodal/src/autogluon/multimodal/configs"
    ],
    "packaging": [
      "pyproject.toml",
      "setup.cfg",
      "VERSION",
      "common/setup.py",
      "core/setup.py",
      "features/setup.py",
      "tabular/setup.py",
      "timeseries/setup.py",
      "multimodal/setup.py",
      "autogluon/setup.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If current source, docs, examples, tests, package metadata, or public predictor signatures differ from this snapshot, run `refresh-repo-skill`.
- Generated skill or review artifacts created after this snapshot do not by themselves make the source evidence stale.
