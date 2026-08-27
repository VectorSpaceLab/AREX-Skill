# Repository Provenance

## Purpose

Read this before deciding whether this NannyML repo skill is current for a checkout or installed package. If the current repository commit, package version, or important evidence paths differ from this snapshot, refresh the skill before relying on it for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T12:38:54Z",
  "repository": {
    "name": "nannyml",
    "remote_url": "https://github.com/NannyML/nannyml.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v0.13.1",
    "commit": "4c86ee350dc541cb244f965cf555b4b2a004ae99",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "nannyml",
      "version": "0.13.1",
      "source_version": "0.13.1",
      "import_names": ["nannyml"]
    }
  ],
  "evidence": {
    "source_roots": ["nannyml/"],
    "docs": [
      "README.md",
      "docs/tutorials/data_requirements.rst",
      "docs/tutorials/performance_estimation/",
      "docs/tutorials/performance_calculation/",
      "docs/tutorials/detecting_data_drift/",
      "docs/tutorials/data_quality/",
      "docs/tutorials/summary_stats/",
      "docs/tutorials/chunking.rst",
      "docs/tutorials/thresholds.rst",
      "docs/tutorials/working_with_results.rst",
      "docs/cli/"
    ],
    "examples": [
      "docs/examples/",
      "docs/example_notebooks/Examples California Housing.ipynb",
      "docs/example_notebooks/Examples Green Taxi.ipynb",
      "docs/example_notebooks/Tutorial - Working with results.ipynb",
      "docs/example_notebooks/Tutorial - Storing and Loading Calculators - Univariate.ipynb"
    ],
    "tests": [
      "tests/performance_estimation/CBPE/test_cbpe.py",
      "tests/performance_estimation/DLE/test_dle.py",
      "tests/performance_calculation/test_performance_calculator.py",
      "tests/drift/",
      "tests/data_quality/",
      "tests/stats/",
      "tests/test_chunk.py",
      "tests/test_thresholds.py",
      "tests/test_datasets.py",
      "tests/test_runner.py",
      "tests/test_ranking.py"
    ],
    "configs": ["pyproject.toml", "setup.cfg", "setup.py"],
    "bundled_runtime_replacements": ["scripts/check_install.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If `nannyml.__version__` differs from `0.13.1`, refresh API signatures, CLI behavior, and troubleshooting.
- If any of these files or directories changed, refresh the related route: `nannyml/performance_estimation/`, `nannyml/performance_calculation/`, `nannyml/drift/`, `nannyml/data_quality/`, `nannyml/stats/`, `nannyml/chunk.py`, `nannyml/thresholds.py`, `nannyml/config.py`, `nannyml/runner.py`, or `nannyml/cli/`.
- If the dirty working tree contains public package, docs, tests, or configuration changes other than generated `skills/` artifacts, refresh before relying on this skill.
- If `DatabaseWriter` optional dependencies or CLI dependency behavior changes, refresh [troubleshooting.md](troubleshooting.md) and the CLI route.
