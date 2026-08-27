# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T16:52:45Z",
  "repository": {
    "name": "lightfm",
    "remote_url": "https://github.com/lyst/lightfm.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0c9c31e027b976beab2385e268b58010fff46096",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "lightfm",
      "version": "1.17",
      "import_names": ["lightfm"]
    }
  ],
  "evidence": {
    "source_roots": ["lightfm/"],
    "metadata": ["setup.py", "setup.cfg", "README.md", "lightfm/version.py"],
    "docs": ["README.md", "doc/", "doc/examples/", "doc/faq.rst"],
    "examples": ["examples/quickstart/", "examples/movielens/", "examples/stackexchange/", "examples/dataset/", "examples/ann/"],
    "tests": ["tests/test_api.py", "tests/test_data.py", "tests/test_evaluation.py", "tests/test_cross_validation.py", "tests/test_datasets.py", "tests/test_movielens.py", "tests/test_fast_functions.py"],
    "maintenance": ["Makefile", ".github/workflows/test.yaml", "test-requirements.txt", "lint-requirements.txt", "docs-requirements.txt", "lightfm/_lightfm_fast.pyx.template", "lightfm/_lightfm_fast_openmp.c", "lightfm/_lightfm_fast_no_openmp.c"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, examples, tests, or package metadata changes beyond generated skill artifacts, refresh before relying on precise API/build guidance.
- If `lightfm.__version__`, public method signatures, compiled extension names, dataset fetcher behavior, or CI/test requirements change, refresh even when the commit comparison looks unchanged.
- If package installation starts selecting a different compiled extension path or Python version support changes, refresh the `repo-development` and root troubleshooting guidance.
