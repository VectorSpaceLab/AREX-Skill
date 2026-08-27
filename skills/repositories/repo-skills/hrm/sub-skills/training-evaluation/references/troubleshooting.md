# Training and Evaluation Troubleshooting

## CUDA dependency gate fails

Symptoms:

- `torch.cuda.is_available()` is false.
- FlashAttention import or tiny attention smoke fails.
- `adam_atan2_backend` import fails.

Recovery:

1. Use `check_training_env.py --require-cuda` to identify the missing piece.
2. Install a PyTorch CUDA build compatible with driver and GPU.
3. Install FlashAttention for the GPU generation and PyTorch/CUDA ABI.
4. Rebuild `adam-atan2` with a matching CUDA toolkit if its backend module is
   missing.
5. Do not proceed with real HRM train/eval verification on CPU-only evidence.

## W&B login or network issues

Symptoms:

- `wandb.init` blocks or fails before training.
- Hosted tracking credentials are missing.

Recovery:

- For production experiments, run `wandb login` first.
- For smoke/debug or offline environments, set `WANDB_MODE=offline`.
- Keep `project_name`, `run_name`, and `checkpoint_path` explicit if you need
  deterministic output locations.

## Hydra override errors

Symptoms:

- Unknown key errors or malformed override parsing.
- `Eval interval must be a divisor of total epochs.`

Recovery:

1. Use `python pretrain.py --help` to view composed config and valid groups.
2. Pass overrides as `key=value`, for example `arch.L_cycles=8`.
3. Ensure `epochs % eval_interval == 0`.
4. Ensure `global_batch_size` is divisible by distributed world size.

## Training yields no progress

Symptoms:

- Data loader produces no batches or training step count is lower than expected.

Likely causes:

- Dataset groups cannot fill `global_batch_size`, so the final short train batch
  is dropped.
- Wrong `data_path` or broken `group_indices` / `puzzle_indices`.

Recovery:

1. Validate the dataset with `validate_dataset_layout.py`.
2. Reduce `global_batch_size` for small debug datasets.
3. Check `metadata.total_groups` and `mean_puzzle_examples`; these determine
   total training steps.

## Checkpoint evaluation fails

Symptoms:

- Missing `all_config.yaml` next to checkpoint.
- Shape mismatch while loading weights.
- `checkpoint=<path>` was omitted or `evaluate.py --help` raises a validation
  error.

Recovery:

1. Pass `checkpoint=/full/or/relative/path/to/step_<N>`.
2. Ensure `all_config.yaml` is in the checkpoint directory.
3. Use the same converted dataset path referenced by the saved config, or edit
   `all_config.yaml` only with clear provenance.
4. If checkpoint keys contain `_orig_mod.`, the evaluator already tries to strip
   this prefix for `torch.compile` checkpoints.

## ARC post-processing reports missing shards or keys

Symptoms:

- `no prediction shards match <checkpoint>_all_preds.*`.
- Missing `logits`, `q_halt_logits`, `inputs`, `labels`, or
  `puzzle_identifiers`.

Recovery:

1. Run `evaluate.py checkpoint=<CHECKPOINT_PATH>` with default `save_outputs`,
   or include the required keys explicitly.
2. Pass `--checkpoint-prefix` without the `_all_preds.<rank>` suffix.
3. Use the matching ARC dataset root so `identifiers.json` aligns with saved
   puzzle ids.

## FlashAttention output stride error

Symptoms:

- Runtime error says `.view` is incompatible with tensor size/stride and suggests
  `.reshape(...)`.

Recovery:

- For a repo-editing task, patch `models/layers.py` to use `.reshape(...)` or
  `.contiguous().view(...)` after FlashAttention.
- For a usage-only task, try dependency versions known to match the repository.
- Treat the failed forward smoke as a real native verification issue until a
  bounded model forward passes.
