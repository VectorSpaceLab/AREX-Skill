---
name: training
description: "Build, debug, and explain ms-swift pre-training and supervised
  fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ms-swift Training

Use this sub-skill when the task is about `swift pt`, `swift sft`, training configs, LoRA/QLoRA/full tuning, distributed training flags, multimodal training memory controls, checkpoint resume semantics, or handing trained checkpoints/adapters to inference/export workflows.

## Route First

- Use `swift pt` for continued pre-training (CPT) or plain generative-language-model training where the chat template should be disabled; it is equivalent to `swift sft --use_chat_template false --loss_scale all`.
- Use `swift sft` for supervised fine-tuning, chat/instruction tuning, LoRA/QLoRA/full tuning, multimodal SFT, and most training examples.
- Reroute dataset schema design, custom dataset registration, and column mapping to `data-model-customization`.
- Reroute runtime inference, deployment servers, and generation backends to `inference-deployment`.
- Reroute RLHF/GRPO/GKD/PPO/KTO/DPO, Ray rollout, and Megatron distributed training depth to `advanced-rl-distributed`.
- Reroute export, quantization, model push, LoRA merge as a primary workflow, and standalone evaluation to `export-evaluation`.

## Read These References

- [Training workflows](references/workflows.md) for command patterns, YAML/JSON configs, tuning modes, checkpoints, multimodal options, and training-to-inference handoff.
- [CLI reference](references/cli-reference.md) for high-value `swift sft` and `swift pt` arguments and safe option combinations.
- [Troubleshooting](references/troubleshooting.md) for download/offline behavior, CUDA/NPU setup, OOM, DDP, DeepSpeed/FSDP, LoRA/QLoRA, and template issues.

## Bundled Scripts

- Use `scripts/build_training_command.py --help` to print a safe command skeleton for `swift sft` or `swift pt` without launching training.
- Use `scripts/validate_training_config.py CONFIG.yaml` or `CONFIG.json` to catch high-risk config mistakes before running training; it parses YAML/JSON and does not import heavy model code.

## Quick Patterns

```bash
swift sft \
  --model Qwen/Qwen2.5-7B-Instruct \
  --dataset ./train.jsonl \
  --split_dataset_ratio 0.05 \
  --train_type lora \
  --output_dir output/qwen2_5_lora_sft \
  --max_length 2048 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 1e-4 \
  --save_steps 500
```

```bash
swift pt \
  --model Qwen/Qwen2.5-7B \
  --dataset ./corpus.jsonl \
  --train_type lora \
  --loss_scale all \
  --use_chat_template false \
  --output_dir output/qwen2_5_cpt
```

## Minimum Review Checklist

- Confirm `model`, `dataset` or `cached_dataset`, `output_dir`, tuning mode, `max_length`, batch/accumulation, dtype, and save/eval cadence.
- Decide whether the run needs ModelScope or HuggingFace sources; use local model/dataset paths plus `--check_model false` for fully offline runs.
- For LoRA outputs, hand off inference with `--adapters checkpoint_dir`; for full fine-tuning outputs, hand off with `--model checkpoint_dir`.
- For vLLM/SGLang/LMDeploy acceleration after LoRA, plan a merge/export path; do not promise adapter-only QLoRA merge acceleration.
