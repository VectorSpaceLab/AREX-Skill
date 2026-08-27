---
name: xtuner
description: "Use XTuner for large-model SFT, pretraining, MLLM fine-tuning,
  data preparation, model/backend configuration, RL/GRPO post-training, and
  legacy XTuner tooling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XTuner repo skill

Use this root skill when a task names XTuner or asks for operating guidance around XTuner V1 large-model training, data preparation, MoE/model backend choices, GRPO/RL post-training, or legacy XTuner utilities.

XTuner V1 is a PyTorch-based training engine aimed at large dense, MoE, and multimodal models. Most real training/RL work needs accelerator resources, model/data assets, and optional backend packages. This generated skill gives safe command builders, validators, and routing guidance; it does not require the original source checkout.

## Start here

1. **Check the package and backend surface.** Read [references/package-and-environment.md](references/package-and-environment.md), then run [scripts/check_xtuner_install.py](scripts/check_xtuner_install.py) in the user's XTuner environment.
2. **Route to the right workflow.** Use the sub-skill map below. Do not mix V1 direct CLIs with the old legacy `xtuner MODE ...` router.
3. **Validate data before training.** Use `data-preparation` for SFT, MLLM, and RL JSONL schemas before building training or RL launch commands.
4. **Treat accelerator checks as real gates.** CPU imports and synthetic cases do not prove CUDA/NPU/FP8/Ray rollout execution. Use [references/native-verification.md](references/native-verification.md) before claiming backend success.
5. **Use troubleshooting early.** Cross-cutting install/import/backend failures are in [references/troubleshooting.md](references/troubleshooting.md); workflow-specific failures live in each sub-skill.

## Sub-skill routes

| Task signal | Read |
|---|---|
| V1 SFT, pretraining, MLLM fine-tuning, `TrainingArguments`, `TrainerConfig`, `torchrun`, FSDP/checkpoint/resume, training logs | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) |
| SFT/MLLM/RL JSONL validation, media paths, chat templates, tokenizer configs, dataset caching, packing, GSM8K conversion | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Dense/MoE/VLM model configs, `get_model_config`, FSDP/TP/EP/HSDP, attention/router/dispatcher, FP8, CUDA/NPU optional backends | [sub-skills/model-backends/SKILL.md](sub-skills/model-backends/SKILL.md) |
| RL/GRPO launch planning, Ray resources, rollout engines, agent loops, judgers, reward data, replay buffers, evaluation, traces | [sub-skills/reinforcement-learning/SKILL.md](sub-skills/reinforcement-learning/SKILL.md) |
| Legacy `xtuner MODE ...`, old config-zoo search/copy, model conversion planning, chat/eval/preprocess tools, HF Trainer examples | [sub-skills/cli-and-tools/SKILL.md](sub-skills/cli-and-tools/SKILL.md) |

## Package facts to remember

- Public package/distribution name: `xtuner`.
- Source snapshot used for this skill: see [references/repo-provenance.md](references/repo-provenance.md).
- Python requirement from package metadata: `>=3.10`.
- Verified package version in the construction environment: `0.2.0`.
- V1 installed-package entry points used by generated helpers:
  - SFT/training: `python -m xtuner.v1.train.cli.sft ...`
  - RL: `python -m xtuner.v1.train.cli.rl ...`
- Optional RL support uses Ray plus a rollout backend such as LMDeploy, SGLang, or vLLM.
- Optional acceleration surfaces include FlashAttention, bitsandbytes quantization, GroupedGEMM, AdaptiveGEMM, FP8 kernels, DeepEP, and NPU/vendor stacks. Verify these in the target environment before relying on them.

## Minimal install and smoke check

Use the package/environment reference for details. A typical installed-package check is:

```bash
python -m pip install xtuner
python scripts/check_xtuner_install.py --json
python -m xtuner.v1.train.cli.sft --help
```

For RL planning, install Ray and a chosen rollout backend in the target environment, then check:

```bash
python -m xtuner.v1.train.cli.rl --help
```

If `python -m xtuner.v1.train.cli.sft --help` prints warnings about missing FlashAttention or bitsandbytes CUDA binaries but still exits successfully, treat those as optional acceleration limitations unless the user explicitly needs that feature.

## Guardrails

- Do not launch training, Ray clusters, model downloads, benchmark evaluation, or model conversion unless the user supplies assets/resources and approves side effects.
- Do not claim GPU/NPU/FP8/backend verification from CPU imports alone.
- Do not ask future agents to open or run original repository docs, examples, tests, configs, or scripts. Use the generated references and bundled helper scripts here.
- For source checkout freshness, compare the current checkout to [references/repo-provenance.md](references/repo-provenance.md); run `refresh-repo-skill` when it diverges.
