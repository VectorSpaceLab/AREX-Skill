# OpenFlamingo training workflows

These are launch templates only. They are not executed here.

The examples use this sub-skill's bundled `scripts/run_training_entrypoint.py` wrapper, which locates the installed OpenFlamingo package and fixes its local import path before handing arguments to the packaged training entrypoint.

## 1) Single-node, 4-GPU DDP, no W&B

Use this when you want the simplest multi-GPU launch and do not want to report to W&B.

```bash
torchrun --standalone --nnodes=1 --nproc_per_node=4 scripts/run_training_entrypoint.py \
  --vision_encoder_path ViT-L-14 \
  --vision_encoder_pretrained openai \
  --lm_path <LM_PATH> \
  --tokenizer_path <TOKENIZER_PATH> \
  --cross_attn_every_n_layers 1 \
  --dataset_resampled \
  --batch_size_mmc4 32 \
  --batch_size_laion 64 \
  --train_num_samples_mmc4 125000 \
  --train_num_samples_laion 250000 \
  --loss_multiplier_laion 0.2 \
  --workers 4 \
  --run_name <RUN_NAME> \
  --num_epochs 480 \
  --warmup_steps 1875 \
  --mmc4_textsim_threshold 0.24 \
  --precision bf16 \
  --gradient_checkpointing \
  --laion_shards "/path/to/laion/shard-{0000..0999}.tar" \
  --mmc4_shards "/path/to/mmc4/shard-{0000..0999}.tar"
```

Notes:

- Omit `--report_to_wandb` for a local-only run.
- Keep the LAION and MMC4 sample budgets aligned so the batch counts match.
- If bf16 is not available on your hardware, switch to `--precision fp16` or `--precision fp32`.

## 2) FSDP launch with tied-embedding safeguards

Use this when memory pressure is high and your LM is compatible with the current FSDP wrapping strategy.

```bash
torchrun --standalone --nnodes=1 --nproc_per_node=8 scripts/run_training_entrypoint.py \
  --vision_encoder_path ViT-L-14 \
  --vision_encoder_pretrained openai \
  --lm_path <LM_PATH> \
  --tokenizer_path <TOKENIZER_PATH> \
  --cross_attn_every_n_layers 1 \
  --dataset_resampled \
  --batch_size_mmc4 16 \
  --batch_size_laion 32 \
  --train_num_samples_mmc4 62500 \
  --train_num_samples_laion 125000 \
  --workers 4 \
  --run_name <RUN_NAME> \
  --num_epochs 480 \
  --fsdp \
  --fsdp_use_orig_params \
  --fsdp_sharding_strategy full \
  --freeze_lm_embeddings \
  --precision bf16 \
  --report_to_wandb \
  --wandb_project <PROJECT> \
  --wandb_entity <ENTITY> \
  --laion_shards "/path/to/laion/shard-{0000..0999}.tar" \
  --mmc4_shards "/path/to/mmc4/shard-{0000..0999}.tar"
```

Notes:

- If the LM ties input and output embeddings, keep `--freeze_lm_embeddings` on or use DDP.
- `--fsdp_use_orig_params` is the recommended FSDP setting here.
- Avoid `--fsdp_sharding_strategy hybrid` unless you have a reason to patch the torch 2.0.1 optimizer-state path.

## 3) Slurm-derived launch template

The training script can read `SLURM_*` environment variables directly. Export a rendezvous address and launch one process per GPU.

```bash
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --gpus-per-task=1

export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=15000
export PYTHONFAULTHANDLER=1
export NCCL_ASYNC_ERROR_HANDLING=1

srun --cpu_bind=v --accel-bind=gn \
  python scripts/run_training_entrypoint.py \
    --vision_encoder_path ViT-L-14 \
    --vision_encoder_pretrained openai \
    --lm_path <LM_PATH> \
    --tokenizer_path <TOKENIZER_PATH> \
    --cross_attn_every_n_layers 1 \
    --dataset_resampled \
    --batch_size_mmc4 32 \
    --batch_size_laion 64 \
    --train_num_samples_mmc4 125000 \
    --train_num_samples_laion 250000 \
    --workers 4 \
    --run_name <RUN_NAME> \
    --laion_shards "/path/to/laion/shard-{0000..0999}.tar" \
    --mmc4_shards "/path/to/mmc4/shard-{0000..0999}.tar"
```

Notes:

- The script uses `SLURM_PROCID`, `SLURM_LOCALID`, and `SLURM_NTASKS` when present.
- If you manually pin each task to one visible GPU, `--no-set-device-rank` can help.
- Keep `MASTER_ADDR` and `MASTER_PORT` set before `srun` starts.

## 4) Resume workflow

```bash
torchrun --standalone --nnodes=1 --nproc_per_node=4 scripts/run_training_entrypoint.py \
  --lm_path <LM_PATH> \
  --tokenizer_path <TOKENIZER_PATH> \
  --laion_shards "/path/to/laion/shard-{0000..0999}.tar" \
  --mmc4_shards "/path/to/mmc4/shard-{0000..0999}.tar" \
  --run_name <RUN_NAME> \
  --resume_from_checkpoint <PATH_TO_CHECKPOINT>
```

If you omit `--resume_from_checkpoint` and the run directory already has checkpoints, the script auto-resumes from the newest `checkpoint_*.pt` file.
