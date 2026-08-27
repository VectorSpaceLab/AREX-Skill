# Training API Reference

## Runtime Entry Points

- `deepspeed.initialize(args=None, model=None, optimizer=None, model_parameters=None, training_data=None, lr_scheduler=None, distributed_port=29500, mpu=None, dist_init_required=None, collate_fn=None, config=None, mesh_param=None, config_params=None)` returns `(engine, optimizer, training_dataloader, lr_scheduler)`.
- `model` is required. `config` may be a dictionary or config file path; `config_params` is a backwards-compatible alias.
- If `args.deepspeed_config` is set, do not also pass `config`; DeepSpeed asserts when both sources are present.
- `args.deepscale_config` is deprecated. New scripts should use `args.deepspeed_config` or pass `config=` directly.
- `deepspeed.init_distributed(...)` replaces direct `torch.distributed.init_process_group(...)` when distributed setup is needed before `initialize`. Otherwise `initialize` can initialize distributed state internally.

Minimal PyTorch integration:

```python
import deepspeed

engine, optimizer, train_loader, scheduler = deepspeed.initialize(
    model=model,
    model_parameters=model.parameters(),
    training_data=train_dataset,
    config=ds_config,
)

for batch in train_loader:
    loss = engine(batch)
    engine.backward(loss)
    engine.step()
```

## Config Objects

- `DeepSpeedConfig(config, mpu=None, mesh_device=None)` accepts a path or dictionary and validates the training batch contract.
- DeepSpeed parses JSON and HJSON-style config files in its runtime path. Duplicate JSON keys are invalid because later values silently override earlier intent in normal JSON tooling; the bundled validator rejects duplicates.
- Batch parameters are inferred when exactly two of the following are present: `train_batch_size`, `train_micro_batch_size_per_gpu`, and `gradient_accumulation_steps`.
- At runtime the configured effective batch must satisfy: `train_batch_size == train_micro_batch_size_per_gpu * gradient_accumulation_steps * world_size`.

## ZeRO Config Object

`DeepSpeedZeroConfig` is the model backing `zero_optimization`. Important fields include:

- `stage`: `0`, `1`, `2`, or `3`; `0` disables ZeRO.
- `contiguous_gradients`, `reduce_scatter`, `reduce_bucket_size`, `allgather_partitions`, `allgather_bucket_size`, `overlap_comm`: communication and memory behavior for ZeRO stages.
- `offload_optimizer`: CPU/NVMe optimizer offload for ZeRO stage 1, 2, or 3.
- `offload_param`: CPU/NVMe parameter offload, valid only with ZeRO stage 3.
- `sub_group_size`, `stage3_prefetch_bucket_size`, `stage3_param_persistence_threshold`, `stage3_max_live_parameters`, `stage3_max_reuse_distance`: ZeRO-3/Infinity memory controls.
- `stage3_gather_16bit_weights_on_model_save`: public config alias that maps to `gather_16bit_weights_on_model_save` and lets `save_16bit_model()` gather ZeRO-3-partitioned 16-bit weights.
- Deprecated aliases accepted by the runtime include `cpu_offload`, `cpu_offload_param`, `cpu_offload_use_pin_memory`, and `stage3_gather_fp16_weights_on_model_save`. Prefer modern fields in new configs.

## Engine Checkpoint Calls

- `engine.save_checkpoint(save_dir, tag=None, client_state=None, ...)` saves model, optimizer, scheduler, and client state.
- `engine.load_checkpoint(load_dir, tag=None, ...)` restores training state and returns the load path plus client state.
- All ranks must call checkpoint save/load collectives consistently. Calling save only on rank 0 can hang because other ranks also own optimizer/master-weight shards.
- `engine.save_16bit_model(output_dir, output_file=...)` is the direct 16-bit export path. With ZeRO-3, set `stage3_gather_16bit_weights_on_model_save: true` before expecting a consolidated weight file.
