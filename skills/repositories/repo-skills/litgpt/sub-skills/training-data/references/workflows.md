# Training Workflows

Use these workflows to plan commands before running expensive GPU/network-dependent LitGPT jobs.

## Supervised Finetuning With JSON/JSONL

1. Validate the base checkpoint with the checkpoint sub-skill if it is local; if the user provides a model name, expect LitGPT to auto-download or ask the user to download first.
2. Validate SFT data:

```bash
python scripts/validate_json_sft_data.py data/sft.jsonl --val-split-fraction 0.1
```

3. Build a conservative first command:

```bash
litgpt finetune_lora checkpoints/org/model \
  --data JSON \
  --data.json_path data/sft.jsonl \
  --data.val_split_fraction 0.1 \
  --train.epochs 1 \
  --train.micro_batch_size 1 \
  --train.max_seq_length 512 \
  --eval.max_iters 10 \
  --eval.final_validation false \
  --logger_name csv \
  --out_dir out/finetune/lora-json-smoke
```

4. Inspect without training when possible:

```bash
litgpt finetune_lora checkpoints/org/model --data JSON --data.json_path data/sft.jsonl --print_config
python scripts/summarize_training_command.py -- litgpt finetune_lora checkpoints/org/model --data JSON --data.json_path data/sft.jsonl --train.micro_batch_size 1
```

5. Scale only after data validation, checkpoint validation, optional dependency checks, and a small smoke plan are clean.

## LoRA Versus QLoRA

Use LoRA when memory is sufficient or bitsandbytes is unavailable:

```bash
litgpt finetune_lora checkpoints/org/model --data Alpaca2k --precision bf16-true
```

Use QLoRA when the user explicitly wants quantized LoRA and has compatible bitsandbytes on one device:

```bash
litgpt finetune_lora checkpoints/org/model \
  --data Alpaca2k \
  --quantize bnb.nf4 \
  --precision bf16-true \
  --devices 1 \
  --num_nodes 1
```

Do not combine QLoRA with mixed precision or multi-GPU. If the user asks for QLoRA on multiple GPUs, recommend non-quantized LoRA/full with sharding or a single-device QLoRA run.

## Convert QLoRA Intent To Full Finetuning

When a user asks to switch from QLoRA to full finetuning:

1. Change `finetune_lora` to `finetune_full`.
2. Remove `--quantize` and all `--lora_*` flags.
3. Keep `--data`, `--train.epochs`, `--train.max_seq_length`, `--eval.*`, `--logger_name`, and optimizer intent where compatible.
4. Lower `--train.micro_batch_size` and consider reducing `--train.max_seq_length`; full finetuning trains all parameters and is much more memory intensive.
5. Run the summarizer and review warnings before training:

```bash
python scripts/summarize_training_command.py -- litgpt finetune_full checkpoints/org/model --data JSON --data.json_path data/sft.jsonl --train.micro_batch_size 1
```

## Adapter Finetuning

Adapter commands are similar to LoRA but save adapter-specific weights:

```bash
litgpt finetune_adapter checkpoints/org/model --data Alpaca2k --out_dir out/finetune/adapter-demo
litgpt finetune_adapter_v2 checkpoints/org/model --data Alpaca2k --out_dir out/finetune/adapter-v2-demo
```

Use adapter_v2 when the user specifically asks for the v2 method or needs its resume surface. Quantization follows LoRA-like constraints: no mixed precision with `--quantize`, and no quantized multi-GPU/multi-node run.

## Full Finetuning

Full finetuning updates all model weights and generally has the highest memory requirement.

Safe first-run shape:

```bash
litgpt finetune_full checkpoints/org/model \
  --data JSON \
  --data.json_path data/sft.jsonl \
  --data.val_split_fraction 0.1 \
  --train.epochs 1 \
  --train.micro_batch_size 1 \
  --train.max_seq_length 512 \
  --eval.max_iters 10 \
  --eval.final_validation false \
  --logger_name csv
```

For interrupted full finetuning:

```bash
litgpt finetune_full checkpoints/org/model \
  --resume auto \
  --out_dir out/finetune/full-run \
  --data JSON \
  --data.json_path data/sft.jsonl
```

`--resume true` should be used only when a checkpoint is expected to exist; `auto` is safer for reusable commands.

## Pretraining From Scratch Or Text Files

1. Choose a supported `model_name` or provide a model config in YAML.
2. Choose a tokenizer source. For many custom text-file workflows, download or provide tokenizer files first.
3. Use `TextFiles` only for small/local text corpora; for multi-GB corpora prefer preprocessed `LitData`.
4. Include required `TrainArgs`: `max_tokens` and `max_norm`.

Example:

```bash
litgpt pretrain pythia-14m \
  --tokenizer_dir checkpoints/EleutherAI/pythia-14m \
  --data TextFiles \
  --data.train_data_path data/pretrain_text \
  --train.max_tokens 1000000 \
  --train.max_norm 1.0 \
  --train.micro_batch_size 1 \
  --eval.final_validation false \
  --logger_name csv
```

Use `--train.max_steps` only for profiling/debug. It is not the intended final budget for pretraining.

## Continued Pretraining

Starting from an existing checkpoint:

```bash
litgpt pretrain pythia-160m \
  --initial_checkpoint_dir checkpoints/EleutherAI/pythia-160m \
  --tokenizer_dir checkpoints/EleutherAI/pythia-160m \
  --out_dir out/pretrain/domain-adapted \
  --data TextFiles \
  --data.train_data_path data/domain_text \
  --train.max_tokens 1000000 \
  --train.max_norm 1.0
```

Resuming an interrupted run:

```bash
litgpt pretrain pythia-160m \
  --resume auto \
  --tokenizer_dir checkpoints/EleutherAI/pythia-160m \
  --out_dir out/pretrain/domain-adapted \
  --data TextFiles \
  --data.train_data_path data/domain_text \
  --train.max_tokens 1000000 \
  --train.max_norm 1.0
```

Do not combine `--initial_checkpoint_dir` with `--resume`.

## OOM-Safe Command Construction

Start conservative:

- `--train.micro_batch_size 1`.
- `--train.max_seq_length 256` or `512` for SFT smoke runs.
- Small model/checkpoint for workflow proof.
- Parameter-efficient method before full finetuning.
- `--precision bf16-true` where supported; avoid mixed precision with quantization.
- Single device for quantized LoRA/adapter.
- `--logger_name csv` to avoid optional logger failures.

Scale in one dimension at a time after the run is stable: sequence length, global batch size, model size, devices, then final token/epoch budget.

## Post-Training Routing

- To generate from a full finetuned checkpoint, route to `../../inference-chat/`.
- To merge LoRA weights or convert trained checkpoints, route to `../../checkpoint-conversion/`.
- To evaluate with LM Evaluation Harness or serve via LitServe, route to `../../evaluation-serving/`.
