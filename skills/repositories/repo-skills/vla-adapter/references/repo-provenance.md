# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
VLA-Adapter. If the current commit, dirty state, package version, public APIs,
or major workflow files differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T12:56:51Z",
  "repository": {
    "name": "VLA-Adapter",
    "remote_url": "https://github.com/OpenHelix-Team/VLA-Adapter",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "23fa0c9c159e2aa04341cdd3e924f44061311060",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "vla-adapter",
      "version": "0.0.1",
      "import_names": ["prismatic"]
    }
  ],
  "evidence": {
    "source_roots": [
      "prismatic/",
      "experiments/robot/",
      "vla-scripts/",
      "scripts/"
    ],
    "docs": [
      "README.md",
      "experiments/robot/aloha/README.md",
      "our_envs.txt"
    ],
    "examples_and_workflows": [
      "experiments/robot/libero/run_libero_eval.py",
      "vla-scripts/evaluate_calvin.py",
      "experiments/robot/server_deploy/deploy.py",
      "experiments/robot/aloha/run_fake_cobot_client.py",
      "experiments/robot/aloha/run_cobot_client.py",
      "experiments/robot/aloha/train_files/train_aloha.sh"
    ],
    "configs": [
      "pyproject.toml",
      "pretrained_models/configs/",
      "prismatic/conf/",
      "prismatic/vla/constants.py"
    ],
    "verification_candidates": [
      "eval_logs/",
      "experiments/robot/libero/sample_libero_spatial_observation.pkl"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If the current working tree is dirty and the dirty paths affect `prismatic/`,
  `vla-scripts/`, `scripts/`, `experiments/robot/`, `README.md`, or
  `pyproject.toml`, refresh before relying on workflow details.
- If package dependencies, robot constants, command-line dataclasses, checkpoint
  layout, or ALOHA deployment scripts changed, refresh even when the commit is
  close to this snapshot.
