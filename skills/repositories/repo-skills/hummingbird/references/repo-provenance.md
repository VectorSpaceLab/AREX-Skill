# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public API, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:41:01Z",
  "repository": {
    "name": "hummingbird",
    "remote_url": "https://github.com/microsoft/hummingbird.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "eb0a23538b364a021b3b723833cfb7e4dcd96134",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The checkout already had a repository-local skills log before generation; this workflow also writes generated skill and review artifacts under skills/."
  },
  "packages": [
    {
      "name": "hummingbird-ml",
      "version": "0.4.12",
      "import_names": [
        "hummingbird",
        "hummingbird.ml"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "hummingbird/"
    ],
    "docs": [
      "README.md",
      "TROUBLESHOOTING.md",
      "website/sphinx/index.rst"
    ],
    "examples": [
      "notebooks/"
    ],
    "tests": [
      "tests/test_backends.py",
      "tests/test_extra_conf.py",
      "tests/test_no_extra_install.py",
      "tests/test_sklearn_*.py",
      "tests/test_onnxml_*.py",
      "tests/test_lightgbm_converter.py",
      "tests/test_xgboost_converter.py",
      "tests/test_sparkml_*.py",
      "tests/test_prophet.py"
    ],
    "configs": [
      "setup.py",
      "pyproject.toml",
      "setup.cfg",
      ".github/workflows/pythonapp.yml"
    ]
  },
  "verification_scope": {
    "verified": [
      "CPU PyTorch import and tiny conversion smoke",
      "ONNX extra import and tiny conversion smoke",
      "public API signature inspection"
    ],
    "optional_not_verified_in_this_run": [
      "CUDA runtime execution",
      "TVM backend execution",
      "LightGBM conversion",
      "XGBoost conversion",
      "SparkML conversion",
      "Prophet conversion",
      "benchmark-scale performance runs"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the changed paths affect package source, docs, tests, setup metadata, optional dependencies, or public examples, run `refresh-repo-skill`.
- If the package version or public entry points change, run `refresh-repo-skill`.
- If a task requires CUDA, TVM, SparkML, LightGBM, XGBoost, Prophet, or benchmark verification beyond the recorded scope, prepare that environment before claiming the runtime behavior is verified.
