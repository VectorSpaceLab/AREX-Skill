# CLI Configuration

`unsloth train` loads a YAML or JSON file into a Pydantic `Config` model, then applies CLI overrides. YAML files use `.yaml` or `.yml`; any other suffix is parsed as JSON.

## Minimal training config

A real training run needs:

- `model`: base model id or local model path.
- Either `data.dataset` or one or more `data.local_dataset` entries.
- `training.training_type`: usually `lora`; use `full` only with a base model, not a LoRA adapter directory.
- `training.output_dir`: a user-controlled output folder.

Use `scripts/training_config_template.yaml` as a starter and validate with:

```bash
unsloth train --config config.yaml --dry-run
```

`--dry-run` prints the resolved config and exits before importing the training backend, loading a model, or loading a dataset.

## Config sections

### Root

| Field | Default | Notes |
|---|---|---|
| `model` | `null` | Required for a real run; may be an HF id or local path. |
| `data` | defaults | Dataset source and format. |
| `training` | defaults | Training loop and optimizer settings. |
| `lora` | defaults | LoRA adapter settings and trainable modules. |
| `logging` | defaults | W&B, TensorBoard, and HF token config. |

### `data`

| Field | Default | CLI flag | Notes |
|---|---:|---|---|
| `dataset` | `null` | `--dataset` | Dataset id/source handled by the backend. |
| `local_dataset` | `null` | `--local-dataset` | Repeat the flag for multiple local files/folders. |
| `format_type` | `auto` | `--format-type` | One of `auto`, `alpaca`, `chatml`, `sharegpt`. |

### `training`

| Field | Default | CLI flag | Notes |
|---|---:|---|---|
| `training_type` | `lora` | `--training-type` | `lora` or `full`; full finetuning rejects LoRA adapter inputs. |
| `max_seq_length` | `2048` | `--max-seq-length` | Context length for model load and training kwargs. |
| `load_in_4bit` | `true` | `--load-in-4bit/--no-load-in-4bit` | Used for LoRA; full finetuning loads without 4-bit. |
| `output_dir` | `./outputs` | `--output-dir` | Converted to a string in dry-run output. |
| `num_epochs` | `3` | `--num-epochs` | Epoch count. |
| `learning_rate` | `0.0002` | `--learning-rate` | Optimizer learning rate. |
| `batch_size` | `2` | `--batch-size` | Per-device batch size passed to backend. |
| `gradient_accumulation_steps` | `4` | `--gradient-accumulation-steps` | Effective batch multiplier. |
| `warmup_steps` | `5` | `--warmup-steps` | Scheduler warmup. |
| `max_steps` | `0` | `--max-steps` | `0` lets epoch settings drive training. |
| `save_steps` | `0` | `--save-steps` | `0` means no step-based checkpoint interval from this field. |
| `weight_decay` | `0.01` | `--weight-decay` | Optimizer weight decay. |
| `random_seed` | `3407` | `--random-seed` | Reproducibility seed. |
| `packing` | `false` | `--packing/--no-packing` | Pack short examples. |
| `train_on_completions` | `false` | `--train-on-completions/--no-train-on-completions` | Completion-only training behavior. |
| `gradient_checkpointing` | `unsloth` | `--gradient-checkpointing` | One of `unsloth`, `true`, `none`. |

### `lora`

| Field | Default | CLI flag | Notes |
|---|---:|---|---|
| `lora_r` | `64` | `--lora-r` | Rank. |
| `lora_alpha` | `16` | `--lora-alpha` | Alpha scaling. |
| `lora_dropout` | `0.0` | `--lora-dropout` | Dropout. |
| `target_modules` | `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` | `--target-modules` | Comma-separated module names; parsed into a list for non-vision models. |
| `vision_all_linear` | `false` | `--vision-all-linear/--no-vision-all-linear` | For vision models, uses `all-linear` target modules when true. |
| `use_rslora` | `false` | `--use-rslora/--no-use-rslora` | Enable rank-stabilized LoRA. |
| `use_loftq` | `false` | `--use-loftq/--no-use-loftq` | Enable LoftQ behavior. |
| `finetune_vision_layers` | `true` | `--finetune-vision-layers/--no-finetune-vision-layers` | Vision-layer training switch. |
| `finetune_language_layers` | `true` | `--finetune-language-layers/--no-finetune-language-layers` | Language-layer training switch. |
| `finetune_attention_modules` | `true` | `--finetune-attention-modules/--no-finetune-attention-modules` | Attention module training switch. |
| `finetune_mlp_modules` | `true` | `--finetune-mlp-modules/--no-finetune-mlp-modules` | MLP module training switch. |

### `logging`

| Field | Default | CLI flag | Notes |
|---|---:|---|---|
| `enable_wandb` | `false` | `--enable-wandb/--no-enable-wandb` | Enables W&B logging. |
| `wandb_project` | `unsloth-training` | `--wandb-project` | W&B project. |
| `wandb_token` | `null` | `--wandb-token` | Also reads `WANDB_API_KEY`; CLI/env wins. |
| `enable_tensorboard` | `false` | `--enable-tensorboard/--no-enable-tensorboard` | Enables TensorBoard logging. |
| `tensorboard_dir` | `runs` | `--tensorboard-dir` | TensorBoard log directory. |
| `hf_token` | `null` | `--hf-token` | Also reads `HF_TOKEN`; CLI/env wins. |

## Override rules

- CLI flag names are derived from config field names by replacing `_` with `-` and prefixing `--`.
- Nested fields are flattened, so `training.max_seq_length` becomes `--max-seq-length` and `lora.lora_r` becomes `--lora-r`.
- Boolean config fields use paired Typer flags such as `--packing/--no-packing`.
- List fields are repeatable; `--local-dataset a.jsonl --local-dataset b.jsonl` resolves to a list.
- CLI overrides apply only when a value is provided; omitted flags leave the config value intact.
- Duplicate flattened field names are invalid in the option generator.

## Token precedence

For `train`, token values resolve in this order:

1. Explicit CLI flag value.
2. Environment variable exposed by the flag: `HF_TOKEN` for `--hf-token`, `WANDB_API_KEY` for `--wandb-token`.
3. Config file fields: `logging.hf_token` and `logging.wandb_token`.
4. `null` if none is provided.

Avoid committing tokens into config files. Prefer environment variables or secret managers for real runs.

## Dry-run review checklist

After `unsloth train --config config.yaml --dry-run`, inspect the emitted YAML for:

- `model` is not empty and is the intended base model, not a LoRA adapter when `training_type: full`.
- Exactly one intended dataset source is present, or multiple `local_dataset` entries are deliberate.
- `output_dir` points to a disposable/user-approved output location.
- `load_in_4bit` matches the training type and memory plan.
- `max_seq_length`, batch size, and gradient accumulation match available hardware.
- Token fields are absent or placeholder-only unless the user intentionally injected them for a private run.
