# Distributed Training Reference

This reference covers distributed and performance options for Transformers training workflows. Treat hardware details as user/project-specific: validate availability before recommending a launch command.

## Dependency Boundary

- `torch` is required for PyTorch training.
- `accelerate` is commonly required by modern `Trainer` device/distributed integration and by no-trainer scripts.
- `deepspeed` is required only for DeepSpeed runs.
- FSDP requires a compatible PyTorch distributed setup.
- XLA/TPU requires PyTorch/XLA and a TPU runtime.

If any dependency is absent, produce a clear install/skip decision rather than silently changing the training strategy.

## Single Process Baseline

Start with a small single-process smoke run whenever possible:

```bash
python ./train_task.py \
  --model_name_or_path MODEL \
  --do_train --do_eval \
  --max_train_samples 50 --max_eval_samples 50 \
  --output_dir outputs/smoke \
  --per_device_train_batch_size 2 \
  --per_device_eval_batch_size 2 \
  --save_strategy no \
  --report_to none
```

Expected signal: preprocessing completes, the model performs a few steps, loss is finite, and evaluation runs if requested.

## `torchrun` With Trainer Scripts

Use `torchrun` when the script uses `Trainer` and should run one process per GPU:

```bash
torchrun --nproc_per_node 8 ./train_task.py \
  --model_name_or_path MODEL \
  --do_train --do_eval \
  --output_dir outputs/distributed \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 8 \
  --bf16 \
  --eval_strategy steps --eval_steps 500 \
  --save_strategy steps --save_steps 500
```

Decision checks:

- Effective batch size is `per_device_train_batch_size * gradient_accumulation_steps * world_size`.
- Use `bf16` on supported modern GPUs; use `fp16` only when appropriate for the hardware and model.
- Ensure output storage is shared/visible as needed and not corrupted by multiple independent launches.
- Watch for port conflicts; set `--master_port` if needed.

## Accelerate No-Trainer Route

Use `accelerate launch` for scripts with a custom loop or names ending in `_no_trainer.py`:

```bash
accelerate config
accelerate test
accelerate launch ./train_task_no_trainer.py \
  --model_name_or_path MODEL \
  --dataset_name DATASET \
  --output_dir outputs/accelerate \
  --per_device_train_batch_size 2 \
  --per_device_eval_batch_size 2
```

Decision checks:

- `accelerate config` should match the actual machine count, GPU count, precision, and distributed type.
- No-trainer scripts expose fewer `TrainingArguments` conveniences; checkpointing, metrics, Hub push, and scheduler behavior may need explicit script flags.
- Prefer this route when custom optimizer/scheduler/loss logic is central to the request.

## Mixed Precision

Common choices:

- `bf16=True`: preferred on Ampere+ NVIDIA GPUs, many modern accelerators, and hardware with stable bfloat16 support.
- `fp16=True`: useful on older CUDA GPUs with fp16 support; may need loss scaling.
- `tf32=True`: can speed matmul on supported NVIDIA GPUs with acceptable numeric tradeoffs.
- Avoid setting both `fp16` and `bf16` unless the API explicitly supports the requested combination; generally pick one.

Validation signals:

- Hardware and `torch` report support.
- Loss remains finite during a tiny run.
- Evaluation metrics do not show obvious numeric instability.

## Memory Controls

Apply in this order for OOM mitigation:

1. Reduce `per_device_train_batch_size`.
2. Increase `gradient_accumulation_steps` to preserve effective batch size.
3. Enable `gradient_checkpointing=True` if the model supports it.
4. Use `dtype="auto"` at model load when weights are lower precision.
5. Use `bf16`/`fp16` when supported.
6. Reduce sequence/image/audio length or batch collator padding waste.
7. Consider `auto_find_batch_size=True` for Trainer-based experiments.
8. Consider FSDP, DeepSpeed, sharding, or quantization/PEFT routes for large models.

Cross-link: quantized or PEFT training belongs primarily in [quantization-integrations](../../quantization-integrations/SKILL.md), then return here for `TrainingArguments` and `Trainer` orchestration.

## `torch_compile`

`TrainingArguments` supports:

```python
TrainingArguments(
    output_dir="outputs/compiled",
    torch_compile=True,
    torch_compile_backend="inductor",
    torch_compile_mode="reduce-overhead",
)
```

Notes:

- Setting `torch_compile_backend` or `torch_compile_mode` can auto-enable compile.
- Compile can increase startup time and may fail for dynamic shapes or unsupported model code.
- Validate with a tiny fixed-shape run before using it in long jobs.
- Disable compile first when debugging correctness, custom losses, or distributed issues.

## FSDP

Use FSDP when model size exceeds single-device memory and PyTorch distributed is available.

Typical `TrainingArguments` shape:

```python
TrainingArguments(
    output_dir="outputs/fsdp",
    fsdp="full_shard auto_wrap",
    fsdp_config={
        "transformer_layer_cls_to_wrap": "DecoderLayerClassName",
        "activation_checkpointing": True,
    },
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
)
```

Decision checks:

- Confirm the transformer layer class name for auto wrapping.
- Keep config as a dict or JSON file path in the user's project.
- Validate checkpoint save/load behavior before a long run.
- FSDP can interact with gradient checkpointing, mixed precision, and CPU offload; change one major knob at a time.

## DeepSpeed

Use DeepSpeed for ZeRO optimization, optimizer offload, or very large model training when `deepspeed` is installed.

Typical `TrainingArguments` shape:

```python
TrainingArguments(
    output_dir="outputs/deepspeed",
    deepspeed="ds_config.json",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
)
```

Decision checks:

- The DeepSpeed JSON and `TrainingArguments` batch sizes must agree or intentionally use `auto` fields.
- ZeRO stage, optimizer offload, parameter offload, and fp16/bf16 settings should match hardware memory and speed goals.
- Save/resume behavior differs by ZeRO stage; test checkpoint restoration early.
- DeepSpeed failures often come from version mismatch, invalid JSON, unavailable CUDA ops, or inconsistent batch-size math.

## Checkpoint And Resume In Distributed Runs

Trainer route:

```python
trainer.train(resume_from_checkpoint="outputs/run/checkpoint-1000")
```

Script route:

```bash
python ./train_task.py ... --resume_from_checkpoint outputs/run/checkpoint-1000
```

Checklist:

- Resume path points to a checkpoint directory, not just the output root unless the script supports auto-detection.
- Optimizer/scheduler states exist if the goal is exact continuation.
- Distributed strategy and world size are compatible with the checkpoint format.
- `save_total_limit` did not prune the needed checkpoint.
- If `load_best_model_at_end=True`, the best checkpoint may be retained even with tight save limits.

## Launch Debugging

Common symptoms and actions:

- Hang at startup: check `torchrun` rendezvous settings, ports, GPU visibility, and world size.
- Rank-specific crash: inspect the first failing rank; later ranks may only show communication teardown.
- NCCL errors: verify driver/CUDA compatibility, network interfaces, and consistent environment variables.
- DeepSpeed config error: validate JSON and batch-size relationships.
- FSDP wrapping error: correct layer class names or disable auto-wrap temporarily.
- OOM only in distributed: check per-rank batch size, duplicated model copies, activation checkpointing, and offload settings.

## Reporting Back

For distributed recommendations, include:

- Launch command (`python`, `torchrun`, or `accelerate launch`).
- Required packages and hardware assumptions.
- Effective batch size calculation.
- Precision choice and fallback.
- Checkpoint/resume plan.
- One small smoke run before full training.
