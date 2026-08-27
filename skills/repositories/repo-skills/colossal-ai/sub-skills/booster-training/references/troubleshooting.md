# Booster Training Troubleshooting

## Distributed setup

- Plugin constructor asserts distributed is not initialized: launch with `torchrun`/`colossalai run` and call `colossalai.launch_from_torch()` before constructing the plugin.
- NCCL backend errors: route to `../installation-and-launch/SKILL.md` for rendezvous, port, and GPU visibility checks.
- World size mismatch: ensure data/tensor/pipeline/expert parallel sizes multiply into the launched world size.

## Training loop errors

- Gradients not synchronized or loss does not decrease: check that model/optimizer were returned from `booster.boost`, and use `booster.backward`.
- Pipeline execution fails: define a criterion callable and use a dataloader iterator. Pipeline stages may only return loss on the final stage.
- Dataloader repeats or misses data: use `plugin.prepare_dataloader` or a correct distributed sampler with deterministic seed/drop behavior.
- `loss.backward()` error under ZeRO/Gemini: replace with `booster.backward(loss, optimizer)`.

## Memory and precision

- CUDA OOM before training: reduce batch/microbatch size, enable lazy initialization for large models, use Gemini placement/offload, reduce activation memory, or adjust topology.
- CUDA OOM during all-gather/reduce: reduce bucket sizes, disable aggressive overlap, or choose a different ZeRO/Gemini placement.
- FP16 overflow/underflow: inspect loss scaling knobs such as `initial_scale`, `min_scale`, `growth_factor`, `backoff_factor`, and `growth_interval`.
- FP8 or fused kernel errors: disable FP8/fused flags unless the backend and optional packages are explicitly verified.

## Optional dependency failures

- Apex fused normalization warning: install Apex from source only if fused RMSNorm is necessary.
- flash-attn import/build failure: use standard attention or a PyTorch SDPA path unless the model/workflow requires flash-attn.
- TensorNVMe warning for async save: set `use_async=False` or install TensorNVMe in an environment prepared for that feature.
- bitsandbytes or quantized LoRA errors: verify GPU architecture and package compatibility before enabling quantization.

## Checkpoint failures

- Missing shards or safetensors files: verify `shard`, `size_per_shard`, and checkpoint directory contents.
- Incompatible wrapped/unwrapped model: load with the same plugin/wrapper family or convert to a static torch model when supported.
- Low CPU memory load issues: try `low_cpu_mem_mode=False` for debugging if memory permits.
