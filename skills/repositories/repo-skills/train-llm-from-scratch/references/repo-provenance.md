# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T16:00:00Z",
  "repository": {
    "name": "train-llm-from-scratch",
    "remote_url": "https://github.com/FareedKhan-dev/train-llm-from-scratch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "98f808c4ea9c4e83e16050358e80288642d0cd80",
    "working_tree": "dirty-generated-skill-output-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "train-llm-from-scratch",
      "version": "0.1.0",
      "import_names": [
        "config",
        "data_loader",
        "src",
        "ui"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/models",
      "src/post_training",
      "data_loader",
      "config",
      "ui"
    ],
    "docs": [
      "README.md",
      "POST_TRAINING.md",
      "docs",
      "mkdocs.yml"
    ],
    "scripts": [
      "scripts/prepare_pretrain_data.py",
      "scripts/prepare_sft_data.py",
      "scripts/prepare_preference_data.py",
      "scripts/prepare_rl_prompts.py",
      "scripts/train_transformer.py",
      "scripts/pretrain_base.py",
      "scripts/train_sft.py",
      "scripts/train_reward.py",
      "scripts/train_dpo.py",
      "scripts/train_ppo.py",
      "scripts/train_grpo.py",
      "scripts/eval_post_training.py",
      "scripts/chat.py",
      "scripts/run_posttraining.sh"
    ],
    "tests": [
      "tests/test_post_training_smoke.py",
      "tests/test_rl_math.py",
      "tests/test_checkpoint_resume.py",
      "tests/verify_data_and_eval.py",
      "tests/verify_rl_optimizes.py",
      "tests/grpo_live.py",
      "tests/gpu_verify.sh"
    ],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      "requirements-post.txt",
      "configs",
      "configs/smoke"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If dirty paths include source, docs, scripts, tests, configs, or package
  metadata beyond generated `skills/` outputs, run `refresh-repo-skill`.
- If package metadata, public entry points, config fields, script flags, or
  checkpoint formats changed even on the same commit, run `refresh-repo-skill`.
- If a future checkout removes or substantially rewrites the post-training suite
  (`src/post_training`, `scripts/train_*.py`, `configs/*.json`), do not rely on
  this skill without refreshing.
