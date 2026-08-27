# Core model and parallelism troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `WORLD_SIZE` mismatch or process group init failure | Launch world size does not equal TP×PP×CP×DP (+ compatible EP layout). | Recompute topology, set `--nproc-per-node`, `--nnodes`, and Megatron parallel flags consistently. |
| Attention head divisibility error | `num_attention_heads` not divisible by TP or query-group setting. | Choose TP that divides heads/query groups, or change model config. |
| Hidden/MLP tensor shape mismatch | Hidden size, FFN size, or vocab padding incompatible with TP. | Check `hidden_size % TP`, tokenizer/vocab padding, and output-layer sharing. |
| Pipeline stage has no layers or imbalanced layout | PP too high, layer count not divisible, or custom pipeline layout invalid. | Reduce PP or specify a valid `pipeline_model_parallel_layout`. |
| MoE expert/routing assertion | EP/ETP, number of experts, top-k, or dispatcher backend incompatible. | Verify expert count and dispatch backend; enable sequence parallel when combining TP and EP if required. |
| Stale process groups in tests | Previous test initialized Megatron groups and did not destroy them. | Destroy model-parallel state between independent tests; reinitialize Torch distributed only when needed. |
| `CUDA_DEVICE_MAX_CONNECTIONS` assertion | Variable set/unset incorrectly for TP/CP/FSDP/overlap mode. | Apply the decision table in `parallelism-reference.md`; do not use `1` with FSDP. |
| TransformerEngine/Apex fallback warning | Minimal environment lacks optional fused kernels. | Use local specs for CPU/lightweight checks; install compatible optional deps or container for TE/FP8 paths. |
| `GPTModel` deprecation warning | Current code warns GPTModel is critical-fixes-only. | For new architectures or migrations, use HybridModel guidance and the checkpointing/conversion route. |
| FSDP checkpoint load fails | Checkpoint format or optimizer state format mismatched with FSDP strategy. | Use `fsdp_dtensor` for Megatron-FSDP and route conversion/resume details to checkpointing. |

## Debug order

1. Capture the exact model config and resolved parallel sizes.
2. Capture the launch environment: ranks, world size, node count, GPUs per node.
3. Read the first non-NCCL Python traceback. Later NCCL timeouts are often downstream.
4. Check optional dependency warnings only after topology and shapes are correct.
5. If checkpoint loading is involved, route to checkpointing before changing model shapes.
