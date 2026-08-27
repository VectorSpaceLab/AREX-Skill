# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: tutel` or top-level `from tutel import system` fails | Tutel is not installed | Install Tutel in a CUDA-capable environment or avoid Swin-MoE workflows |
| CPU probe passes but MoE fails | CPU is not a substitute for Tutel/CUDA distributed MoE | Use GPU runtime verification before claiming MoE support |
| `swin_window_process` import failure | CUDA extension not built or ABI mismatch | Omit `--fused_window_process` or build the extension against the active PyTorch/CUDA stack |
| `nvcc` not found during extension build | CUDA toolkit compiler missing | Install a compatible toolkit or use pure PyTorch fallback |
| Apex fused optimizer/layernorm import error | Apex not installed or mismatched with torch/CUDA | Use AdamW/LayerNorm fallback or install a matching Apex build |
| MoE checkpoint rank file not found | Resume path includes a rank suffix or shards are incomplete | Use the base checkpoint path expected by the utilities and ensure every rank shard is present |
| Distributed hang | Wrong `--nnodes`, `--node_rank`, `--master_addr`, or `--master_port` | Verify all ranks see the same rendezvous settings and data paths |

Do not patch these by changing generated skill claims. Record missing optional backends as unverified unless a real CUDA/Tutel/Apex/fused-kernel smoke passes.
