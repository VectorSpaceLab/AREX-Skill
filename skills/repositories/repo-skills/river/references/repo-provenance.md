# Repository Provenance

## Purpose

Read this before deciding whether this River skill is current for a checkout. If the current repository commit, dirty state, package version, or public entry points differ from this snapshot, refresh the repo skill before relying on detailed API guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:09:20Z",
  "repository": {
    "name": "river",
    "remote_url": "https://github.com/online-ml/river.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ab092395a9d6654f51d2fd020af6a127c29ded42",
    "working_tree": "dirty",
    "dirty_paths": ["skills/ (generated skill artifacts and production log)"]
  },
  "packages": [
    {
      "name": "river",
      "version": "0.25.0",
      "import_names": ["river"]
    }
  ],
  "evidence": {
    "source_roots": ["river/"],
    "docs": ["README.md", "docs/introduction/", "docs/faq/", "docs/recipes/", "docs/examples/"],
    "examples": ["docs/recipes/*.ipynb", "docs/examples/*.ipynb"],
    "tests": ["tests/test_estimators.py", "tests/compose/", "tests/stream/", "tests/evaluate/", "tests/metrics/", "tests/linear_model/", "tests/drift/", "tests/anomaly/", "tests/cluster/", "tests/time_series/", "tests/bandit/"],
    "configs": ["pyproject.toml", "Cargo.toml", "Cargo.lock", ".python-version"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale.
- If package metadata, `river/api.py`, exported module `__all__` lists, base estimator interfaces, or optional dependency declarations change, refresh the skill even on the same commit.
- If a checkout is generated from a dirty source tree that changes files outside generated `skills/`, refresh before using detailed behavior claims.
