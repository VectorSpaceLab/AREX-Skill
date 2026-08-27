# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an EasyR1 checkout. If the current commit, package version, public config/API surface, examples, or dirty state differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:56:33Z",
  "repository": {
    "name": "EasyR1",
    "remote_url": "https://github.com/hiyouga/EasyR1.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b44b311b669bf1fd1aa2fc36f2251482ba33cb16",
    "working_tree": "dirty-after-generation",
    "dirty_paths": [
      "skills/"
    ],
    "source_state_note": "The source checkout was clean before skill files and review artifacts were generated under skills/."
  },
  "packages": [
    {
      "name": "verl",
      "version": "0.3.3.dev0",
      "import_names": ["verl"]
    }
  ],
  "evidence": {
    "source_roots": ["verl/"],
    "docs": ["README.md", "assets/baselines.md"],
    "examples": [
      "examples/config.yaml",
      "examples/*.sh",
      "examples/baselines/*.sh",
      "examples/format_prompt/",
      "examples/reward_function/",
      "examples/android_gui_cookbook/"
    ],
    "scripts": ["scripts/model_merger.py"],
    "tests": [
      "tests/test_dataproto.py",
      "tests/test_dynamic_batch.py",
      "tests/test_checkpoint.py",
      "tests/test_model_merger.py",
      "tests/test_dataset.py"
    ],
    "package_metadata": ["pyproject.toml", "setup.py", "requirements.txt", ".github/requirements-test.txt", ".github/workflows/tests.yml"],
    "configs": ["examples/config.yaml"]
  },
  "verification_baseline": {
    "cpu_api_imports": [
      "verl",
      "verl.protocol",
      "verl.trainer.core_algos",
      "verl.utils.dataset",
      "verl.utils.checkpoint",
      "verl.workers.reward.function"
    ],
    "cuda_smoke": "PyTorch CUDA allocation succeeded on NVIDIA A100 host during construction.",
    "full_training_backend": "Not fully verified; flash-attn/vLLM training runtime should be verified in an EasyR1-compatible container or provisioned CUDA environment before native full examples are claimed."
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current package version or import package changes from `verl 0.3.3.dev0`, refresh the skill.
- If `examples/config.yaml`, training shell recipes, reward examples, `scripts/model_merger.py`, or public `verl/` APIs change materially, refresh the skill.
- If a future environment fully verifies vLLM/flash-attn training examples that were not verified here, refresh or extend the verification artifacts before import.
