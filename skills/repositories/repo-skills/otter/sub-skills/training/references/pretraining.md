# Pretraining workflows

Otter contains two pretraining entry points distinct from instruction tuning. The entry point names are target-checkout commands for a user-controlled Otter checkout or equivalent deployment package. They are resource-heavy WebDataset-style workflows and should normally be treated as command-construction tasks unless the user explicitly authorizes a full run.

## How pretraining differs from SFT

| Aspect | SFT / instruction following | `pretraining.py` | `pretraining_cc3m.py` |
|---|---|---|---|
| Entry point | `pipeline/train/instruction_following.py` | `pipeline/train/pretraining.py` | `pipeline/train/pretraining_cc3m.py` |
| Data input | MIMIC-IT YAML via `--training_data_yaml` | MMC4 shards plus LAION shards | CC3M shards |
| Loader call | `get_data(..., "mimicit")` | `get_data(..., "mmc4")` and `get_data(..., "laion")` | `get_data(..., "cc3m")` |
| Batch flags | `--batch_size` | `--batch_size_mmc4`, `--batch_size_laion` | `--batch_size_cc3m` |
| Loss terms | MIMIC-IT loss | Separate MMC4 and LAION losses | CC3M loss |
| Checkpoint cadence | final weights; optional epoch and step saves | `--checkpointing_steps`, epoch checkpoints, final weights | `--checkpointing_steps`, epoch checkpoints, final weights |
| Resume behavior | `--trained_ckpt` can load a checkpoint state before SFT; parser also exposes `--resume_from_checkpoint` but SFT does not implement the same scan logic as pretraining | scans the run save directory when `--resume_from_checkpoint` is set | scans step checkpoints in the run save directory when `--resume_from_checkpoint` is set |

## MMC4 + LAION pretraining

Required inputs:

- `--pretrained_model_name_or_path`: model identifier or local path.
- `--mmc4_shards`: brace/glob-style shard pattern for MMC4 webdataset shards.
- `--laion_shards`: brace/glob-style shard pattern for LAION webdataset shards.
- `--external_save_dir` and `--run_name`: make save location explicit.

High-impact defaults:

| Flag | Default | Notes |
|---|---:|---|
| `--train_num_samples_mmc4` | `100` | Used when dataset size metadata is unavailable or for limiting. |
| `--train_num_samples_laion` | `100` | Keep sample counts compatible with expected batch counts. |
| `--batch_size_mmc4` | `8` | Per-process MMC4 batch size. |
| `--batch_size_laion` | `8` | Per-process LAION batch size. |
| `--loss_multiplier_mmc4` | `1.0` | MMC4 loss scale. |
| `--loss_multiplier_laion` | `0.2` | LAION loss scale. |
| `--checkpointing_steps` | `10000` | Saves `checkpoint_steps<N>.pt` plus config. |
| `--precision` | `amp` | Accepted choices: `amp_bf16`, `amp_bfloat16`, `bf16`, `amp`, `fp16`, `fp32`. |
| `--max-src-length` / `--max-tgt-length` | `1024` / `1024` | Sequence length controls memory. |

Command-construction example:

```bash
python ../scripts/build_training_command.py \
  --mode pretraining \
  --pretrained-model <model-or-local-path> \
  --mmc4-shards '/data/mmc4/shard-{0000..0999}.tar' \
  --laion-shards '/data/laion/shard-{0000..0999}.tar' \
  --run-name otter_pretrain_mmc4_laion \
  --external-save-dir checkpoints \
  --num-processes 8 \
  --checkpointing-steps 10000
```

Operational notes:

- `pretraining.py` asserts that MMC4 and LAION dataloaders have the same number of batches. Adjust shard patterns, sample counts, and batch sizes until they align.
- The loader expands brace patterns and looks for dataset-size metadata such as `sizes.json` or `__len__` next to shards when available.
- Each training step performs LAION forward/backward and MMC4 forward/backward before optimizer/scheduler updates.
- Final output includes `final_weights.pt` unless `--save_hf_model` is set, in which case Hugging Face-format assets are also written.

## CC3M pretraining

Required inputs:

- `--pretrained_model_name_or_path`: model identifier or local path.
- `--cc3m_shards`: brace/glob-style shard pattern for CC3M webdataset shards.
- `--external_save_dir` and `--run_name`: make save location explicit.

High-impact defaults:

| Flag | Default | Notes |
|---|---:|---|
| `--train_num_samples_cc3m` | `100` | Used for limiting/size fallback. |
| `--batch_size_cc3m` | `8` | Per-process CC3M batch size; also written to DeepSpeed plugin micro-batch size. |
| `--loss_multiplier_cc3m` | `1` | CC3M loss scale. |
| `--checkpointing_steps` | `10000` | Saves `checkpoint_steps<N>.pt` plus config. |
| `--max-src-length` / `--max-tgt-length` | `1024` / `1024` | Sequence length controls memory. |

Command-construction example:

```bash
python ../scripts/build_training_command.py \
  --mode pretraining-cc3m \
  --pretrained-model <model-or-local-path> \
  --cc3m-shards '/data/cc3m/shard-{0000..0999}.tar' \
  --run-name otter_pretrain_cc3m \
  --external-save-dir checkpoints \
  --num-processes 8
```

## W&B, offline, and checkpoints in pretraining

- `--save_checkpoints_to_wandb` requires `--report_to_wandb` and otherwise raises a parser-time error.
- `--offline` sets offline/cache mode; ensure checkpoints, tokenizer/model files, and shards are already local.
- `--delete_previous_checkpoint` removes earlier checkpoints after a newer checkpoint is saved; use it only when storage pressure is more important than recovery history.
- Resume logic is filename-pattern-sensitive. Before relying on resume, list the run directory and confirm checkpoint names match the script's expected scan pattern.
