# Fine-Tuning Workflows

This reference turns the fine-tuning surface into runnable steps. It is scoped to supervised fine-tuning of Baichuan2-7B-Base with optional LoRA and DeepSpeed. It intentionally excludes inference demos, quantized serving, and CPU deployment.

## Inputs you need

- A Base model identifier or local model directory, usually `baichuan-inc/Baichuan2-7B-Base`.
- A supervised JSON training file in the format described in [`data-format.md`](data-format.md).
- A writable output directory for trainer state, checkpoints, tokenizer files, and final weights or LoRA adapters.
- A DeepSpeed JSON config. You can generate the default ZeRO-3 config with the bundled trainer.
- CUDA-capable GPUs for practical runs. A verified environment used torch CUDA wheels, DeepSpeed, PEFT, Accelerate, SentencePiece, and an NVIDIA A100 smoke check.

## Step 1: validate data

```bash
python scripts/validate_training_data.py \
  --data_path /data/baichuan2_sft.json \
  --model_max_length 512
```

For a minimal local fixture:

```bash
python scripts/validate_training_data.py \
  --write_fixture ./baichuan2_sft_fixture.json
python scripts/validate_training_data.py \
  --data_path ./baichuan2_sft_fixture.json
```

Add `--tokenizer_name_or_path baichuan-inc/Baichuan2-7B-Base` when the tokenizer is available and you want truncation estimates.

## Step 2: write the default DeepSpeed config

```bash
python scripts/train_supervised.py \
  --dry_run True \
  --write_deepspeed_config /work/baichuan2_sft/ds_config.json \
  --data_path /data/baichuan2_sft.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /work/baichuan2_sft/output
```

The generated config mirrors the documented ZeRO-3 setup: Hugging Face fills in batch-size-related `auto` values, bf16 follows the trainer flag, and model-save gathering is enabled so saved checkpoints are usable after ZeRO partitioning.

## Step 3: dry-run trainer arguments

```bash
python scripts/train_supervised.py \
  --dry_run True \
  --data_path /data/baichuan2_sft.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /work/baichuan2_sft/output \
  --model_max_length 512 \
  --num_train_epochs 4 \
  --per_device_train_batch_size 16 \
  --gradient_accumulation_steps 1 \
  --learning_rate 2e-5 \
  --gradient_checkpointing True \
  --bf16 True \
  --tf32 True \
  --deepspeed /work/baichuan2_sft/ds_config.json
```

Dry-run mode validates schema and prints the resolved training plan without loading the model. Add `--dry_run_tokenize True` only when you intentionally want to load the tokenizer and preview the label mask.

## Single-machine DeepSpeed launch

Use no hostfile or an empty hostfile value for one machine. Match `CUDA_VISIBLE_DEVICES` to the GPUs you intend to use.

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

deepspeed scripts/train_supervised.py \
  --report_to none \
  --data_path /data/baichuan2_sft.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /work/baichuan2_sft/output \
  --model_max_length 512 \
  --num_train_epochs 4 \
  --per_device_train_batch_size 16 \
  --gradient_accumulation_steps 1 \
  --save_strategy epoch \
  --learning_rate 2e-5 \
  --lr_scheduler_type constant \
  --adam_beta1 0.9 \
  --adam_beta2 0.98 \
  --adam_epsilon 1e-8 \
  --max_grad_norm 1.0 \
  --weight_decay 1e-4 \
  --warmup_ratio 0.0 \
  --logging_steps 1 \
  --gradient_checkpointing True \
  --deepspeed /work/baichuan2_sft/ds_config.json \
  --bf16 True \
  --tf32 True
```

Reduce `per_device_train_batch_size` first if VRAM is insufficient. Increase `gradient_accumulation_steps` to preserve the effective global batch size.

## Multi-machine hostfile launch

DeepSpeed hostfile lines have the form:

```text
node-a slots=8
node-b slots=8
node-c slots=8
node-d slots=8
```

Each hostname must be resolvable from the launch node, SSH access must be configured, and `slots` must not exceed the number of visible GPUs on that node. Then launch:

```bash
deepspeed --hostfile /work/baichuan2_sft/hostfile \
  scripts/train_supervised.py \
  --report_to none \
  --data_path /data/baichuan2_sft.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /work/baichuan2_sft/output \
  --model_max_length 512 \
  --num_train_epochs 4 \
  --per_device_train_batch_size 16 \
  --gradient_accumulation_steps 1 \
  --save_strategy epoch \
  --learning_rate 2e-5 \
  --lr_scheduler_type constant \
  --gradient_checkpointing True \
  --deepspeed /work/baichuan2_sft/ds_config.json \
  --bf16 True \
  --tf32 True
```

## LoRA launch

LoRA is enabled by adding `--use_lora True`. The bundled trainer defaults to Baichuan's packed attention projection module, `W_pack`, with rank 1, alpha 32, and dropout 0.1. Override those when intentionally experimenting.

```bash
deepspeed scripts/train_supervised.py \
  --report_to none \
  --data_path /data/baichuan2_sft.json \
  --model_name_or_path baichuan-inc/Baichuan2-7B-Base \
  --output_dir /work/baichuan2_lora/output \
  --model_max_length 512 \
  --num_train_epochs 4 \
  --per_device_train_batch_size 16 \
  --gradient_accumulation_steps 1 \
  --learning_rate 2e-5 \
  --gradient_checkpointing True \
  --deepspeed /work/baichuan2_sft/ds_config.json \
  --bf16 True \
  --tf32 True \
  --use_lora True \
  --lora_target_modules W_pack \
  --lora_r 1 \
  --lora_alpha 32 \
  --lora_dropout 0.1
```

## Post-training loading path

Full-parameter output:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir = "/work/baichuan2_sft/output"
tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_dir, trust_remote_code=True)
```

LoRA adapter output:

```python
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

adapter_dir = "/work/baichuan2_lora/output"
tokenizer = AutoTokenizer.from_pretrained(adapter_dir, use_fast=False, trust_remote_code=True)
model = AutoPeftModelForCausalLM.from_pretrained(adapter_dir, trust_remote_code=True)
```

Keep this loading check separate from training. It verifies that the output directory is structurally loadable; quality evaluation needs a task-specific evaluation plan.
