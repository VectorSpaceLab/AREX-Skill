# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout or installed copy of auto-sklearn. If the current repo commit, dirty state, package version, public estimator signatures, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this generated skill for repository-specific details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:13:04Z",
  "repository": {
    "name": "auto-sklearn",
    "remote_url": "https://github.com/automl/auto-sklearn.git",
    "vcs": "git",
    "branch": "development",
    "tag": null,
    "commit": "673211252ca508b6f5bb92cf5fa87c6455bbad99",
    "working_tree": "clean",
    "dirty_paths": [],
    "submodules": [
      {
        "path": "autosklearn/automl_common",
        "commit": "c760e29b5fbf90455d1a16aebbca6424468628c2"
      }
    ]
  },
  "packages": [
    {
      "name": "auto-sklearn",
      "version": "0.16.0.dev0",
      "import_names": ["autosklearn"],
      "source_version_string": "0.16.0dev"
    }
  ],
  "evidence": {
    "source_roots": [
      "autosklearn",
      "autosklearn/automl_common"
    ],
    "docs": [
      "README.md",
      "doc/installation.rst",
      "doc/manual.rst",
      "doc/api.rst",
      "doc/extending.rst",
      "doc/faq.rst"
    ],
    "examples": [
      "examples/20_basic",
      "examples/40_advanced",
      "examples/60_search",
      "examples/80_extending"
    ],
    "tests": [
      "test/test_estimators",
      "test/test_data",
      "test/test_metric",
      "test/test_pipeline",
      "test/test_ensemble_builder",
      "test/test_scripts",
      "test/test_util"
    ],
    "scripts": [
      "scripts/readme.md",
      "scripts/01_create_commands.py",
      "scripts/02_retrieve_metadata.py",
      "scripts/03_calculate_metafeatures.py",
      "scripts/04_create_aslib_files.py",
      "scripts/run_auto-sklearn_for_metadata_generation.py",
      "scripts/update_metadata_util.py"
    ],
    "configs": [
      "setup.py",
      "pyproject.toml",
      "requirements.txt",
      ".gitmodules",
      ".github/workflows/pytest.yml"
    ],
    "other": [
      "CONTRIBUTING.md",
      "misc"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the checkout dirty state differs from this snapshot, refresh before using source-specific guidance.
- If `autosklearn.__version__`, installed distribution metadata, public estimator signatures, metric lists, component registries, or AutoSklearn2 behavior differ, refresh or re-verify the affected sub-skill.
- If the `autosklearn/automl_common` submodule commit differs and the task is source-maintenance or backend/file handling, refresh the metadata-maintenance guidance.
- If a task depends on examples, metadata scripts, or tests not listed above, inspect and refresh the relevant route before relying on this skill.
