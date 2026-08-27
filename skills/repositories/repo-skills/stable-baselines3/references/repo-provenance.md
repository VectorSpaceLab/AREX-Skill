# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Stable-Baselines3. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "stable-baselines3",
    "remote_url": "https://github.com/DLR-RM/stable-baselines3",
    "vcs": "git",
    "branch": "master",
    "tag": "v2.9.0",
    "commit": "8908708f10c8ff29759c67f55c8acb56cab27463",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "stable_baselines3",
      "version": "2.9.0",
      "import_names": ["stable_baselines3"]
    }
  ],
  "evidence": {
    "source_roots": ["stable_baselines3"],
    "docs": ["README.md", "docs/guide", "docs/modules", "docs/common"],
    "tests": [
      "tests/test_run.py",
      "tests/test_save_load.py",
      "tests/test_predict.py",
      "tests/test_env_checker.py",
      "tests/test_vec_envs.py",
      "tests/test_callbacks.py",
      "tests/test_custom_policy.py",
      "tests/test_dict_env.py",
      "tests/test_her.py",
      "tests/test_sde.py"
    ],
    "scripts": ["scripts/run_tests.sh"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If package metadata, public exports, constructor signatures, or documented workflows changed, refresh even if the commit is close.
- If the current checkout has source/doc/test changes outside generated `skills/` artifacts, refresh before relying on exact API details.
