# Configuration and CLI Troubleshooting

Use this guide for failures before or during `accelerate config`, `env`, `launch`, `test`, `estimate-memory`, `merge-weights`, and `to-fsdp2`.

## Missing Config

Symptoms:

- `FileNotFoundError` mentioning a passed configuration file.
- Launch unexpectedly uses cached defaults instead of the intended config.

Fixes:

1. Pass an explicit `--config_file path/to/config.yaml`.
2. If no config exists, create one with `accelerate config` or `accelerate config default --config_file path.yaml`.
3. Remember the default cache path precedence: `$HF_HOME/accelerate`, then `$XDG_CACHE_HOME/huggingface/accelerate`, then `~/.cache/huggingface/accelerate`.
4. For CI and schedulers, prefer project-local config files over relying on a user's cache.

## Invalid YAML or Unknown Keys

Symptoms:

- YAML parser errors.
- Accelerate error saying the config had unknown keys.
- Error saying `distributed_type` must be specified.

Fixes:

1. Run `python scripts/validate_accelerate_config.py path/to/config.yaml`.
2. Remove typo keys or move backend-specific options under their nested dictionary, such as `fsdp_config` or `deepspeed_config`.
3. Keep `compute_environment`, `distributed_type`, `mixed_precision`, `use_cpu`, and process placement keys at top level.
4. Run `accelerate config update --config_file path/to/config.yaml` after backing up a hand-edited config.

## CPU and Multi-GPU Conflicts

Symptoms:

- Error: only one of `--cpu`, `--multi_gpu`, `--tpu`, `--use_deepspeed`, and `--use_fsdp` can be used at a time.
- CPU launch still appears to read a GPU config.
- Multi-GPU launch errors because fewer than two processes or GPU ids were selected.

Fixes:

- CPU debug: use `accelerate launch --cpu --num_processes 1 train.py ...` or a config with `distributed_type: 'NO'` and `use_cpu: true`.
- Multi-GPU: set `--multi_gpu --num_processes N` with `N >= 2`, or use a config with `distributed_type: MULTI_GPU` and `num_processes >= 2`.
- If using `--gpu_ids`, provide at least two ids for same-machine multi-GPU or use `all`.

## Rendezvous and Machine Rank Mistakes

Symptoms:

- Distributed job hangs before training starts.
- Workers cannot connect to rank 0.
- Address already in use or connection timeout.

Fixes:

1. Make sure every node runs a launch command.
2. Set `machine_rank` uniquely from `0` to `num_machines - 1`.
3. Set `main_process_ip` to the rank-0 machine's reachable intranet IP when possible.
4. Use the same `main_process_port` on every node and ensure it is free on rank 0.
5. Verify `num_processes` is the total process count across all nodes.
6. For scheduler jobs, consider `--rdzv_backend c10d` and derive host information from the scheduler.

## Subprocess Tracebacks

Symptoms:

- A long launcher traceback hides the actual training-script exception.
- Distributed operations hang after tensor collectives.

Fixes:

- Add `--debug` to `accelerate launch` or set `debug: true` in config for better distributed diagnostics.
- Use `--quiet` to reduce subprocess stack noise for DeepSpeed and single-process configurations when the relevant exception is already visible.
- If a distributed collective hangs, check that tensors gathered or reduced across processes have matching shapes and that all ranks execute the same collective calls.

## SLURM Is Not Available

Symptoms:

- `scontrol: command not found` or `srun: command not found`.
- The user asks for a SLURM command on a non-SLURM workstation.

Fixes:

- Do not execute scheduler commands locally. Produce a batch script template and clearly mark scheduler variables such as `SLURM_NNODES`, `SLURM_JOB_NODELIST`, and `GPUS_PER_NODE`.
- Use a non-SLURM multi-node template for direct SSH/manual execution.
- Flatten multiline launcher strings before passing them through `srun`.

## Training-Script Argument Separation

Symptoms:

- Accelerate complains about an unknown argument intended for the training script.
- The training script receives missing or wrong arguments.

Fixes:

- Put Accelerate flags before the script/module/executable target.
- Put training-script flags after the target.
- Do not rely on `--` as the primary separator; Accelerate's parser boundary is the positional target.

Correct:

```bash
accelerate launch --num_processes 2 train.py --learning_rate 3e-4
```

Wrong:

```bash
accelerate launch --learning_rate 3e-4 --num_processes 2 train.py
```

## Command-Specific Failures

- `to-fsdp2`: ensure `--config_file` exists. Provide `--output_file` unless using `--overwrite`.
- `merge-weights`: ensure the checkpoint directory contains FSDP sharded weights and the machine has enough CPU RAM to load the full state dict.
- `estimate-memory`: install the selected model library, use `--library_name` when Hub metadata is missing, authenticate for private or gated repos, and avoid `--trust_remote_code` unless the repo is trusted.
- `test`: it actually launches subprocesses. Use it after config validation, not as a static check on shared login nodes.
