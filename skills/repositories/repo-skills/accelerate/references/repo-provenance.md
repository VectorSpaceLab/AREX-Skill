# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Hugging Face Accelerate. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "accelerate",
    "remote_url": "https://github.com/huggingface/accelerate",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "fb77442677c85f6ebcd7a226588f60046cd6b301",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "accelerate",
      "version": "1.15.0.dev0",
      "import_names": ["accelerate"]
    }
  ],
  "entry_points": [
    "accelerate=accelerate.commands.accelerate_cli:main",
    "accelerate-config=accelerate.commands.config:main",
    "accelerate-estimate-memory=accelerate.commands.estimate:main",
    "accelerate-launch=accelerate.commands.launch:main",
    "accelerate-merge-weights=accelerate.commands.merge:main"
  ],
  "evidence": {
    "source_roots": ["src/accelerate"],
    "docs": [
      "README.md",
      "docs/source/basic_tutorials",
      "docs/source/package_reference",
      "docs/source/usage_guides",
      "docs/source/concept_guides"
    ],
    "examples": [
      "examples/by_feature",
      "examples/config_yaml_templates",
      "examples/deepspeed_config_templates",
      "examples/inference",
      "examples/slurm",
      "examples/torch_native_parallelism"
    ],
    "tests": [
      "tests/test_cli.py",
      "tests/test_launch.py",
      "tests/test_accelerator.py",
      "tests/test_data_loader.py",
      "tests/test_grad_sync.py",
      "tests/test_state_checkpointing.py",
      "tests/test_tracking.py",
      "tests/test_big_modeling.py",
      "tests/test_modeling_utils.py",
      "tests/test_offload.py",
      "tests/deepspeed",
      "tests/fsdp",
      "tests/tp"
    ],
    "configs": [
      "tests/test_configs",
      "examples/config_yaml_templates",
      "examples/deepspeed_config_templates"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the working tree changes in package source, docs, examples, tests, configs, or entry point metadata, run `refresh-skill-from-repo`.
- If package metadata or public console scripts change even on the same commit, refresh this skill.
- The recorded dirty path is the generated DisCo output under `skills/`; unrelated dirty source/docs/test paths should be treated as a staleness signal.
