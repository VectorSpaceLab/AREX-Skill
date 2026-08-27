# Motus cross-cutting troubleshooting

| Surface | Symptom | Recovery |
|---|---|---|
| Install | Python/CUDA wheel or flash-attn import mismatch | Use Python 3.10 and a torch/CUDA build supported by the GPU; treat flash-attn as optional performance acceleration and use the SDPA fallback when available. |
| Import | Heavy warnings from DeepSpeed/CUDA extension probes | Separate parser/import warnings from runtime failure; check torch CUDA and DeepSpeed only when the selected workflow needs them. |
| Assets | Missing config, VAE, WAN, Qwen, or Motus checkpoint | Verify every configured directory and checkpoint format before model construction; no random-weight fallback is equivalent to a pretrained result. |
| Data | Empty loader or tensor shape mismatch | Validate the selected dataset layout, episode resource basenames, sampling span, action dimension, and text/embedding alignment. |
| Memory | OOM during inference/training | Use pre-encoded T5, reduce process count/batch size only when the config remains semantically valid, and match documented VRAM requirements. |
| External runtime | RoboTwin/LeRobot unavailable or incompatible | Keep those integrations explicit; verify their own version, root, metadata, and permissions before invoking Motus adapters. |
| Logging | WandB prompts or connection failures | Choose `tensorboard` or `none` for isolated checks; use WandB only with credentials/network and an explicit project. |

A successful source import does not prove CUDA model execution. Preserve
unavailable checkpoints, datasets, external runtimes, or required hardware as
visible blockers in verification notes.
