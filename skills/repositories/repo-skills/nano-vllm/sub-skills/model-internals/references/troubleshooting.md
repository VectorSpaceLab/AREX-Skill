# Internals troubleshooting

| Symptom | Owning contract | Recovery |
| --- | --- | --- |
| FlashAttention import/build failure | `layers.attention` imports FlashAttention at module import time. | Fix the CUDA/PyTorch/FlashAttention environment before importing full nano-vLLM; a CPU-only stack cannot exercise this code. |
| Triton compile/runtime failure in KV-cache store | `store_kvcache` launches a Triton kernel with contiguous K/V assumptions. | Check tensor strides, slot mapping length, CUDA toolkit, and Triton compatibility. |
| `dist.get_rank()` or NCCL failure during layer construction | Tensor-parallel layers assume an initialized distributed process group. | Construct layers through `ModelRunner`, or initialize a process group in controlled tests. |
| Assertion on attention/KV heads | `Qwen3Attention` requires total heads and KV heads divisible by TP size. | Pick a compatible TP size or modify sharding logic deliberately. |
| Vocabulary embedding assertion | `VocabParallelEmbedding` requires `vocab_size % tensor_parallel_size == 0`. | Use a compatible TP degree or pad/handle vocabulary sharding explicitly. |
| Missing parameter in weight loader | Safetensors names do not match direct parameters or packed mapping fragments. | Add/adjust a packed mapping only after verifying source and target shapes. |
| Shape mismatch copying weight | Config dimensions and checkpoint tensor shapes disagree, or TP slice width is wrong. | Compare config fields, source tensor shape, target parameter shape, and rank slice. |
| Context fields are `None` in attention | `set_context` was not called before invoking attention. | Run through `ModelRunner.run`; do not call attention modules directly without setting context. |
| Device mismatch CPU/CUDA | Runner temporarily sets default device to CUDA; external tensors may still be CPU. | Move inputs/context tensors explicitly and avoid hidden tensor creation after default device reset. |
| Worker processes do not exit | Shared-memory loop did not receive `exit`, or rank 0 died first. | Ensure `llm.exit()` is called once and errors are handled so rank 0 can signal workers. |
