# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of XTuner. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:21:03Z",
  "repository": {
    "name": "xtuner",
    "remote_url": "https://github.com/InternLM/xtuner",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "575d7e058040baa7f609b3d5d3f397653877bc25",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "xtuner",
      "version": "0.2.0",
      "import_names": [
        "xtuner"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "xtuner",
      "xtuner/v1"
    ],
    "docs": [
      "README.md",
      "docs/en/get_started",
      "docs/en/pretrain_sft",
      "docs/en/rl",
      "docs/en/api",
      "docs/en/benchmark"
    ],
    "examples": [
      "examples/v1",
      "examples/demo_data",
      "examples/huggingface_trainer"
    ],
    "tests": [
      "tests",
      "tests/resource",
      "autotest"
    ],
    "configs": [
      "xtuner/configs",
      "examples/v1/config"
    ],
    "scripts": [
      "xtuner/tools",
      "examples/v1/scripts",
      ".dev_scripts",
      "ci/scripts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, refresh before relying on generated guidance.
- If package metadata, V1 CLI help, model config classes, data protocol classes, or RL trainer config APIs changed even on the same commit, refresh the skill.
- This skill intentionally excludes generated review/test artifacts and live import state from public runtime guidance.
