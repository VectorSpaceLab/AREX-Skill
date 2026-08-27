# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MLJAR Supervised. If the current repo commit, dirty state, package version, public API signatures, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:24:41Z",
  "repository": {
    "name": "mljar-supervised",
    "remote_url": "https://github.com/mljar/mljar-supervised.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v1.3.2",
    "commit": "c6fa22b6888bedc4189458608e19508eabbc9be9",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source checkout was clean before repo-skill generation; the dirty path is generated skill/review output and production logging."
  },
  "packages": [
    {
      "name": "mljar-supervised",
      "version": "1.3.2",
      "import_names": ["supervised"]
    }
  ],
  "evidence": {
    "source_roots": ["supervised/"],
    "docs": [
      "README.md",
      "docs/docs/index.md",
      "docs/docs/api.md",
      "docs/docs/features/",
      "docs/docs/tutorials/"
    ],
    "examples": ["examples/scripts/", "examples/notebooks/"],
    "tests": [
      "tests/tests_automl/",
      "tests/tests_fairness/",
      "tests/tests_preprocessing/",
      "tests/tests_algorithms/",
      "tests/tests_ensemble/",
      "tests/tests_validation/",
      "tests/tests_utils/"
    ],
    "configs": [
      "setup.py",
      "requirements.txt",
      "requirements_dev.txt",
      "pytest.ini",
      ".github/workflows/"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata changes from `mljar-supervised` version `1.3.2`, refresh the skill.
- If public `AutoML` constructor/method signatures, supported modes, algorithm names, fairness metrics, app APIs, or report payload structure change, refresh the skill.
- If a checkout is dirty only because generated skill or review artifacts exist under `skills/`, compare source files separately before deciding it is stale.
- If source paths listed under `evidence` were renamed or substantially reorganized, refresh the skill.
