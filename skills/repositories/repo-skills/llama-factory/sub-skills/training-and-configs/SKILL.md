---
name: training-and-configs
description: "Use for LlamaFactory v0 training runs, config files, CLI
  overrides, preprocessing, distributed launch variables, experiment logging,
  and training-time diagnostics. Covers llamafactory-cli train/lmf train for
  SFT, PT, DPO, PPO, RM, KTO, ORPO, and SimPO-style preference training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Configs

Use this sub-skill when the user needs to start, modify, audit, or debug a LlamaFactory training job with `llamafactory-cli train` or `lmf train`.

## Route Here

- Training stages: `stage: sft`, `pt`, `dpo`, `ppo`, `rm`, or `kto`; ORPO and SimPO are DPO-stage variants selected with `pref_loss: orpo` or `pref_loss: simpo`.
- Config mechanics: YAML/JSON train configs, CLI overrides, parse errors, unknown args, safe dry planning, and command rendering.
- Fine-tuning choices: `finetuning_type: lora`, `oft`, `freeze`, or `full`, including LoRA/QLoRA restrictions and optimizer add-ons.
- Runtime orchestration: `FORCE_TORCHRUN`, multi-node `torchrun`, DeepSpeed config selection, Ray opt-in, preprocess-only tokenized datasets, and logging integrations.

## Route Elsewhere

- Dataset registration, `dataset_info.json`, data formats, templates, packing semantics, or multimodal media schemas: use `data-and-templates`.
- Model loading internals, adapter merge, model export, or quantized export: use `model-loading-and-export`.
- Chat, API serving, Web UI inference, vLLM, SGLang, or prediction-only configs: use `inference-and-serving`.
- `USE_V1=1` trainer architecture or v1-only YAML shape: use `v1-experimental`.

## Start With

1. Identify whether the requested flow is training, preprocessing, or diagnostics; never run model downloads or training unless the user explicitly asks.
2. Read `references/training-workflows.md` for stage-specific command/config patterns.
3. Read `references/configuration.md` before changing YAML/JSON or CLI overrides.
4. Read `references/distributed-and-logging.md` for multi-GPU, multi-node, Ray, DeepSpeed, FSDP, and tracker settings.
5. Read `references/troubleshooting.md` for common parser, quantization, dependency, memory, distributed, and logging failures.

## Bundled Helpers

- `scripts/render_train_command.py` renders a safe `llamafactory-cli train` command from a YAML/JSON config and optional overrides without importing LlamaFactory.
- `scripts/eval_bleu_rouge.py` computes dependency-free approximate BLEU/ROUGE-style metrics for JSON/JSONL prediction files with `predict` and `label` fields.

## Safety

- Treat example model ids and dataset names as templates, not permission to download or train.
- Prefer `report_to: none`, small `max_samples`, and `max_steps: 1` when proposing smoke tests.
- Keep secrets out of configs; use environment variables for tracker tokens and hub credentials.
