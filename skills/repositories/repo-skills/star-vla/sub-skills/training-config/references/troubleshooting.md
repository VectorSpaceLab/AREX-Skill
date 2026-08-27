# Training troubleshooting

Use this checklist when a StarVLA training plan, YAML override, or launch fails.

## Bad dotlist syntax or bare-string overrides

Symptoms:

- Override appears ignored.
- A boolean unexpectedly becomes `true`.
- Checkpoint/policy override raises `Expected KEY=VALUE` or `sequence of KEY=VALUE strings`.

Checks:

1. Prefer `--key=value` in training commands.
2. Use `KEY=VALUE` entries with the planner script.
3. Do not pass a bare string where a sequence/list of config overrides is required by checkpoint or policy-serving APIs.
4. Avoid empty shell-variable expansion after a key. Use `--trainer.freeze_modules=` or quote an empty value deliberately.
5. For repeated keys, remember the later OmegaConf value wins.

## Mismatched `action_horizon`, data indices, or dimensions

Symptoms:

- Action tensor shape mismatch.
- Model predicts a different action chunk length than the dataset provides.
- Serving metadata reports an unexpected action chunk size.

Checks:

1. Treat `framework.action_model.action_horizon` as canonical.
2. If `future_action_window_size` is present, it should equal `action_horizon - 1`.
3. Compare `action_horizon` against the dataset/data-config action index count.
4. Compare `action_dim` and `state_dim` against modality dimensions.
5. Route dataset registry, modality JSON, and key/index fixes to [data-integration](../../data-integration/SKILL.md).
6. Route serving-time action-chunk metadata issues to [policy-deployment](../../policy-deployment/SKILL.md).

## Missing `dataset_statistics.json`

Symptoms:

- A trained checkpoint cannot be served because statistics are missing.
- `PolicyNormProcessor` or policy wrapper cannot select an unnormalization key.
- `available_unnorm_keys` is empty or wrong.

Checks:

1. VLA dataloader construction should save `dataset_statistics.json` in `run_root_dir/run_id`.
2. If the file is missing, the job likely failed before VLA dataloader construction, used a VLM-only entry point, or wrote to a different `run_root_dir/run_id` than expected.
3. Confirm `datasets.vla_data.dataset_py`, `data_root_dir`, and `data_mix` with [data-integration](../../data-integration/SKILL.md).
4. Confirm the checkpoint directory and statistics file are kept together before serving with [policy-deployment](../../policy-deployment/SKILL.md).

## Unwanted W&B logging

Symptoms:

- The job tries to log online.
- W&B prompts, times out, or creates unwanted project runs.

Fixes:

```bash
export WANDB_MODE=disabled
# or
export WANDB_DISABLED=true
```

`train_starvla.py` and `train_starvla_cotrain.py` explicitly check these variables. `train_starvlm.py` still calls `wandb.init`, but W&B disabled mode prevents online logging.

## Distributed process group absent

Symptoms:

- `Default process group has not been initialized`.
- Rank-specific logic fails in a single-process smoke context.

Checks:

1. Source trainer utilities guard rank/barrier calls with `dist.is_initialized()` in the inspected paths.
2. If a custom script fails, inspect any added `dist.get_rank()` or `dist.barrier()` calls.
3. Do not use CPU smoke checks as proof that a full DeepSpeed training launch is valid.
4. If importing a training entry point only for inspection, remember the source creates an `Accelerator` at import time; prefer the planner script for dry-run command construction.

## DeepSpeed or GPU mismatch

Symptoms:

- NCCL timeout.
- DeepSpeed ZeRO stage errors.
- `no_sync` incompatibility with ZeRO partitioning.
- CUDA autocast or fused optimizer errors in CPU-only contexts.
- Number of processes does not match available devices.

Checks:

1. Match `--num_processes`, the Accelerate config, and available GPUs.
2. Confirm `distributed_type: DEEPSPEED` is intentional.
3. Choose ZeRO-2 or ZeRO-3 based on model size and memory budget.
4. Confirm BF16/FP16 support on the target hardware.
5. For co-training, preserve the source DeepSpeed-engine gradient accumulation pattern instead of wrapping ZeRO engines in `no_sync()`.
6. For CPU-only validation, restrict work to dry-run planning and CPU-safe tests; do not launch the CUDA-oriented trainers.

## flash-attn install failure

Symptoms:

- Install/build failure for `flash-attn`.
- Import failure when `framework.qwenvl.attn_implementation: flash_attention_2` is selected.
- CUDA/Torch/NVCC version mismatch.

Checks:

1. Align PyTorch, CUDA toolkit/NVCC, and `flash-attn` versions.
2. Use `pip install flash-attn --no-build-isolation` in a prepared StarVLA environment.
3. Source docs report `flash-attn==2.7.4.post1` as working with NVCC 12.0 and 12.4.
4. If the backend cannot support flash attention, ask [model-frameworks](../../model-frameworks/SKILL.md) whether the chosen framework can use another `attn_implementation`.
5. Treat flash-attn as an environment/backend issue, not a YAML syntax problem.

## Checkpoint reload or resume surprises

Symptoms:

- Resume starts from step 0.
- Partial reload prints missing module path or missing checkpoint prefix warnings.
- Optimizer state is not restored.

Checks:

1. For VLA-only latest resume, set `trainer.is_resume: true` and keep checkpoint files under `run_root_dir/run_id/checkpoints/` with source naming conventions.
2. For explicit warm-start, set `trainer.pretrained_checkpoint` to a specific weight file.
3. For partial warm-start, set `trainer.reload_modules` to comma-separated model module paths such as `action_model`.
4. Do not expect optimizer state restoration; source FAQ states optimizer state is not saved.
5. Ensure `save_format` is either `pt` or `safetensors`.
