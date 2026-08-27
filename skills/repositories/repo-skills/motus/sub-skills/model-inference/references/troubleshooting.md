# Inference troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA unavailable or `torch.amp.autocast` failure | CPU torch, hidden GPUs, incompatible driver/runtime, or wrong device | Check torch CUDA availability, device count, compute capability, and the documented CUDA wheel before loading weights. |
| Out-of-memory with real-world inference | Runtime T5 encoder, too many processes, or mismatched resolution | Use pre-encoded T5 embeddings, one process/GPU, the correct embodiment resolution, and free other allocations. |
| Missing `mp_rank_00_model_states.pt` | Wrong checkpoint level or incomplete download | Point at the checkpoint directory containing the expected rank file or select the intended file; do not initialize random weights as a substitute. |
| Missing WAN config/VAE/T5/VLM files | `wan_path` or model config points at the wrong asset family | Preflight every configured path and match Motus/Wan/Qwen checkpoint generations. |
| Checkpoint loads with missing/unexpected keys | Stage mismatch or wrong loader | Use full loading for a matching Motus checkpoint; use pretrain loading only for the documented finetune transition and inspect counts. |
| Poor action or frame result | Wrong embodiment YAML, three-view layout, instruction embedding, normalization, or checkpoint | Recheck config/checkpoint pairing, image layout, action statistics, T5 choice, and input state dimensions. |
| Flash-attn import/build error | Optional extension ABI/toolkit mismatch | Use the repository's scaled-dot-product fallback for correctness, or install a flash-attn build matching torch/Python/CUDA for performance. |
| RoboTwin policy cannot start | External simulator version/root/policy path is wrong | Validate the simulator installation and copied policy layout separately; run a single task with a tiny evaluation budget first. |
| Help command triggers dependency warnings | Heavy model modules probe optional DeepSpeed/CUDA extensions at import | Treat warnings as import diagnostics; distinguish a successful parser from a successful model run. |

CPU imports and CLI help are useful static gates but cannot verify actual Motus
inference. Missing checkpoints, datasets, or RoboTwin are explicit blockers.
