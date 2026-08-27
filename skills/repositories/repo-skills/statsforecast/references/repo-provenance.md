# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:53:47Z",
  "repository": {
    "name": "statsforecast",
    "remote_url": "https://github.com/Nixtla/statsforecast.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4876cd0d9ae83495b25e07f4b40ca42658f5793a",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "submodules": [
      {
        "path": "external_libs/eigen",
        "commit": "9df21dc8b4b576a7aa5c0094daa8d7e8b8be60f0"
      }
    ]
  },
  "packages": [
    {
      "name": "statsforecast",
      "version": "2.1.1",
      "import_names": ["statsforecast"]
    }
  ],
  "evidence": {
    "source_roots": [
      "python/statsforecast",
      "src",
      "include/statsforecast"
    ],
    "docs": [
      "README.md",
      "docs/src/core/core.html.md",
      "docs/src/core/models.html.md",
      "docs/src/core/distributed.fugue.html.md",
      "docs/src/feature_engineering.html.md",
      "nbs/docs/getting-started",
      "nbs/docs/how-to-guides",
      "nbs/docs/tutorials",
      "nbs/docs/models",
      "nbs/docs/distributed"
    ],
    "examples": [
      "action_files/test_fit_predict.py",
      "action_files/utils.py",
      "action_files/test_dask.py",
      "action_files/test_ray.py",
      "action_files/test_spark.py"
    ],
    "tests": [
      "tests/test_core.py",
      "tests/test_models.py",
      "tests/test_feature_engineering.py",
      "tests/test_distributed_core.py",
      "tests/test_distributed_multiprocess.py",
      "tests/test_arima.py",
      "tests/test_ets.py",
      "tests/test_ces.py",
      "tests/test_theta.py",
      "tests/test_mstl.py",
      "tests/test_mfles.py",
      "tests/test_garch.py",
      "tests/test_ucm.py"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "MANIFEST.in",
      "uv.lock"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, public model signatures, optional dependency groups, or backend behavior changed even on the same commit, run `refresh-repo-skill`.
- If the package is used from a released wheel whose version differs from `2.1.1`, verify the changed APIs before trusting parameter details in this skill.
