# Gemini, ZeRO, Checkpointing, and LoRA

## Low-level ZeRO

`LowLevelZeroPlugin(stage=1|2)` wraps ZeRO-1/2 optimizer behavior. Use it when optimizer states or gradients dominate memory but full parameter sharding is not needed.

Common knobs:

- `stage`: 1 or 2.
- `precision`: often `fp16` for CUDA training.
- `reduce_bucket_size_in_m`: communication bucket size.
- `overlap_communication`: overlap gradient communication.
- `cpu_offload`: offload optimizer state/gradients to CPU at a performance cost.
- `master_weights`: maintain FP32 master weights.

## Gemini / ZeRO-3-style memory management

`GeminiPlugin` and low-level `GeminiDDP` manage parameter, gradient, and optimizer state placement with chunk-based memory management.

Useful knobs:

- `placement_policy`: static/cuda/cpu/auto-style placement behavior depending on version support.
- `shard_param_frac`, `offload_optim_frac`, `offload_param_frac`: tune memory movement and offload.
- `min_chunk_size_m`, `search_range_m`, `hidden_dim`: tune chunk search and memory granularity.
- `pin_memory`, `enable_async_reduce`, `gpu_margin_mem_ratio`: performance and memory tradeoffs.
- `enable_flash_attention`, `enable_fused_normalization`, `enable_sequence_parallelism`: optional acceleration flags that require matching dependencies.

For Gemini-managed models, prefer Booster/optimizer APIs for backward and checkpointing rather than ordinary PyTorch calls.

## Checkpointing

`Booster.save_model` supports:

```python
booster.save_model(model, checkpoint, shard=True, gather_dtensor=True, size_per_shard=1024, use_safetensors=True, use_async=False)
```

`Booster.save_optimizer` supports sharded optimizer checkpoints and async save. Async save can require TensorNVMe. Use ordinary synchronous saves until async dependencies are installed and tested.

Load with:

```python
booster.load_model(model, checkpoint, strict=True, low_cpu_mem_mode=True)
booster.load_optimizer(optimizer, checkpoint, low_cpu_mem_mode=True)
```

## LoRA

`Booster.enable_lora(model, pretrained_dir=None, lora_config=None, bnb_quantization_config=None, quantize=False)` wraps a model with LoRA modules when PEFT and optional quantization dependencies are available. Save adapter-only outputs with `save_lora_as_pretrained`.

Do not mix LoRA, quantization, and distributed checkpointing until each dependency is installed and a tiny smoke has passed.
