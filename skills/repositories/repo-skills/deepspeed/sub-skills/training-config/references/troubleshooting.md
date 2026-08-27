# Training Config Troubleshooting

## Duplicate or Invalid Config

Symptoms:

- JSON parses in one tool but DeepSpeed appears to use an unexpected value.
- `DeepSpeedConfig` raises a validation or assertion error.
- HJSON syntax works in DeepSpeed but fails in a strict JSON parser.

Fixes:

- Run `scripts/validate_ds_config.py`; it rejects duplicate JSON keys and falls back to HJSON parsing only when `hjson` is installed.
- Keep runtime config as plain JSON when portability matters.
- Avoid providing both `args.deepspeed_config` and `config=` to `deepspeed.initialize`.

## Batch-Size Inference Errors

Symptoms:

- Error text says `train_batch_size` is not equal to `micro_batch_per_gpu * gradient_acc_step * world_size`.
- Only `gradient_accumulation_steps` is specified.
- Inferred micro-batch is zero or not divisible by `world_size`.

Fixes:

- For a fixed cluster size, compute `train_batch_size = micro * grad_acc * world_size`.
- For portable configs, specify `train_micro_batch_size_per_gpu` and `gradient_accumulation_steps`; let DeepSpeed infer the global batch.
- Re-run the validator with the actual launch world size.

## Deprecated ZeRO Aliases

Symptoms:

- Warnings about deprecated ZeRO format or CPU offload fields.
- Config uses `zero_optimization: true`, `cpu_offload`, `cpu_offload_param`, or `stage3_gather_fp16_weights_on_model_save`.

Fixes:

- Use `zero_optimization: {"stage": 1}` instead of boolean `true`.
- Use `offload_optimizer` instead of `cpu_offload`.
- Use `offload_param` instead of `cpu_offload_param`, and only with Stage 3.
- Use `stage3_gather_16bit_weights_on_model_save` instead of `stage3_gather_fp16_weights_on_model_save`.

## No Device Count or No Hostfile

Symptoms:

- Launcher falls back to local resources.
- Multi-node launch complains that `num_nodes > 1` but no extra nodes are available.
- Config validates locally but fails at the intended distributed world size.

Fixes:

- Provide a hostfile with `host slots=N` lines for multi-node jobs.
- Do not rely on `/job/hostfile` unless the scheduler creates it.
- Validate resource filters with `scripts/launcher_resource_preview.py` before launch.
- Check accelerator visibility separately before promising GPU slots.

## Mutually Exclusive Launcher Filters

Symptoms:

- `include_str and exclude_str are mutually exclusive`.
- `Cannot specify num_nodes/gpus with include/exclude`.
- A host or slot named in a filter is not found.

Fixes:

- Choose one of `--include`, `--exclude`, or `--num_nodes`/`--num_gpus`.
- Use `NODE[:SLOT[,SLOT...]][@NODE...]` syntax.
- Keep host names identical to the hostfile entries.

## Rank-0-Only Checkpoint Hangs

Symptoms:

- Training hangs when saving a checkpoint under distributed or ZeRO training.
- Only `global_rank == 0` calls `engine.save_checkpoint(...)`.

Fixes:

- Call `engine.save_checkpoint(...)` on every rank.
- Put only side effects such as external logging behind rank-0 checks.
- Keep `tag` and `client_state` schema consistent across ranks.

## ZeRO-3 Immediate Reload and Export Pitfalls

Symptoms:

- Reloading immediately after saving with the same ZeRO-3 engine fails or behaves unexpectedly.
- `save_16bit_model()` produces no consolidated weights.
- A normal `state_dict()` is missing full parameters under ZeRO-3.

Fixes:

- Treat ZeRO-3 checkpoints as sharded training state; reinitialize before resume when needed.
- Set `stage3_gather_16bit_weights_on_model_save: true` before `save_16bit_model()`.
- Use generated `zero_to_fp32.py` or `deepspeed.utils.zero_to_fp32` utilities for FP32 consolidation, with enough CPU RAM.

## Missing CUDA Toolkit for CUDA Op Probing

Symptoms:

- Environment checks or JIT op probing report missing `nvcc`, CUDA toolkit, ROCm compiler, or build tools.
- Training config work is blocked by extension diagnostics unrelated to config syntax.

Fixes:

- Separate config/launcher validation from op build diagnostics.
- For config-only planning, use the bundled scripts because they do not import DeepSpeed or compile ops.
- Route install, `ds_report`, CUDA/ROCm compiler, and extension build failures to `ops-tooling`.
