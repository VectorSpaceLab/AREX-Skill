# Testing and Maintenance Guide

## Fast Sanity and Focused Tests

Use the smallest check set that exercises the changed area before considering broader CI parity.

- Import/package smoke: `pytest tests/special_sanity/test_import.py`.
- Config documentation consistency: `pytest tests/special_sanity/test_config_docs.py`.
- Base config CPU behavior: `pytest tests/test_base_config_on_cpu.py`.
- Path-specific unit tests: prefer matching `tests/<area>/test_*.py` files for the touched `verl/<area>/` code.
- CPU-only tests are identified by filenames ending in `_on_cpu.py` and are suitable for non-accelerator environments.
- GPU tests are the default for test files without `_on_cpu.py`, except NPU-specific tests and special categories.
- NPU tests live under `tests/special_npu` or use names containing `_on_npu.py`; only suggest them for Ascend/NPU-related changes.

`tests/README.md` describes CI layout: `special_sanity` contains quick checks; `special_distributed` needs multiple GPUs; `special_e2e` covers training/generation scripts; `special_npu` targets NPUs; `special_standalone` expects dedicated environments.

## Pre-commit Hooks

The repository pre-commit configuration includes:

- `ruff` and `ruff-format` from `ruff-pre-commit`; ruff uses line length 120 and lint families `E`, `F`, `UP`, `B`, `I`, and `G` with project-specific ignores.
- `mypy`, but project configuration currently has blanket `ignore_errors = true` with selected stricter modules under trainer PPO/reward areas.
- Local hooks for trainer config autogeneration, docs time info, docstrings, license, device API usage, DataProto usage, structure validation, naming conventions, example naming, and compileall.

Useful command patterns:

```bash
pre-commit run --all-files --show-diff-on-failure --color=always ruff
pre-commit run --all-files --show-diff-on-failure --color=always ruff-format
pre-commit run --all-files --show-diff-on-failure --color=always autogen-trainer-cfg
```

Run narrower hooks first when possible; broad `--all-files` checks can be expensive.

## Generated Trainer Configs

Trainer reference configs are generated, not hand-authored. The pre-commit hook `autogen-trainer-cfg` invokes the repo script that writes:

- `verl/trainer/config/_generated_ppo_trainer.yaml`
- `verl/trainer/config/_generated_ppo_megatron_trainer.yaml`
- `verl/trainer/config/_generated_ppo_veomni_trainer.yaml`
- `verl/trainer/config/_generated_ppo_torchtitan_trainer.yaml`

The source script flattens `verl/trainer/config/ppo_trainer.yaml` using `scripts/print_cfg.py --cfg job` plus model-engine overrides, then verifies that generated outputs have no uncommitted diff. Because this mutates generated YAML, only run it intentionally and commit the regenerated files with the source config/docs change.

## CI Workflow Selection

When adding or moving tests, check workflow path filters and exclusions so tests are not run twice or missed:

- `cpu_unit_tests.yml` targets `tests/**/test_*_on_cpu.py`.
- `gpu_unit_tests.yml` targets test files that do not use the `_on_cpu.py` suffix.
- NPU/Ascend workflows cover NPU-specific tests and backend-specific e2e coverage.
- Heavy model, vLLM, SGLang, distributed, and e2e workflows should be selected only when the touched code needs those integrations.

Use the bundled `scripts/select_verl_tests.py` helper to get a first-pass suggestion from changed paths, then refine with code ownership and dependency knowledge.
