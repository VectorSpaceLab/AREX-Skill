---
name: verl
description: "Use verl for LLM post-training workflows: setup, data and rewards,
  PPO/GRPO/SFT configs, rollout tools, checkpoints, profiling, and repository
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# verl

Use this repo skill when a user asks how to install, configure, run, debug, or maintain `verl`, the Volcano Engine Reinforcement Learning library for LLM post-training.

## Start Here

- Read `references/repo-provenance.md` before relying on this skill for a different checkout or after package metadata, config files, examples, or docs change.
- Read `references/troubleshooting.md` for cross-cutting failures that span setup, Hydra configs, data schema, rollout backends, checkpoint operations, and repo maintenance.
- Run `scripts/check_skill_integrity.py` when editing or importing this skill to check frontmatter, links, private-path leaks, and generated cache files.

## Route By User Task

- **Install or verify an environment**: use `sub-skills/setup-and-backends/` for base install choices, Docker-vs-custom setup, Python/CUDA requirements, optional extras, vLLM/SGLang/Megatron/TensorRT-LLM/NPU/ROCm caveats, and safe import/backend checks.
- **Prepare or validate data and rewards**: use `sub-skills/data-and-rewards/` for parquet row schemas, chat prompt fields, `reward_model.ground_truth`, custom reward modules, and the bundled parquet validator.
- **Build training commands and Hydra overrides**: use `sub-skills/training-and-configs/` for PPO, GRPO, SFT, on-policy distillation, backend strategy switches, batch/micro-batch sizing, generated config references, and the dry-run PPO command builder.
- **Configure rollout, agent loops, and tools**: use `sub-skills/rollout-and-tools/` for rollout engines, async generation server flows, multi-turn agent loops, `@function_tool`, native `BaseTool`, tokenization sanity checks, traces, and tool schema validation.
- **Operate checkpoints and model artifacts**: use `sub-skills/checkpoints-and-model-ops/` for checkpoint layout inspection, `verl.model_merger`, FSDP/Megatron/HuggingFace export decisions, LoRA merge implications, profiling, and performance diagnostics.
- **Maintain the repository**: use `sub-skills/repo-development/` for contribution policy, duplicate-work checks, AGENTS.md editing rules, generated trainer config maintenance, focused test selection, and non-executing test suggestions.

## Common Decision Points

- If the user says “training fails,” first classify the failure: installation/import (`setup-and-backends`), parquet/reward schema (`data-and-rewards`), Hydra override/resource sizing (`training-and-configs`), rollout backend/tooling (`rollout-and-tools`), or checkpoint/export (`checkpoints-and-model-ops`).
- If the user asks for a command, prefer the nearest bundled command builder or validator; never require the original source checkout examples to remain available.
- If the user asks for GPU execution, distinguish a base Python import check from real accelerator runtime validation. vLLM, SGLang, Megatron, flash-attn, TensorRT-LLM, ROCm, and NPU stacks need backend-specific environments.
- If the user is editing the repo, apply `repo-development` before changing files so duplicate-work, AGENTS.md scope, generated config, and focused-test rules are not missed.

## Bundled Helpers

- `sub-skills/setup-and-backends/scripts/check_verl_environment.py` checks active Python package metadata, imports, optional CUDA state, and dependency consistency.
- `sub-skills/data-and-rewards/scripts/validate_verl_parquet.py` validates verl parquet rows without importing `verl`.
- `sub-skills/training-and-configs/scripts/build_ppo_command.py` prints a dry-run `python -m verl.trainer.main_ppo` command from common arguments.
- `sub-skills/rollout-and-tools/scripts/validate_function_tool.py` preflights trusted function-tool Python files for type hints and Google-style `Args:` docs.
- `sub-skills/checkpoints-and-model-ops/scripts/inspect_checkpoint_path.py` classifies checkpoint/run/role directories without loading tensors.
- `sub-skills/repo-development/scripts/select_verl_tests.py` maps changed paths to suggested tests and pre-commit hooks without running them.

## Safety Rules

- Do not run training, dataset downloads, Docker builds, GPU/NPU jobs, checkpoint merges, or source-mutating maintenance scripts unless the user explicitly asks and the environment is appropriate.
- Treat original repo docs, examples, scripts, and tests as evidence only. Runtime guidance in this skill is self-contained and should use bundled references/scripts.
- Do not leak local checkout paths, private Python prefixes, cache paths, credentials, or machine-specific install commands into public skill content.
- For native verification, prefer CPU-safe tests and help/parser checks first; record GPU/NPU/e2e examples as skipped unless the user authorizes heavy hardware runs.
