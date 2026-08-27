# Setup Troubleshooting

## Missing model root

Symptom:

```text
ValueError: `models_root` not exists: <path>
```

Cause: `--model-base` points to a missing directory. Create/download the checkpoint root or pass the correct path. Validate with:

```bash
python sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base <path>
```

## Inconsistent `MODEL_BASE` and `--model-base`

The constants for VAE/text encoder paths read `MODEL_BASE` at import time, while sampling code also uses `--model-base` for the root passed into `from_pretrained`. If you customize paths, set them consistently:

```bash
MODEL_BASE=/models/hunyuan-video python sub-skills/inference/scripts/run_sample_video.py --repo-root <hunyuan-video-source-root> --model-base /models/hunyuan-video ...
```

## Missing VAE or text encoder files

- `VAE checkpoint not found` means the VAE folder is missing `pytorch_model.pt`.
- Text encoder failures from `AutoModel.from_pretrained` usually mean `text_encoder/` was not created from the LLaVA language model or is incomplete.
- CLIP failures from `CLIPTextModel.from_pretrained` usually mean `text_encoder_2/` is missing or incomplete.

## CUDA stack or core-dump failures

The README suggests two paths for floating point exception/core-dump failures on specific GPU types:

1. Use CUDA 12.4 with compatible CUBLAS/CUDNN, including `nvidia-cublas-cu12==12.4.5.8` when needed.
2. Force a CUDA 11.8 PyTorch wheel, reinstall requirements, flash-attn, and xDiT.

Do not mix arbitrary PyTorch/CUDA/flash-attn binaries. Rebuild or reinstall flash-attn after changing PyTorch or CUDA wheels.

## Insufficient VRAM

Single-GPU generation at README resolutions is large. If a user has less than the documented memory floor, suggest one or more of:

- lower resolution such as `544x960` instead of `720x1280`;
- `--use-cpu-offload` for single-GPU mode;
- FP8 weights when the FP8 pair is present;
- xDiT multi-GPU mode, but only after installing `xfuser`/flash-attn and using a valid degree plan.
