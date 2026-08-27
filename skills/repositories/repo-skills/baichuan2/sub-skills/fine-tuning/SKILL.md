---
name: fine-tuning
description: "Route supervised fine-tuning, DeepSpeed, LoRA, data preprocessing,
  and post-training loading for Baichuan2-7B-Base."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Baichuan2 Fine-Tuning

Use this sub-skill when the task is to prepare, explain, validate, or launch supervised fine-tuning for Baichuan2-7B-Base. It covers the training data format, the bundled supervised trainer, DeepSpeed ZeRO-3 launch structure, multi-machine hostfiles, LoRA toggling, and how to load the saved fine-tuned result.

Do **not** use this sub-skill for inference demos, chat APIs, quantized loading, or CPU deployment. Route those tasks to the appropriate inference or deployment guidance instead.

## Read first

- For an end-to-end run plan, read [`references/workflows.md`](references/workflows.md).
- For JSON training data requirements and label construction, read [`references/data-format.md`](references/data-format.md).
- For ZeRO-3 and `ds_config` interpretation, read [`references/deepspeed-config.md`](references/deepspeed-config.md).
- For dependency expectations and environment checks, read [`references/installation.md`](references/installation.md).
- For failure diagnosis, read [`references/troubleshooting.md`](references/troubleshooting.md).

## Bundled helpers

- [`scripts/validate_training_data.py`](scripts/validate_training_data.py): validates Belle-style multi-turn JSON, can write a tiny fixture, and can optionally estimate token truncation with a Baichuan tokenizer.
- [`scripts/train_supervised.py`](scripts/train_supervised.py): self-contained supervised trainer adapted for Baichuan2-7B-Base with schema validation, dry-run mode, DeepSpeed config generation, and LoRA options.

## Routing checklist

1. Confirm the user is fine-tuning a Base checkpoint, normally `baichuan-inc/Baichuan2-7B-Base`, not asking for inference or quantized deployment.
2. Validate the JSON data before launching any distributed job.
3. Decide full-parameter versus LoRA fine-tuning. Use LoRA when VRAM or wall-clock budget is limited, and keep `target_modules=W_pack` unless the model architecture has been intentionally changed.
4. Create or verify a DeepSpeed ZeRO-3 config and match it with the Hugging Face `TrainingArguments` flags.
5. For one machine, use an empty or omitted hostfile. For multiple machines, prepare a DeepSpeed hostfile with one `hostname slots=N` line per node.
6. After training, load a full fine-tuned output with `AutoModelForCausalLM.from_pretrained(...)`; load LoRA adapter output with `peft.AutoPeftModelForCausalLM.from_pretrained(...)`.

## Safe default posture

Before launching training, prefer:

```bash
python scripts/validate_training_data.py \
  --data_path /path/to/train.json \
  --model_max_length 512

python scripts/train_supervised.py \
  --dry_run True \
  --data_path /path/to/train.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /path/to/output \
  --model_max_length 512
```

Only move from dry-run validation to DeepSpeed training when dependencies, CUDA visibility, hostfile formatting, and data schema all pass.
