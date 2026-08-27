---
name: training-and-configs
description: "Assemble verl PPO, GRPO, SFT, and on-policy distillation training
  commands, Hydra overrides, backend strategy switches, and config
  troubleshooting guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-and-configs

Use this sub-skill when a coding agent needs to build or debug verl training commands and Hydra config overrides for PPO-like RL, GRPO, SFT, or on-policy distillation.

## Route by Task

- **PPO / critic training**: Use `references/training-workflows.md` for the `python -m verl.trainer.main_ppo` command shape, required actor/critic/model/data/logger overrides, and FSDP or Megatron examples.
- **GRPO / critic-less RL**: Use `references/training-workflows.md` for `algorithm.adv_estimator=grpo`, grouped rollout `n`, KL-loss settings, and no-critic command patterns.
- **SFT**: Use `references/training-workflows.md` for `torchrun -m verl.trainer.sft_trainer`, `engine=fsdp`, dataset message keys, LoRA/PEFT, and sequence-parallel switches.
- **On-policy distillation**: Use `references/training-workflows.md` for `distillation.enabled=True`, teacher resource sizing, teacher model overrides, and distillation loss modes.
- **Hydra and backend switches**: Use `references/configuration.md` before changing `model_engine`, FSDP/FSDP2, Megatron, VeOmni, TorchTitan, rollout backend, batch, checkpoint, logger, or generated-reference config fields.
- **Failures and validation errors**: Use `references/troubleshooting.md` for overlong prompts, OOM, Hydra override syntax, config-doc CI, rollout backend mismatch, Ray/GPU resource, and distillation teacher sizing problems.

## Bundled Tool

- `scripts/build_ppo_command.py` assembles a dry-run `python -m verl.trainer.main_ppo` command from common data, model, rollout, backend, batch, and logger options. It prints only; it never imports verl, starts Ray, downloads models, or runs training.

## Boundaries

- Dataset schema details, reward/tool internals, backend installation, and checkpoint merge/export operations belong to other verl sub-skills or repo-level references.
- Do not point future agents at source checkout examples or scripts as runtime dependencies; adapt their patterns into commands or use the bundled script here.
