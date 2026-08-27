# Repository Provenance

## Purpose

Read this before deciding whether this W&B skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "evidence": {
    "configs": [
      "pyproject.toml",
      "hatch.toml",
      "requirements"
    ],
    "docs": [
      "README.md",
      "package_readme.md",
      "docs"
    ],
    "examples": [
      "tests/assets/scripts",
      "tests/assets/notebooks"
    ],
    "scripts": [
      "tools/wandb_export_history.py",
      "tools/local_wandb_server.py"
    ],
    "source_roots": [
      "wandb"
    ],
    "tests": [
      "tests/unit_tests",
      "tests/system_tests/test_core",
      "tests/system_tests/test_artifacts",
      "tests/system_tests/test_api",
      "tests/system_tests/test_sweep",
      "tests/system_tests/test_launch",
      "tests/system_tests/test_automations",
      "tests/system_tests/test_registries"
    ]
  },
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "packages": [
    {
      "import_names": [
        "wandb"
      ],
      "name": "wandb",
      "version": "0.27.3.dev1"
    }
  ],
  "repository": {
    "branch": "main",
    "commit": "12d9004340791a09ef4fc0a3f4b6c1bf4076a8b4",
    "dirty_paths": [],
    "name": "wandb",
    "remote_url": "https://github.com/wandb/wandb",
    "tag": null,
    "vcs": "git",
    "working_tree": "clean"
  },
  "schema": "disco.repo-provenance.v1"
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it from repository evidence.
- If the current working tree is dirty and this snapshot is clean, or dirty paths differ from this snapshot, refresh before relying on exact behavior.
- If `wandb.__version__`, `pyproject.toml` entry points, public SDK signatures, CLI help, or major tests/docs changed, refresh even when the commit is similar.
- Keep local environment paths, credentials, and private installation details out of refreshed public skill content.
