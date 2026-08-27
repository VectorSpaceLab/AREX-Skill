# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of LM Evaluation Harness. If the current commit, dirty state, package metadata, entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T06:30:00Z",
  "repository": {
    "name": "lm-evaluation-harness",
    "remote_url": "https://github.com/EleutherAI/lm-evaluation-harness.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1dd931087362abba74e0375c8c631295559f48b2",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "lm_eval",
      "version": "0.4.13.dev0",
      "import_names": ["lm_eval"],
      "python_requires": ">=3.10",
      "console_scripts": ["lm-eval", "lm_eval"]
    }
  ],
  "evidence": {
    "source_roots": ["lm_eval"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "scripts": ["scripts", "templates/new_yaml_task"],
    "tests": ["tests"],
    "package_metadata": ["pyproject.toml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If working-tree changes include package metadata, CLI modules, evaluator APIs, task config handling, model backends, result schemas, docs, examples, or scripts, refresh the skill.
- If `pyproject.toml` optional extras or console scripts change, refresh backend and CLI references.
- If docs move or the CLI subcommand surface changes, refresh root routing and evaluation-run guidance.
