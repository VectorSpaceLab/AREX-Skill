# Training CLI Reference

LitGPT training commands are Lightning CLI-backed entry points. Use `--config <yaml>` for recipe files and `--print_config` to inspect the final merged config before expensive work.

## Command Families

| Command | Purpose | Required positional | Default output | Notes |
| --- | --- | --- | --- | --- |
| `litgpt finetune_lora` | LoRA SFT and QLoRA when `--quantize` is set | `checkpoint_dir` | `out/finetune/lora` | Saves LoRA weights such as `lit_model.pth.lora`; merge/conversion is checkpoint-owned. |
| `litgpt finetune_full` | Full-parameter supervised finetuning | `checkpoint_dir` | `out/finetune/full` | No `--quantize` option. Highest memory cost. Supports `--resume`. |
| `litgpt finetune_adapter` | Adapter supervised finetuning | `checkpoint_dir` | `out/finetune/adapter` | Supports `--quantize` with LoRA-like quantization caveats. |
| `litgpt finetune_adapter_v2` | Adapter v2 supervised finetuning | `checkpoint_dir` | `out/finetune/adapter-v2` | Supports `--resume true/false/null`; saves `lit_model.pth.adapter_v2`. |
| `litgpt pretrain` | Scratch or continued pretraining | `model_name` | `out/pretrain` | Uses token-based `TrainArgs`; continued pretraining uses `--initial_checkpoint_dir`. |

`litgpt finetune` is a command group/alias surface in user docs; prefer the explicit installed commands above when constructing commands for reproducibility.

## Shared Training Args

`TrainArgs` fields appear as `--train.<field>` flags:

- `--train.save_interval`: optimizer-step interval for checkpoints; use `null`/config `null` only if checkpointing is intentionally disabled.
- `--train.log_interval`: iteration interval for metrics logging.
- `--train.global_batch_size`: samples per optimizer step across all data-parallel ranks.
- `--train.micro_batch_size`: samples per device/rank per iteration; reduce first for OOM.
- `--train.lr_warmup_steps` and `--train.lr_warmup_fraction`: mutually exclusive; the fraction must be between 0 and 1.
- `--train.epochs`: required by finetuning families; unsupported by `pretrain`.
- `--train.max_tokens`: required by `pretrain`; unsupported by finetuning families.
- `--train.max_steps`: debug/profiling limit; for full pretraining prefer `max_tokens` or `max_time`.
- `--train.max_seq_length`: truncates SFT samples or caps pretrain sequence length; primary OOM lever after micro batch size.
- `--train.max_norm`: required by `pretrain`; unsupported by finetuning families.
- `--train.tie_embeddings`: supported in pretrain recipes; unsupported by finetuning families.
- `--train.min_lr`: minimum learning rate used by schedulers.

`global_batch_size` must be large enough for `devices * num_nodes`; per-rank batch is `global_batch_size // (devices * num_nodes)`, and gradient accumulation is per-rank batch divided by `micro_batch_size`.

## Eval Args

`EvalArgs` fields appear as `--eval.<field>` flags:

- `--eval.interval`: optimizer-step interval for validation.
- `--eval.max_new_tokens`: required by finetuning families because they can periodically generate an example; unsupported by `pretrain`.
- `--eval.max_iters`: validation batches to evaluate.
- `--eval.initial_validation`: run validation before training.
- `--eval.final_validation`: run final validation after training; set false for quick smoke/debug plans.
- `--eval.evaluate_example`: `first`, `random`, or an integer sample index for SFT example generation.

If generated example length plus `eval.max_new_tokens` exceeds the model sequence length used for training, LitGPT skips example generation for efficiency.

## Log Args And Logger Names

`LogArgs` fields appear as `--log.<field>` flags and logger selection uses `--logger_name`:

- Logger choices: `csv`, `tensorboard`, `wandb`, `mlflow`, `litlogger`.
- Default finetuning logger: `csv`.
- Default pretraining logger: `tensorboard`.
- `wandb`, `mlflow`, `litlogger`, and sometimes `tensorboard` require optional packages and/or credentials outside the core install.
- `--log.project`, `--log.run`, and `--log.group` are WandB-oriented fields.
- `--log.teamspace`, `--log.metadata`, `--log.log_model`, `--log.save_logs`, and `--log.checkpoint_name` are LitLogger-oriented fields.

Prefer `--logger_name csv` for local deterministic smoke or CI-like runs.

## Data Flags

All training commands expose:

- `--data <DataModuleName>` or a config object with `class_path`/`init_args`.
- `--data.help [CLASS_PATH_OR_NAME]` to inspect data-module-specific options.
- Built-in SFT examples include `Alpaca`, `Alpaca2k`, `AlpacaGPT4`, `Deita`, `Dolly`-style modules when available in the installed build, `FLAN`, `LIMA`, `LongForm`, and `JSON`.
- Pretraining modules include `TextFiles`, `TinyStories`, `OpenWebText`, `TinyLlama`, `MicroLlama`, and `LitData` depending on optional dependencies.

For custom SFT files, use `--data JSON --data.json_path <file-or-dir>`; see `data-formats.md`.

## Quantization Rules

Quantization is available for LoRA and adapter finetuning commands through `--quantize` values such as `bnb.nf4`, `bnb.nf4-dq`, `bnb.fp4`, `bnb.fp4-dq`, and `bnb.int8-training`.

Hard constraints verified from training source:

- Quantization with mixed precision is not supported. Avoid `--precision bf16-mixed` or `--precision 16-mixed` when `--quantize` is set.
- Quantized LoRA/adapter training is single-device/single-node only. Use `--devices 1 --num_nodes 1`.
- Quantization requires bitsandbytes support; missing or incompatible bitsandbytes fails before/at training setup.
- Full finetuning does not expose a quantization flag; remove `--quantize` when converting a QLoRA plan to full finetuning.

## Pretrain-Specific Rules

`litgpt pretrain` requires a model name from LitGPT configs or a config object:

- Scratch-like pretraining usually needs `--tokenizer_dir` if the selected data module expects an existing tokenizer.
- Continued pretraining uses `--initial_checkpoint_dir <checkpoint>` and should also use the tokenizer from that checkpoint or preprocessing pipeline.
- `--initial_checkpoint_dir` and `--resume` are mutually exclusive.
- `--train.max_tokens` and `--train.max_norm` are required by source validation.
- `--train.epochs` and `--eval.max_new_tokens` are unsupported by source validation.

## Resume Rules

- `finetune_full`: `--resume true` errors if no checkpoint exists, `--resume auto` resumes if possible and otherwise starts fresh, or pass an explicit resume checkpoint path.
- `finetune_adapter_v2`: `--resume true` searches `out_dir` for latest adapter_v2 step checkpoint; false/null starts fresh.
- `pretrain`: `--resume true`, `--resume auto`, or a path resumes from `out_dir`/path; cannot be combined with `--initial_checkpoint_dir`.
- `finetune_lora` and `finetune_adapter` do not expose the same public resume flag in the verified CLI surface.

## Minimal Command Shapes

LoRA SFT with custom JSON:

```bash
litgpt finetune_lora checkpoints/org/model \
  --data JSON \
  --data.json_path data/sft.jsonl \
  --data.val_split_fraction 0.1 \
  --train.micro_batch_size 1 \
  --train.max_seq_length 512 \
  --out_dir out/finetune/lora-custom \
  --logger_name csv
```

QLoRA SFT:

```bash
litgpt finetune_lora checkpoints/org/model \
  --quantize bnb.nf4 \
  --precision bf16-true \
  --devices 1 \
  --num_nodes 1 \
  --data Alpaca2k
```

Full finetuning from an adapted QLoRA intent:

```bash
litgpt finetune_full checkpoints/org/model \
  --data JSON \
  --data.json_path data/sft.jsonl \
  --train.epochs 1 \
  --train.micro_batch_size 1 \
  --train.max_seq_length 512 \
  --logger_name csv
```

Pretraining from text files:

```bash
litgpt pretrain pythia-14m \
  --tokenizer_dir checkpoints/EleutherAI/pythia-14m \
  --data TextFiles \
  --data.train_data_path data/pretrain_text \
  --train.max_tokens 1000000 \
  --train.max_norm 1.0 \
  --train.micro_batch_size 1
```

Before executing, run:

```bash
python scripts/summarize_training_command.py -- litgpt finetune_lora checkpoints/org/model --data JSON --data.json_path data/sft.jsonl
```
