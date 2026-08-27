# Configuration Guide

## Batch-Size Contract

DeepSpeed uses three training batch parameters:

- `train_batch_size`: global effective batch for one optimizer update.
- `train_micro_batch_size_per_gpu`: per-rank batch for one forward/backward micro-step.
- `gradient_accumulation_steps`: number of micro-steps before an optimizer update.

The runtime contract is:

```text
train_batch_size = train_micro_batch_size_per_gpu * gradient_accumulation_steps * world_size
```

Authoring guidance:

- Specify two of the three values and let DeepSpeed infer the third when practical.
- If all three are specified, ensure divisibility and exact equality for the intended `world_size`.
- If only `train_batch_size` or only `train_micro_batch_size_per_gpu` is specified, DeepSpeed assumes `gradient_accumulation_steps = 1` and infers the other value from `world_size`.
- Do not specify only `gradient_accumulation_steps`; DeepSpeed requires one of the batch sizes.

Run the bundled validator before launching:

```bash
python scripts/validate_ds_config.py --world-size 8 ds_config.json
```

## Minimal Training Config

```json
{
  "train_micro_batch_size_per_gpu": 4,
  "gradient_accumulation_steps": 2,
  "optimizer": {
    "type": "Adam",
    "params": {
      "lr": 0.00015
    }
  },
  "bf16": {
    "enabled": true
  }
}
```

For 8 ranks, this infers `train_batch_size = 64`.

## Precision, Optimizer, and Scheduler

- Use `bf16.enabled` when the accelerator supports BF16; use `fp16.enabled` when FP16 mixed precision is intended.
- `optimizer.type` may name DeepSpeed-supported optimizers such as `Adam`, `AdamW`, `OneBitAdam`, `Lamb`, `OneBitLamb`, or `Muon`, or a compatible torch optimizer name.
- Optimizer `params` keys must match the selected optimizer constructor and DeepSpeed-specific options.
- When a scheduler is supplied in the DeepSpeed config or passed into `initialize`, DeepSpeed calls scheduler `step()` at each `engine.step()`.
- If the intended schedule advances at an epoch or custom interval, do not hand that scheduler to DeepSpeed; manage it explicitly in the training script.

## ZeRO Stage Selection

- Stage 0: no ZeRO; use for small models or debugging.
- Stage 1: partitions optimizer states; often the first memory-saving step.
- Stage 2: partitions optimizer states and reduced gradients; common default for large data-parallel training.
- Stage 3: partitions optimizer states, gradients, and parameters; required for the largest models and for parameter offload.

Typical Stage 2 skeleton:

```json
{
  "zero_optimization": {
    "stage": 2,
    "contiguous_gradients": true,
    "overlap_comm": true,
    "reduce_scatter": true,
    "reduce_bucket_size": 500000000,
    "allgather_bucket_size": 500000000
  }
}
```

Typical Stage 3 CPU offload skeleton:

```json
{
  "zero_optimization": {
    "stage": 3,
    "contiguous_gradients": true,
    "reduce_bucket_size": 10000000,
    "stage3_prefetch_bucket_size": 10000000,
    "stage3_param_persistence_threshold": 100000,
    "stage3_max_live_parameters": 1000000000,
    "stage3_max_reuse_distance": 1000000000,
    "sub_group_size": 1000000000,
    "offload_optimizer": {"device": "cpu"},
    "offload_param": {"device": "cpu"}
  }
}
```

## ZeRO and Offload Pitfalls

- Prefer object form for `zero_optimization`; boolean `true` is a deprecated format that maps to Stage 1.
- Replace deprecated `cpu_offload: true` with `offload_optimizer: {"device": "cpu"}`.
- Replace deprecated `cpu_offload_param: true` with `offload_param: {"device": "cpu"}` and use it only with Stage 3.
- Replace deprecated `stage3_gather_fp16_weights_on_model_save` with `stage3_gather_16bit_weights_on_model_save`.
- NVMe offload requires a deliberate `nvme_path`, sufficient host memory, and storage bandwidth planning; do not add NVMe offload as a blind default.
- For Muon with ZeRO-3 and NVMe offload, consider `save_muon_momentum_buffer_in_memory: true` when preserving momentum buffer behavior is required.
