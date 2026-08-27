# Training troubleshooting

| Symptom | Diagnosis | Remedy |
|---|---|---|
| Dataset name not found | Registration module was not imported or name was prefixed | Import the registration module and compare the exact registry key. |
| `Unsupported train_backend` | Typo or unsupported config value | Use one of `ddp`, `deepspeed`, `fsdp`, `fsdp2`; select a supported recipe rather than fallback silently. |
| DeepSpeed/FSDP conflict | `train_backend=deepspeed` while `fsdp` is configured | Clear FSDP fields or explicitly select FSDP. |
| FSDP requires config | `fsdp` strategy is missing | Supply the FSDP strategy/profile and let backend defaults normalize its config. |
| FSDP2 unsupported | torch/accelerate/Transformers versions do not meet resolver gates | Upgrade only in an isolated environment or use a deliberately validated alternative; record the choice. |
| OOM at initialization | Model, image count, sequence length, or per-device batch is too large | Reduce batch/sequence/cameras, use gradient accumulation, or select an appropriate sharding strategy; do not claim the job is healthy until a CUDA smoke passes. |
| LoRA rejects backend | Recipe intentionally supports DDP only | Use DDP for that entrypoint and verify the adapter target modules. |
| Loss is NaN | Invalid data, bad normalization, precision issue, or empty labels | Validate data, inspect norm stats, run a short fp32/precision diagnostic, and confirm non-empty labels. |
| Resume cannot find model weights | FSDP checkpoint is sharded or output is incomplete | Inspect checkpoint contents and merge with the supported sharded-weight utility before inference. |
| Workers hang at startup | Launcher/world-size, NCCL, or inherited environment mismatch | Start with one GPU, set an explicit visible-device list, then scale; collect rank-0 and rank-failure logs. |
| Checkpoint loads but actions are wrong | Wrong model family, camera order, action dimension, or norm stats | Compare training and inference configs field-by-field; action semantics are not inferred safely from filenames. |
| WandB/remote logging blocks a smoke | Credentials/network are unavailable | Disable external logging for local validation; never add credentials to a skill workflow. |
