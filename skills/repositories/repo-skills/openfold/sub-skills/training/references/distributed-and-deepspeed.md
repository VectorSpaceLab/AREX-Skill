# Distributed Training and DeepSpeed

## Strategy Selection

`train_openfold.py` chooses strategy from flags:

- If `--deepspeed_config_path` is set, it builds a Lightning `DeepSpeedStrategy` using that JSON.
- Else if `--gpus > 1` or `--num_nodes > 1`, it builds a Lightning DDP strategy with `find_unused_parameters=False`.
- Else it uses the default single-process strategy.
- If `--mpi_plugin` is set, it passes an MPI cluster environment to the strategy.

OpenFold raises an error when distributed training is requested without `--seed`. Treat `--seed` as mandatory for every multi-GPU or multi-node command.

## Precision Rules

- The training script default precision is `bf16`.
- The docs recommend BF16 on A100-class GPUs.
- The script rejects `--precision 16` together with `--deepspeed_config_path`.
- DeepSpeed config precision (`fp16`, `bfloat16`, or `amp`) must be consistent with the Lightning precision flag and hardware support.
- CPU-only training is not a viable fallback for OpenFold training.

For A100 DeepSpeed training, a safe planning default is a DeepSpeed JSON with `bfloat16.enabled: true`, ZeRO stage 2, activation checkpointing, and no FP16/AMP block enabled.

## DeepSpeed Config Generation

Use the bundled helper:

```bash
python scripts/build_deepspeed_config.py --bfloat16 --zero-stage 2 --offload-optimizer --partition-activations --gradient-clipping 0.1 --output deepspeed_config.json
```

The helper is standalone and deterministic. It exposes only common safe settings and validates that at most one precision mode is enabled.

Minimal BF16 config shape:

```json
{
  "bfloat16": {"enabled": true},
  "zero_optimization": {"stage": 2},
  "activation_checkpointing": {"partition_activations": true, "cpu_checkpointing": false, "profile": false}
}
```

Add `--deepspeed_config_path PATH_TO_JSON` to the training command. When W&B is enabled, the training script attempts to save the DeepSpeed config as a run artifact.

## Multi-Node and MPI

For multi-node runs:

- Set `--num_nodes` to the number of participating nodes and `--gpus` to GPUs per node.
- Include `--seed`.
- Ensure the scheduler launches one worker per GPU with the environment variables expected by Lightning/PyTorch or MPI.
- Use `--mpi_plugin` only when `mpi4py` and the MPI runtime are installed and the job is launched under MPI.
- Keep training data, alignments, templates, caches, checkpoints, and DeepSpeed config on paths visible to all nodes.

The original repository includes Slurm examples, but this generated skill does not depend on them. Treat scheduler scripts as cluster-specific wrappers around the command planned here.

## Effective Batch and Accumulation

OpenFold uses `num_nodes * gpus` to compute global batch size for performance logging. Use `--accumulate_grad_batches` when a user needs a larger effective batch without increasing per-GPU memory. Any change to batch behavior should be paired with a config/learning-rate review.

## DeepSpeed Checkpoint Notes

- A full DeepSpeed resume may use a checkpoint directory with a `latest` file that points to the current tag.
- Fine-tuning from DeepSpeed weights can use `--resume_from_ckpt DS_CHECKPOINT_DIR --resume_model_weights_only true` so OpenFold extracts FP32 weights from the ZeRO checkpoint.
- Do not assume a single `.ckpt` file exists for DeepSpeed runs.
