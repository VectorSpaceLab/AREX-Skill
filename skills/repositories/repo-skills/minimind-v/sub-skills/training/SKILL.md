---
name: training
description: "Guides MiniMind-V Pretrain and SFT command planning, DDP launch,
  freezing, checkpoint/resume, precision, logging, prerequisites, and output
  naming."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MiniMind-V Training

Use this sub-skill when the task is to plan, configure, resume, or safely construct commands for MiniMind-V VLM Pretrain or SFT training.

Do not run full training as a default verification step. MiniMind-V training is GPU-, data-, and weight-gated; build commands, check prerequisites, and ask before launching any expensive training job.

## Route here

- Choosing between optional Pretrain and SFT-first training.
- Constructing single-GPU or DDP `torchrun` commands from a MiniMind-V checkout.
- Setting `freeze_llm`, `from_weight`, `from_resume`, precision, logging, and checkpoint options.
- Understanding output weight names, resume state, and GPU-count-change resume behavior.
- Troubleshooting missing weights/data, CUDA/OOM, tokenizer/model resources, DDP ranks, checkpoint mismatch, logging, or `torch.compile`.

## Route elsewhere

- Parquet schema or resource downloads: `data-and-resources`.
- Model internals or SigLIP2 architecture: `model-architecture-and-api`.
- Inference, evaluation, WebUI, or serving: `inference-and-serving`.
- Post-training conversion to Transformers: `model-export-and-format-conversion`.

## Operating workflow

1. Identify the desired stage: `sft` for the recommended main path or `pretrain` for optional projector alignment before SFT.
2. Confirm prerequisites without downloading them: parquet data, base/previous-stage weights, tokenizer files, and SigLIP2.
3. Use [`build_training_command.py`](scripts/build_training_command.py) for safe planning; it prints commands and optional file-check results but never launches training.
4. Read [training workflows](references/training-workflows.md), [CLI reference](references/cli-reference.md), [checkpoints and resume](references/checkpoints-and-resume.md), and [troubleshooting](references/troubleshooting.md).

## Key defaults

- Pretrain: `save_weight=pretrain_vlm`, `batch_size=16`, `learning_rate=4e-4`, `max_seq_len=450`, `data_path=../dataset/pretrain_i2t.parquet`, `from_weight=llm`, `freeze_llm=2`.
- SFT: `save_weight=sft_vlm`, `batch_size=4`, `learning_rate=5e-6`, `max_seq_len=768`, `data_path=../dataset/sft_i2t.parquet`, `from_weight=pretrain_vlm`, `freeze_llm=1`.
- To skip Pretrain, use SFT with `--from_weight llm` because the SFT parquet already includes the Pretrain caption subset.
