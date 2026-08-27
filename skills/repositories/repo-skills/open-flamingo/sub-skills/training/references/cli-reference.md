# OpenFlamingo training CLI reference

This reference summarizes the packaged OpenFlamingo training entrypoint parser. Use this sub-skill's bundled `scripts/run_training_entrypoint.py` wrapper when you need a checkout-independent launch target.

## Model configuration

| Flag | Default | Meaning |
| --- | --- | --- |
| `--vision_encoder_path` | `ViT-L-14` | OpenCLIP vision backbone name or path. |
| `--vision_encoder_pretrained` | `openai` | Vision encoder pretraining tag. |
| `--lm_path` | `facebook/opt-1.3b` | Hugging Face causal language model checkpoint. |
| `--tokenizer_path` | `facebook/opt-30b` | Tokenizer checkpoint. If you pass an empty string, the code falls back to `--lm_path`. |
| `--cross_attn_every_n_layers` | `1` | Insert one Flamingo cross-attention block every N decoder layers. |

## Data

| Flag | Default | Meaning |
| --- | --- | --- |
| `--laion_shards` | required | Brace-expanded glob or shard URL pattern for LAION WebDataset tar files. |
| `--mmc4_shards` | required | Brace-expanded glob or shard URL pattern for MMC4 / ChatGPT WebDataset tar files. |
| `--workers` | `1` | DataLoader worker count per process. |
| `--train_num_samples_mmc4` | `10000` | Samples per epoch budget for MMC4 when shard metadata is unavailable. |
| `--train_num_samples_laion` | `10000` | Samples per epoch budget for LAION when shard metadata is unavailable. |
| `--dataset_resampled` | off | Sample shards with replacement instead of a finite epoch over the shard list. Recommended for long training runs. |
| `--mmc4_textsim_threshold` | `30` | Minimum image-text similarity score used when filtering MMC4 matches. The example README run uses `0.24`; match the scale to your shard conversion pipeline. |
| `--mmc4_max_num_images` | `6` | Maximum images kept per MMC4 / ChatGPT sequence. |
| `--mmc4_min_num_images` | `1` | Minimum images required after filtering and truncation. |

### Data sizing rule

If the shard directory does not expose size metadata, the code requires explicit sample counts. Without `--dataset_resampled`, the shard count must also be at least `workers * world_size`.

## Optimization and training

| Flag | Default | Meaning |
| --- | --- | --- |
| `--batch_size_mmc4` | `128` | Per-process MMC4 batch size before gradient accumulation. |
| `--batch_size_laion` | `128` | Per-process LAION batch size before gradient accumulation. |
| `--gradient_accumulation_steps` | `1` | Accumulate gradients across N forward/backward passes before stepping the optimizer. |
| `--seed` | `42` | Base random seed; the code offsets it by rank. |
| `--learning_rate` | `1e-4` | AdamW learning rate. |
| `--lr_scheduler` | `constant` | Scheduler choice: `constant`, `linear`, or `cosine`. |
| `--loss_multiplier_mmc4` | `1.0` | Multiplier applied to MMC4 loss before backpropagation. |
| `--loss_multiplier_laion` | `1.0` | Multiplier applied to LAION loss before backpropagation. |
| `--warmup_steps` | `5000` | Warmup steps for the selected scheduler. |
| `--weight_decay` | `0.1` | AdamW weight decay. |
| `--precision` | `fp32` | Precision mode. Valid values: `amp_bf16`, `amp_bfloat16`, `bf16`, `fp16`, `fp32`. |
| `--gradient_checkpointing` | off | Enable gradient / activation checkpointing. |
| `--freeze_lm_embeddings` | off | Keep LM embeddings frozen instead of training the new special-token embeddings. |
| `--num_epochs` | `1` | Epoch budget. In this code, an epoch is a fixed sample budget, not a full pass over the raw dataset. |
| `--offline` | off | Set W&B and Transformers offline mode. |
| `--logging_steps` | `100` | Console loss logging interval. |

### Precision notes

- `amp_bf16` and `amp_bfloat16` both use bf16 autocast.
- `bf16` and `fp16` also affect the FSDP mixed-precision policy.
- `fp32` disables mixed precision in the training loop.

## Distributed launch

| Flag | Default | Meaning |
| --- | --- | --- |
| `--dist-url` | `env://` | Distributed init URL. |
| `--dist-backend` | `nccl` | Distributed backend. |
| `--horovod` | off | Use Horovod instead of native PyTorch distributed. |
| `--no-set-device-rank` | off | Do not map the CUDA device from local rank. Useful when each process already sees only one device. |
| `--fsdp` | off | Wrap the model in FullyShardedDataParallel. |
| `--fsdp_use_orig_params` | off | Recommended FSDP constructor option for param groups and gradient masking. |
| `--fsdp_sharding_strategy` | `full` | FSDP sharding strategy: `full` or `hybrid`. |

### FSDP notes

- `--fsdp_use_orig_params` is recommended. Without it, all embeddings become trainable instead of only the newly added special-token embeddings.
- The current FSDP wrapping strategy is not compatible with tied input/output embeddings. Freeze LM embeddings or use DDP for tied-embedding checkpoints.
- `hybrid` sharding has a torch 2.0.1 optimizer-state caveat; avoid it unless you know you need the patched state-dict path.
- `--fsdp_use_orig_params` is not a good fit for some OPT checkpoints; test carefully before committing a long run.

## Checkpointing and resume

| Flag | Default | Meaning |
| --- | --- | --- |
| `--run_name` | `openflamingo3B` | Save directory and W&B run name. |
| `--resume_from_checkpoint` | unset | Explicit checkpoint file to resume from. Must contain model, optimizer, and LR scheduler state. |
| `--delete_previous_checkpoint` | off | Remove the previous checkpoint after each successful save. |

### Checkpoint behavior

- If `run_name/` already exists and no explicit resume path is given, the script auto-resumes from the newest `checkpoint_*.pt` file in that directory.
- Saved checkpoints are named `checkpoint_<epoch>.pt`.
- The checkpoint contains `epoch`, `model_state_dict`, `optimizer_state_dict`, and `lr_scheduler_state_dict`.

## Logging and W&B

| Flag | Default | Meaning |
| --- | --- | --- |
| `--report_to_wandb` | off | Enable W&B logging on rank 0. |
| `--wandb_project` | unset | W&B project name. |
| `--wandb_entity` | unset | W&B entity or team name. |
| `--save_checkpoints_to_wandb` | off | Upload checkpoints to W&B after each save. Requires `--report_to_wandb`. |

### Logging notes

- W&B init happens only on rank 0.
- `--save_checkpoints_to_wandb` is rejected unless `--report_to_wandb` is also enabled.
- `--offline` sets both `WANDB_MODE=offline` and `TRANSFORMERS_OFFLINE=1`.

## Useful constraints to remember

- The training loop asserts that LAION and MMC4 produce the same number of batches per epoch.
- The code also asserts that the per-epoch sample budgets line up: `train_num_samples_laion // batch_size_laion == train_num_samples_mmc4 // batch_size_mmc4`.
- S3 shard URLs are rewritten to `pipe:aws s3 cp ... -` before loading.
