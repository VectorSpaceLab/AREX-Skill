# Memory and Backend Planning

## Memory facts

The repository states:

- NVIDIA CUDA GPU is required for actual HunyuanVideo generation.
- Single-GPU testing used an 80GB GPU.
- Approximate minimum peak memory is 60GB for `720x1280x129` and 45GB for `544x960x129`.
- 80GB is recommended for better generation quality and reliability.

If the user has a 40GB GPU, do not promise default 540p or 720p single-GPU success. Prefer lower settings, FP8, or multi-GPU xDiT if the optional stack is ready.

## Dependency variants

| Workflow | Required dependency/backend |
| --- | --- |
| Single-GPU generation | CUDA PyTorch 2.6.0, repo requirements, checkpoints. |
| Single-GPU memory offload | `accelerate` and a compatible CUDA/PyTorch stack; use `--use-cpu-offload`. |
| FP8 | CUDA PyTorch with FP8 dtype support, FP8 DIT weight, FP8 map. |
| xDiT multi-GPU | CUDA, NCCL, `xfuser==0.4.0`, flash-attn, valid torchrun world size. |
| Gradio UI | `gradio==5.0.0` plus the same generation backend. |

## CPU substitution

CPU can validate parser flags, checkpoint layout, and command strings. CPU cannot validate true HunyuanVideo generation, FP8 execution, xDiT attention, or video quality. Treat skipped GPU runs as unverified, not passed.
