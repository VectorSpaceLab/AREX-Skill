# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
Lazy Predict repository. If the current repo commit, dirty state, package
version, public entry points, optional dependency groups, or major evidence
paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:22:31Z",
  "repository": {
    "name": "lazypredict",
    "remote_url": "https://github.com/shankarpandala/lazypredict.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "57a65577966b0928f2aad54c5fac6ebd8adf8a40",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": ["skills/"],
    "source_package_dirty_paths": []
  },
  "packages": [
    {
      "name": "lazypredict",
      "version": "0.3.0",
      "import_names": ["lazypredict"]
    }
  ],
  "evidence": {
    "source_roots": ["lazypredict/"],
    "docs": ["README.md", "docs/usage.md", "docs/advanced.md", "docs/forecasting.md", "docs/installation.md", "docs/api/"],
    "examples": ["examples/classification_example.py", "examples/regression_example.py", "examples/timeseries_example.py"],
    "tests": ["tests/test_cli.py", "tests/test_supervised.py", "tests/test_categorical_encoder.py", "tests/test_config.py", "tests/test_new_features.py", "tests/test_roadmap_features.py", "tests/test_timeseries.py"],
    "package_metadata": ["pyproject.toml", "setup.py", "setup.cfg", "MANIFEST.in", "requirements.txt", "tox.ini"],
    "entry_points": ["lazypredict = lazypredict.cli:main"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source-package changes outside generated skill
  artifacts, refresh before trusting API signatures or optional dependency
  guidance.
- If `pyproject.toml`, the console script entry point, `lazypredict/Supervised.py`,
  `lazypredict/TimeSeriesForecasting.py`, or the optional extras changed,
  refresh this skill even when the commit is otherwise familiar.
