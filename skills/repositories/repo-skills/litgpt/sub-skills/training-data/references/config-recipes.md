# Config Recipes

LitGPT config hub recipes are YAML files consumed with `--config`. They are the safest starting point for non-trivial finetuning or pretraining because they encode command-family defaults, optimizer settings, batch sizes, sequence lengths, logger choices, and data module init args.

## Recipe Families

Finetuning recipe shape:

```yaml
checkpoint_dir: checkpoints/org/model
out_dir: out/finetune/lora-model
precision: bf16-true
quantize: null
devices: 1
num_nodes: 1
data:
  class_path: litgpt.data.Alpaca2k
  init_args:
    mask_prompt: false
    prompt_style: alpaca
    ignore_index: -100
    seed: 42
    num_workers: 4
train:
  save_interval: 200
  log_interval: 1
  global_batch_size: 8
  micro_batch_size: 1
  lr_warmup_steps: 10
  epochs: 2
  max_seq_length: 512
eval:
  interval: 100
  max_new_tokens: 100
  max_iters: 100
  initial_validation: false
  final_validation: true
logger_name: csv
seed: 1337
optimizer:
  class_path: torch.optim.AdamW
  init_args:
    lr: 0.0002
    weight_decay: 0.0
    betas: [0.9, 0.95]
```

Pretraining recipe shape:

```yaml
model_name: pythia-14m
model_config: null
out_dir: out/pretrain/debug
precision: bf16-mixed
initial_checkpoint_dir: null
resume: false
data: TinyStories
train:
  save_interval: 1000
  log_interval: 1
  global_batch_size: 125
  micro_batch_size: 5
  lr_warmup_steps: 100
  epochs: null
  max_tokens: 100000000
  max_seq_length: null
  tie_embeddings: null
  max_norm: 1.0
  min_lr: 0.00006
eval:
  interval: 1000
  max_new_tokens: null
  max_iters: 100
  initial_validation: false
  final_validation: false
devices: auto
num_nodes: 1
tokenizer_dir: checkpoints/org/tokenizer
logger_name: tensorboard
seed: 42
```

## Choosing A Recipe

- Use `lora.yaml` for standard LoRA SFT when the user wants cheaper training and later LoRA merge/conversion.
- Use `qlora.yaml` when the user explicitly needs quantized LoRA and has compatible single-GPU bitsandbytes support.
- Use `full.yaml` only when the user wants all-parameter finetuning and has enough memory; remove all quantization concepts.
- Use `pretrain/debug.yaml` for small smoke plans, not for final training budgets.
- Use TinyStories/TinyLlama-style pretrain recipes as structural examples for `model_config`, tokenizer, token budget, and sequence length.

## Safe Adaptation Steps

1. Copy a matching recipe to the user's working config path.
2. Change `checkpoint_dir` or `model_name` first; ensure the selected model architecture is supported.
3. Change `out_dir` to a run-specific directory.
4. Change `data` to a built-in module or `litgpt.data.JSON` with local `json_path`.
5. Lower memory pressure for the first run: `micro_batch_size: 1`, modest `max_seq_length`, and a small `max_steps` debug cap if appropriate.
6. Keep optimizer values from the recipe unless the user has a concrete training reason to change them.
7. Run `litgpt <command> --config recipe.yaml --print_config` to inspect final values.
8. Run `python scripts/summarize_training_command.py -- litgpt <command> --config recipe.yaml ...` for command-line override risk checks.

## QLoRA To Full Finetuning Conversion

When converting a QLoRA request or recipe to full finetuning:

- Change the command from `finetune_lora` to `finetune_full`.
- Remove `quantize`; full finetuning has no `--quantize` flag.
- Remove LoRA-only fields: `lora_r`, `lora_alpha`, `lora_dropout`, `lora_query`, `lora_key`, `lora_value`, `lora_projection`, `lora_mlp`, `lora_head`.
- Increase memory caution: set `train.micro_batch_size: 1`, reduce `train.max_seq_length`, and consider a smaller model.
- Keep compatible intent fields: `checkpoint_dir`, `out_dir`, `precision`, `data`, `train.epochs`, `train.max_seq_length`, `eval.*`, `logger_name`, `seed`, and optimizer settings after reviewing memory.
- Re-check `global_batch_size`; full recipes often use different global/micro batch sizes than QLoRA recipes.

## Finetune Recipe Validation Rules

Source validation for finetuning families rejects or requires these fields:

- Required: `train.epochs`, `eval.max_new_tokens`.
- Unsupported: `train.max_tokens`, `train.max_norm`, `train.tie_embeddings`, `train.lr_warmup_fraction`.
- For LoRA/adapter quantization: no mixed precision and no multi-GPU/multi-node quantized run.
- Full finetuning supports `resume`; LoRA/adapter base commands do not share the same public resume surface.

## Pretrain Recipe Validation Rules

Source validation for pretraining rejects or requires these fields:

- Required: `train.max_tokens`, `train.max_norm`.
- Unsupported: `train.epochs`, `eval.max_new_tokens`.
- Mutually exclusive: `initial_checkpoint_dir` and `resume`.
- `train.max_steps` is intended for profiling/debug; final runs should use `max_tokens` or `max_time`.
- Some data modules require `tokenizer_dir`; if pretraining from text files or continuing a checkpoint, plan it explicitly.

## Recipe Hygiene

- Do not embed access tokens in YAML; pass tokens through secure runtime mechanisms only when the command truly needs gated downloads.
- Do not store machine-specific absolute paths in reusable recipes.
- Keep comments from source recipes useful, but remove stale comments that contradict changed values.
- Prefer `logger_name: csv` for safe local checks; switch to remote loggers only after dependencies and credentials are available.
- Keep `seed` explicit for reproducible data splits and training initialization.
