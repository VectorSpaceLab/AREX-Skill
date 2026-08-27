---
name: axolotl
description: "Routes agents working with Axolotl config-driven LLM fine-tuning,
  datasets, SFT, preference tuning, GRPO/EBFT, model adapters, distributed
  training, CLI operations, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Axolotl

Use this repo skill when the user asks about Axolotl, `axolotl` CLI commands, Axolotl YAML configs, LLM fine-tuning recipes, dataset/preprocess issues, LoRA/QLoRA, preference tuning, GRPO/EBFT, vLLM-assisted training, model architecture support, DeepSpeed/FSDP/Ray scaling, or Axolotl-specific troubleshooting.

Axolotl is config-driven: a single YAML config selects the base model, adapter/training method, datasets, preprocessing, launch/runtime settings, and output paths.

## Start Here

1. Identify the user’s primary task family before editing YAML.
2. Read the nearest sub-skill route below, then only open deeper references as needed.
3. Prefer safe static helpers first; run `axolotl preprocess <config> --debug` only in the user’s Axolotl environment when tokenizer/model access and runtime cost are acceptable.
4. Treat bundled helper scripts as triage tools, not replacements for Axolotl’s installed `config-schema`, `preprocess`, or training runtime.
5. Read [references/repo-provenance.md](references/repo-provenance.md) before judging whether this skill matches a current Axolotl checkout.

## Route By Task

| User task | Read |
| --- | --- |
| Write or debug YAML config structure, dataset columns, `chat_template`, prompt strategies, preprocessing, sample packing, or schema issues | [data-and-configs](sub-skills/data-and-configs/SKILL.md) |
| Build SFT, LoRA/QLoRA, full fine-tune, or continual pretraining recipes; diagnose SFT/pretraining loss, OOM, checkpoint, or resume issues | [sft-and-pretraining](sub-skills/sft-and-pretraining/SKILL.md) |
| Configure DPO, IPO, KTO, ORPO, SimPO, reward model, process reward model, paired/unpaired preference data, or preference loss settings | [preference-tuning](sub-skills/preference-tuning/SKILL.md) |
| Configure GRPO, EBFT, custom reward functions, vLLM rollout servers, async online RL, NeMo Gym, or Hatchery reward hooks | [rl-and-rewards](sub-skills/rl-and-rewards/SKILL.md) |
| Choose base models, tokenizers/processors, chat templates, LoRA targets, QLoRA, quantization/QAT/PTQ, multimodal settings, architecture quirks, or new model support | [model-loading-and-adapters](sub-skills/model-loading-and-adapters/SKILL.md) |
| Configure DeepSpeed, FSDP, Ray, SLURM/multi-node, tensor/context/sequence/expert parallelism, precision, kernels, profiling, or performance troubleshooting | [distributed-and-performance](sub-skills/distributed-and-performance/SKILL.md) |
| Use `axolotl` commands, launchers, `agent-docs`, `config-schema`, `fetch`, `inference`, `evaluate`, `merge-lora`, `vllm-serve`, `quantize`, install checks, or command construction | [cli-and-operations](sub-skills/cli-and-operations/SKILL.md) |

## Common Entry Points

- `axolotl preprocess config.yaml --debug` checks rendered/tokenized samples and label masking before expensive training.
- `axolotl train config.yaml` launches training; use `--launcher torchrun`, `--launcher accelerate`, or `--launcher python` deliberately.
- `axolotl inference config.yaml`, `axolotl merge-lora config.yaml`, `axolotl evaluate config.yaml`, `axolotl vllm-serve config.yaml`, and `axolotl quantize config.yaml` are operational routes covered by `cli-and-operations`.
- `axolotl agent-docs --list`, `axolotl agent-docs <topic>`, and `axolotl config-schema --field <field>` are preferred installed-package truth checks when available.

## Cross-Cutting Helpers

- [references/troubleshooting.md](references/troubleshooting.md) covers install/import, optional dependency, config-first triage, hardware/backend, and workflow-routing symptoms.
- [scripts/check_axolotl_environment.py](scripts/check_axolotl_environment.py) performs a safe package/CLI/schema availability check without loading models or starting training.

## Routing Notes

- Reward-model and process-reward-model training belong to `preference-tuning`; callable reward functions for GRPO/EBFT belong to `rl-and-rewards`.
- Config validation usually starts in `data-and-configs`, then narrows to method/model/distributed/CLI-specific static helpers, then escalates to `axolotl config-schema` or `axolotl preprocess` in the user’s runtime.
- Model downloads, gated repositories, GPU kernels, vLLM services, distributed launchers, and long training runs require user environment readiness and should not be inferred from static helper success.

## Refresh Guidance

Run `refresh-repo-skill` when the Axolotl commit, package version, CLI entry points, config schema, docs, examples, or training APIs have changed relative to [references/repo-provenance.md](references/repo-provenance.md).
