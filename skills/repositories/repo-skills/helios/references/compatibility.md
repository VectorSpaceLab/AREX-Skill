# Compatibility and environment notes

## Baseline packages

The Helios workflows expect a modern CUDA-capable Python environment with:

- `torch` with CUDA support
- `diffusers` with Helios video classes available
- `transformers`
- `accelerate`
- `peft`
- `omegaconf`
- `kernels`
- `ftfy`, `einops`, `regex`, `imageio-ffmpeg`
- Source-side extras used by batch or evaluation paths: `pandas`, `opencv-python`, `moviepy`

Demo-only UI flows also need `gradio` and `spaces`.

## Backend expectations

| Surface | Backend | Notes |
| --- | --- | --- |
| Core inference | CUDA | The practical generation path is GPU-first. |
| Core training | CUDA | DDP is the baseline; DeepSpeed is optional/alternative. |
| Data-prep validation | Any | File-layout checks can run without GPU. |
| Demo UI | CUDA | The local demo preloads and compiles model code on startup. |

## Verified runtime facts

The installed diffusers build exposes these Helios-facing APIs:

- `AutoencoderKLWan`
- `HeliosPyramidPipeline`
- `HeliosDMDScheduler`
- `ContextParallelConfig`

The local source also exposes a richer training/inference pipeline with chunked
history controls, low-VRAM offload, and prompt/video input branching.

## Common compatibility traps

- A `kernels` build variant must match the selected torch/CUDA combination.
  When it does not, Helios kernel imports can fail before any model code runs.
- `app.py` is not a lazy import. It downloads and compiles at import time, so
  it is not the safest first smoke test.
- `enable_low_vram_mode` and `enable_compile` are incompatible in the local
  inference pipeline.
- `bfloat16` training on MPS is not supported.
