# OpenFlamingo training troubleshooting

## Compatibility notes

Known-good dependency anchors from this codebase are:

- `torch==2.0.1`
- `transformers==4.31.0`
- `numpy<2`

The training path also depends on `wandb`, `webdataset`, `braceexpand`, `tqdm`, and `scipy` for MMC4 matching.

If `train.py` or the data loaders fail to import, verify that the training dependencies are installed before chasing a model bug.

## Missing shards or metadata

### Symptom

- `number of shards must be >= total workers`
- `Currently, number of dataset samples must be specified for training dataset`

### Fix

- Increase the shard count.
- Turn on `--dataset_resampled` if you want shard sampling with replacement.
- Provide both `--train_num_samples_laion` and `--train_num_samples_mmc4` when the shard directory has no size metadata.

## LAION / MMC4 batch mismatch

### Symptom

- `number of samples per epoch must be equal for mmc4 and laion`
- the two loaders finish at different times

### Fix

- Choose `batch_size_*` and `train_num_samples_*` values so that the floor-divided per-epoch batch counts match.
- Re-check that the sample budgets were copied correctly into both datasets.

## FSDP and tied embeddings

### Symptom

- runtime failures or poor behavior when a tied-embedding LM is wrapped with FSDP
- unexpected training of all LM embeddings

### Fix

- Use DDP instead of FSDP for tied-embedding checkpoints, or
- keep `--fsdp_use_orig_params` with `--freeze_lm_embeddings` for tied-embedding models.

## FSDP and OPT

### Symptom

- optimizer-state or param-group issues when using FSDP with OPT checkpoints

### Fix

- Avoid `--fsdp_use_orig_params` for OPT unless you have verified the exact checkpoint and torch build.
- If you only need a working run, use DDP.

## MPT label errors

### Symptom

- `forward()` or loss computation fails on MPT-1B checkpoints when labels are passed in

### Fix

- Use the modified MPT checkpoints that accept labels and compute cross-entropy in `forward()`.
- Do not assume the base MosaicML MPT-1B checkpoints are drop-in compatible with this training loop.

## W&B issues

### Symptom

- `save_checkpoints_to_wandb requires report_to_wandb`
- runs appear offline or do not show up in W&B

### Fix

- Add `--report_to_wandb` before `--save_checkpoints_to_wandb`.
- Set `--wandb_project` and `--wandb_entity` when you want named runs.
- Add `--offline` when the machine should not talk to external services.
- Remember that W&B initialization happens only on rank 0.

## NCCL and distributed launch hangs

### Symptom

- processes start but stall during collective setup
- NCCL warnings or timeouts appear in logs

### Fix

- Use `torchrun --standalone` for single-node launches.
- On Slurm, export `MASTER_ADDR` and `MASTER_PORT` before launching tasks.
- Set `NCCL_DEBUG=INFO` and `NCCL_ASYNC_ERROR_HANDLING=1` while debugging.
- Confirm that `CUDA_VISIBLE_DEVICES` matches the process-to-GPU mapping.
- Use `--no-set-device-rank` only when each process already sees exactly one GPU.

## Local import or PYTHONPATH issues

### Symptom

- `ModuleNotFoundError` for `data`, `distributed`, or `train_utils`

### Fix

- Launch the training file from a shell environment that can resolve the training directory.
- If you change the working directory or embed the script in another launcher, make sure the training directory is on `PYTHONPATH`.

## MMC4 similarity threshold confusion

### Symptom

- too many or too few MMC4 image-text matches
- the threshold works in one setup but not another

### Fix

- Match `--mmc4_textsim_threshold` to the similarity score scale produced by your MMC4 conversion pipeline.
- The code history includes both `30` and `0.24` as real values, so do not copy a threshold blindly across pipelines.

## Quick sanity checklist

Before a long run, confirm that:

- model and tokenizer checkpoints are reachable,
- LAION and MMC4 shard patterns are valid,
- sample budgets line up,
- the chosen precision is supported by the hardware,
- the launcher exports the expected distributed environment variables, and
- the command only enables W&B when you really want logging.
