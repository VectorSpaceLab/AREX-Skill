# Distributed training guidance

This reference covers the runtime pieces that sit around the data loader: custom samplers, checkpoint resume, optimizer selection, DeepSpeed config, and the optional Megatron fused-kernel path.

## Resume-safe data loading

`UniversalDataModule` computes consumed samples from either the lightning module or the current trainer state. The resume path only works correctly when the sampler and checkpoint logic stay consistent.

| Piece | What it does | Why it matters |
|---|---|---|
| `get_consume_samples` | Derives how many samples were already seen | Prevents repeated batches after resume. |
| `PretrainingSampler` | Sequential sampler for pretraining-style data | Used when the run should continue in order. |
| `PretrainingRandomSampler` | Randomized sampler with epoch-aware shuffling | Used when the run should resume and still reshuffle safely. |
| `replace_sampler_ddp=False` | Keeps the custom sampler instead of letting Lightning replace it | Required for resume-aware pretraining loaders. |

### Practical rule

If the data module owns `batch_sampler`, keep `replace_sampler_ddp=False`. If you let Lightning replace the sampler, the consumed-sample accounting in the pretraining loaders stops matching the actual batch order.

## Optimizer and scheduler selection

`model_utils.configure_optimizers` chooses the optimizer from the active strategy and the deepspeed config.

| Condition | Optimizer chosen | Meaning |
|---|---|---|
| No DeepSpeed strategy | `AdamW` | Standard non-DeepSpeed training path. |
| DeepSpeed with `offload_optimizer` in `zero_optimization` | `DeepSpeedCPUAdam` | CPU-offloaded optimizer state. |
| DeepSpeed without optimizer offload | `FusedAdam` | GPU-side fused optimizer path. |

The scheduler is selected from `scheduler_type` and uses `warmup_steps` / `warmup_ratio` plus `lr_decay_steps` / `lr_decay_ratio`. `inverse_sqrt` is the special case that uses `warmup_min_lr` and `warmup_max_lr`.

## DeepSpeed configuration paths

Some entry points pass an external config file through `--deepspeed`; others set `PL_DEEPSPEED_CONFIG_PATH` directly. Treat that JSON as runtime policy, not as part of the data shape.

### Typical config knobs

- `zero_optimization.stage`
- `offload_optimizer.device`
- `offload_param.device`
- `fp16.enabled`
- `train_micro_batch_size_per_gpu`
- `gradient_clipping`
- `activation_checkpointing`

### What to preserve when reading a shell script

- the micro-batch size,
- the ZeRO stage,
- whether the optimizer is offloaded,
- whether activation checkpointing is enabled,
- the external config path or environment variable.

## The custom Megatron + DeepSpeed wrapper

The repo ships a custom strategy class named `megatron_deepspeed`. It extends the DeepSpeed strategy and adds Megatron-style model parallel initialization.

### Responsibilities of the wrapper

- enforce that DeepSpeed is installed,
- load the fused CUDA kernels,
- set up pipe / data / model parallel topology,
- initialize the Megatron `mpu`,
- configure activation checkpointing when the config asks for it,
- pass the `mpu` object into `deepspeed.initialize`.

### When to use it

Use the wrapper only when the run needs both DeepSpeed and Megatron-style model parallelism. For ordinary single-node fine-tuning, the normal Lightning DeepSpeed strategy is simpler.

## Optional Megatron fused kernels

The fused-kernel loader tries to import compiled CUDA extensions such as `scaled_masked_softmax_cuda` and `scaled_upper_triang_masked_softmax_cuda`. If they are missing, the loader prints an install hint and exits.

### Build prerequisites

- a matching CUDA toolkit,
- `nvcc` in `CUDA_HOME`,
- a compatible PyTorch build,
- permission to compile C++ / CUDA extensions.

### What counts as success

You have optional kernel support only if the compiled extension modules import cleanly. If the modules are missing, the rest of the skill still works, but the Megatron fused-kernel path is unverified.

## Distributed runtime checklist

1. Decide whether you need plain Lightning, Lightning + DeepSpeed, or the Megatron wrapper.
2. Keep custom samplers and `replace_sampler_ddp=False` together.
3. Keep checkpoint resume and consumed-sample accounting together.
4. Keep optimizer choice aligned with the deepspeed offload policy.
5. Keep fused kernels optional unless you have a CUDA build environment.

## Failure signatures and meaning

| Symptom | Likely meaning | What to check |
|---|---|---|
| `ImportError` for `DeepSpeedCPUAdam` / `FusedAdam` | DeepSpeed is missing or not importable | Verify the package install first, then inspect the optimizer path. |
| `fused kernels configured but not installed` | The optional CUDA extension is absent | Build the extension only if you truly need the Megatron path. |
| repeated batches after resume | Sampler / resume state mismatch | Preserve consumed-sample accounting and custom sampler behavior. |
| checkpoint path silently disappears | `load_ckpt_path` points to a missing directory | Create the path or remove the resume option before launching. |

## Related references

- [training-arguments.md](training-arguments.md)
- [pretraining-workflows.md](pretraining-workflows.md)
- [troubleshooting.md](troubleshooting.md)
