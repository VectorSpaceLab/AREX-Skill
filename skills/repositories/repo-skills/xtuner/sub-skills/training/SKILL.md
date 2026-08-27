---
name: training
description: "Plan and troubleshoot XTuner V1 SFT, pretraining, and multimodal
  fine-tuning launches with CLI or Python configs, torchrun resources, FSDP,
  checkpoints, resume, profiling, and log interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XTuner Training

Use this sub-skill when a task is about launching, configuring, or diagnosing XTuner V1 supervised fine-tuning, pretraining, or multimodal SFT. It is optimized for future agents that need to choose between direct SFT CLI arguments and Python config files, build `torchrun` commands safely, reason about `TrainerConfig` / `TrainingArguments`, and interpret XTuner training logs.

## Route here when

- The user wants an XTuner V1 SFT or pretraining launch command.
- The user needs to decide between direct CLI arguments and `--config <python_config.py>`.
- The user is tuning `TrainerConfig`, `TrainingArguments`, optimizer, LR scheduler, loss, FSDP, checkpoint, resume, profiling, or work directory settings.
- The user has XTuner training logs and asks whether loss, throughput, memory, data loading, or checkpoint/resume behavior looks healthy.
- The user is fine-tuning a multimodal model and the question is about training orchestration rather than JSONL/media schema details.

## Route elsewhere

- JSONL schema, media paths, tokenization functions, packing internals, dataset validation, and cache invalidation details belong to `data-preparation`.
- MoE routing, FP8 kernels, attention backends, GroupedGEMM/AdaptiveGEMM, tensor/expert parallel internals, and model-family selection belong to `model-backends`.
- GRPO, DAPO, Ray, rollout engines, reward functions, and RL trainer launches belong to `reinforcement-learning`.
- Legacy `xtuner train`, config-zoo discovery, model conversion, chat, eval, and old tools belong to `cli-and-tools`.

## Fast operating procedure

1. **Identify the launch mode.** Direct CLI arguments are for simple SFT/pretraining-style runs where paths and a few knobs change. Python config files are required for MLLM examples, pretraining recipes, custom datasets/tokenizers, explicit resume/checkpoint paths, profiler hooks, or deeper `TrainerConfig` control. See [references/workflows.md](references/workflows.md).
2. **Validate mutually exclusive inputs.** XTuner V1 `sft.py` accepts either `--config` or direct `TrainingArguments`, not both. Mixing them raises `ValueError: Cannot specify both \`config\` and \`arguments\`.`
3. **Build commands with the bundled helper.** Use [scripts/build_sft_command.py](scripts/build_sft_command.py) to assemble a dry `torchrun -m xtuner.v1.train.cli.sft ...` command without relying on any source checkout.
4. **Check path assumptions before launch.** Direct mode needs a dataset JSONL/file/dir/glob and either `--load-from` or `--model-cfg`. If `--tokenizer-path` is omitted, `--load-from` must resolve as a Hugging Face model snapshot directory or model id; a local snapshot should contain `config.json`.
5. **Choose resource knobs deliberately.** Set `--nproc-per-node`, node rank, master address/port, FSDP `tp_size`/`ep_size`, CPU offload, recompute ratio, and global batch size together. World size must be compatible with the parallel mesh. See [references/api-reference.md](references/api-reference.md).
6. **Inspect logs early.** XTuner step lines report `data_time`, `time`, tokens, loss, memory, `grad_norm`, throughput (`tgs`, `seqlen_tgs`, `exp_tgs`), and ETA. Use [scripts/summarize_xtuner_log.py](scripts/summarize_xtuner_log.py) for a quick run summary and warning triage.
7. **Troubleshoot by symptom.** For config/direct conflicts, missing HF snapshots, dataset glob misses, flash-attn fallback, bitsandbytes CUDA warnings, OOM, FSDP size mismatches, and resume/checkpoint problems, use [references/troubleshooting.md](references/troubleshooting.md).

## Minimal examples

Build a direct Qwen3 SFT command for an OpenAI-format JSONL:

```bash
python sub-skills/training/scripts/build_sft_command.py \
  --nproc-per-node 8 \
  --load-from /models/Qwen3-8B/snapshots/<revision> \
  --chat-template qwen3 \
  --dataset /data/train.jsonl \
  --total-step 100 \
  --work-dir /runs/qwen3-sft
```

Summarize a work directory or torchrun log file:

```bash
python sub-skills/training/scripts/summarize_xtuner_log.py /runs/qwen3-sft
```

Keep commands, logs, and user-provided model/data paths in the user's environment. This skill tree does not require or link to an XTuner source checkout.
