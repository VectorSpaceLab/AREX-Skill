---
name: trl
description: "Use and modify TRL, the Hugging Face Transformers Reinforcement
  Learning library for post-training, CLI workflows, data/reward utilities,
  scaling backends, experimental environments, and repo development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TRL Repo Skill

Use this skill for TRL (Transformers Reinforcement Learning), a Hugging Face library for post-training foundation models with SFT, DPO, GRPO, reward modeling, RLOO, experimental RLHF methods, CLI launchers, dataset utilities, reward functions, and scaling integrations.

## Start Here

- Read [repo provenance](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.
- Read [installation and extras](references/installation-and-extras.md) when a task involves installing TRL, optional extras, Python versions, or import checks.
- Read [troubleshooting](references/troubleshooting.md) for cross-cutting install/import, optional dependency, CLI, data, backend, and repo-development failures.
- Run `scripts/check_trl_environment.py --help` when you need a safe local diagnostic helper; it checks imports, metadata, CLI help, and optional packages without training or downloads.

## Route by Task

- Use [core-training](sub-skills/core-training/SKILL.md) for stable trainer selection and API usage: `SFTTrainer`, `DPOTrainer`, `GRPOTrainer`, `RewardTrainer`, `RLOOTrainer`, and their configs.
- Use [data-and-rewards](sub-skills/data-and-rewards/SKILL.md) for dataset schemas, chat templates, multimodal messages, packing, prompt extraction, tool-call parsing, and built-in reward functions.
- Use [cli-and-configs](sub-skills/cli-and-configs/SKILL.md) for `trl` commands, YAML configs, dataset mixtures, `trl env`, `trl skills`, and command/config parser troubleshooting.
- Use [scaling-and-backends](sub-skills/scaling-and-backends/SKILL.md) for Accelerate, FSDP, DeepSpeed, PEFT, quantization, Liger, Unsloth, Kernels Hub, vLLM, memory planning, and optional backend diagnostics.
- Use [experimental-and-environments](sub-skills/experimental-and-environments/SKILL.md) for `trl.experimental`, experimental trainers, `GRPOTrainer(environment_factory=...)`, OpenEnv, OpenReward, Harbor, and tool-calling environment training.
- Use [repo-development](sub-skills/repo-development/SKILL.md) when modifying this repository: duplicated trainer logic, tests, docs, paper index updates, packaged skills, and contribution policy.

## Minimal Install and Import Check

Install the public package for normal use:

```bash
pip install trl
python - <<'PY'
import trl
from trl import SFTTrainer, DPOTrainer, GRPOTrainer, RewardTrainer
print('trl import ok')
PY
```

For source development, use an editable install from the checkout:

```bash
pip install -e .
trl --help
trl env
```

Install optional extras only when the selected workflow needs them. Examples include `trl[peft]` for adapter training, `trl[vllm]` for vLLM generation/server support, `trl[deepspeed]` for DeepSpeed, `trl[vlm]` for vision-language examples, `trl[openreward]` for OpenReward integration, and `trl[harbor]` for Harbor tasks. Avoid broad dev installs unless doing repository development.

## Common Workflow Routing

- **"Fine-tune a model with SFT/DPO/GRPO"**: start in `core-training`, then use `data-and-rewards` for dataset shape and `cli-and-configs` if the user wants a command or YAML file.
- **"My dataset columns or chat template are wrong"**: start in `data-and-rewards`; use its validator script before changing trainer code.
- **"Generate a `trl sft` or `trl grpo` command"**: start in `cli-and-configs`, then cross-check trainer semantics in `core-training`.
- **"Use vLLM, DeepSpeed, FSDP, LoRA, quantization, or Unsloth"**: start in `scaling-and-backends`; do not start servers or training jobs unless the user asked and prerequisites are available.
- **"Train with tools, OpenEnv, OpenReward, or Harbor"**: start in `experimental-and-environments`; verify extras, services, credentials, and stability warnings.
- **"Edit TRL internals"**: start in `repo-development`; maintain duplicated trainer logic consistency and update `docs/source/paper_index.md` for paper-backed methods.

## Safety and Validation

- Prefer read-only checks first: imports, `trl --help`, config rendering, dataset validation, and optional backend diagnostics.
- Treat examples, notebooks, long training runs, vLLM servers, Docker/sandbox tasks, and distributed jobs as expensive or environment-dependent unless explicitly requested.
- Do not assume optional dependencies are installed because the base package imports.
- Keep trainer changes consistent across duplicated blocks when editing the repository.
- Use focused tests for changed areas; skip invariant, distributed, service, GPU, or long-running candidates unless they match the change and the environment supports them.
