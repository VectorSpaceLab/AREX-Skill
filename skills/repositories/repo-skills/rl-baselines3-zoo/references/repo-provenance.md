# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an RL Baselines3 Zoo checkout or package version. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this operating graph for changed APIs or workflows.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T09:02:10Z",
  "repository": {
    "name": "rl-baselines3-zoo",
    "remote_url": "https://github.com/DLR-RM/rl-baselines3-zoo.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f94cef4e59fb2f03b77177db432c3f771d0ee72c",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "rl_zoo3",
      "version": "2.9.2a0",
      "import_names": [
        "rl_zoo3"
      ]
    }
  ],
  "evidence": {
    "metadata": [
      "setup.py",
      "pyproject.toml",
      "requirements.txt",
      "docs/conda_env.yml"
    ],
    "source_roots": [
      "rl_zoo3",
      "rl_zoo3/plots"
    ],
    "docs": [
      "README.md",
      "docs/guide",
      "docs/modules",
      "benchmark.md"
    ],
    "configs": [
      "hyperparams",
      "hyperparams/python/ppo_config_example.py"
    ],
    "scripts": [
      "train.py",
      "enjoy.py",
      "scripts"
    ],
    "tests": [
      "tests/test_train.py",
      "tests/test_enjoy.py",
      "tests/test_hyperparams_opt.py",
      "tests/test_wrappers.py",
      "tests/test_callbacks.py",
      "tests/test_config.yml",
      "tests/dummy_env"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If public entry points, `setup.py` dependencies/extras, `rl_zoo3/train.py`, `rl_zoo3/enjoy.py`, `rl_zoo3/exp_manager.py`, `rl_zoo3/utils.py`, `rl_zoo3/hyperparams_opt.py`, `rl_zoo3/wrappers.py`, `rl_zoo3/callbacks.py`, `rl_zoo3/plots`, `hyperparams`, or docs guides changed, refresh the skill.
- If package version differs from `2.9.2a0`, run at least the root install checker and targeted sub-skill verification before using version-sensitive API or CLI claims.
- The checkout was dirty because generated skill/review artifacts were being written under `skills/`; no source files under `rl_zoo3`, `docs`, `hyperparams`, `scripts`, or `tests` were intentionally modified for this skill.
