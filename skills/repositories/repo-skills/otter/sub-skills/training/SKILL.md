---
name: training
description: "Guide Otter SFT, pretraining, OtterHD/Fuyu finetuning, and safe
  Accelerate/DeepSpeed training command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Otter training sub-skill

Use this sub-skill when the task is to plan or construct Otter training commands: supervised instruction tuning, OtterHD/Fuyu finetuning, MMC4/LAION/CC3M pretraining, Accelerate/DeepSpeed launch setup, data-YAML handoff, logging, checkpoint, offline, and resource choices.

## Fast route

1. Select the workflow in [training-workflows](references/training-workflows.md):
   - SFT / instruction tuning: `pipeline/train/instruction_following.py` with a MIMIC-IT-style `--training_data_yaml`.
   - OtterHD / Fuyu finetuning: the same SFT script with `--model_name=fuyu`, `--instruction_format=fuyu`, and Fuyu resource warnings.
   - Pretraining: see [pretraining](references/pretraining.md) for MMC4+LAION or CC3M shard workflows.
2. Select a launch config in [accelerate-and-deepspeed](references/accelerate-and-deepspeed.md). The documented SFT example uses ZeRO-3; the documented OtterHD/Fuyu example uses ZeRO-2.
3. Generate a command without launching training:

```bash
python scripts/build_training_command.py --help
```

4. Before any expensive run, check [troubleshooting](references/troubleshooting.md) for GPU memory, Flash-Attention/fused-operator, W&B/offline, checkpoint, and YAML-validation issues.

## Route elsewhere

- MIMIC-IT schema design, validation, conversion, Syphus, and image/parquet preparation: [data-preparation](../data-preparation/SKILL.md).
- Inference, generation, prompt/media tensors, and checkpoint conversion for use at inference time: [model-inference](../model-inference/SKILL.md).
- Benchmark evaluation and benchmark YAMLs: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).
- Controller/worker/Gradio/API serving: [serving](../serving/SKILL.md).

## Safety boundary

Full training is a long-running, GPU-heavy workflow that may download large checkpoints and datasets. This skill provides source-backed command construction and operational checks; do not start training unless the user explicitly supplies the model/data locations, resource budget, and permission to run the job.
