# Checkpoints and Environment

Read this before running any SUPIR workflow that can load a model. This file is
public runtime guidance; it intentionally omits local machine paths and private
cache locations.

## Runtime posture

- SUPIR's public scripts are CUDA-only. They abort when `torch.cuda.device_count()` is zero.
- A two-GPU host assigns SUPIR restoration to `cuda:0` and LLaVA captioning to `cuda:1`; a one-GPU host puts both on `cuda:0`.
- End-to-end restoration is checkpoint-heavy. Preflight configs and paths before loading SDXL, SUPIR, CLIP, or LLaVA weights.
- The core API/batch stack and the optional Gradio UI stack have different dependency needs. Do not install Gradio just to inspect core APIs.

## Core package stack

For core API, batch restoration, tiled VAE, and face helper import inspection, use a CUDA PyTorch environment with these package families:

- PyTorch + torchvision CUDA build (`torch>=2.1`, `torchvision>=0.16`).
- Config and diffusion stack: `omegaconf`, `safetensors`, `k-diffusion`, `diffusers`, `pytorch-lightning`, `kornia`, `einops`, `open-clip-torch`, `openai-clip`, `timm`, `transformers`, `tokenizers`, `sentencepiece`, `accelerate`.
- Image/data helpers: `opencv-python`, `Pillow`, `numpy`, `scipy`, `scikit-image`, `tqdm`, `requests`.
- Face workflow: `facexlib` plus its detection/parsing model assets when face restoration is used.
- Optional UI workflow: `gradio`, `gradio_imageslider`, and their web-service dependencies. The UI stack is not required for batch/API use.

A working inspection combination used Python 3.11, CUDA PyTorch, Transformers 4.28.1, tokenizers 0.13.3, open-clip-torch 2.17.1, k-diffusion 0.1.1.post1, and facexlib 0.3.0. Newer Transformers releases may already reserve the `llava` model type and can break this repo's local LLaVA config registration.

## Checkpoint variables

The source repository uses a Python checkpoint settings module and YAML fields.
Do not copy private defaults; replace every value with a user-controlled path or
set CLIP paths to `None` only when automatic Hugging Face download is acceptable.

| Variable or YAML field | Used by | Meaning |
| --- | --- | --- |
| `LLAVA_CLIP_PATH` | LLaVA captioning | CLIP vision tower for LLaVA v1.5 13B. README says users with Hugging Face access may set this to `None` for automatic download. |
| `LLAVA_MODEL_PATH` | LLaVA captioning | LLaVA v1.5 13B model path. Required unless captioning is disabled or a compatible local model path is supplied. |
| `SDXL_CLIP1_PATH` | SDXL conditioner | OpenAI CLIP ViT-L/14 text encoder path; may be `None` for HF download when allowed. |
| `SDXL_CLIP2_CKPT_PTH` | SDXL conditioner | OpenCLIP ViT-bigG checkpoint file; may be `None` for HF/download-compatible setup. |
| `SDXL_CKPT` | YAML config | SDXL base or Juggernaut/Lightning checkpoint used to initialize the diffusion model. |
| `SUPIR_CKPT_Q` | YAML config | SUPIR v0Q high-quality/general restoration checkpoint. |
| `SUPIR_CKPT_F` | YAML config | SUPIR v0F fidelity/light-degradation restoration checkpoint. |
| `SUPIR_CKPT` | YAML config | Optional additional SUPIR checkpoint loaded before Q/F selection; usually unset in the public configs. |

## Config variants

| Config | Sampler/model role | Typical route |
| --- | --- | --- |
| `SUPIR_v0.yaml` | Default SUPIR v0 with `RestoreEDMSampler` and SDXL base checkpoint | Batch restoration, standard demo, API use |
| `SUPIR_v0_tiled.yaml` | Uses `TiledRestoreEDMSampler` for large images/local prompt tiled restoration | Interactive tiled/large-image workflows |
| `SUPIR_v0_Juggernautv9_lightning.yaml` | Uses a Juggernaut Lightning checkpoint and `RestoreDPMPP2MSampler` | Faster photorealistic demo variant when matching checkpoint is available |

## Preflight order

1. Confirm CUDA and a compatible PyTorch wheel.
2. Confirm core imports with `sub-skills/python-api-and-config/scripts/supir_api_probe.py --check-cuda`.
3. Validate checkpoint/config paths with `scripts/check_supir_assets.py --config <yaml> --validate-existing`.
4. Use `--no_llava` or manual/local prompts when LLaVA checkpoints are absent.
5. Only then run the batch wrapper or demo preflight.

## Backend verification limits

A CUDA allocation and source-module import prove the environment is ready for
skill-guided setup and API inspection. They do not prove full restoration quality.
Full native verification requires real model checkpoints, one or more input
images, enough VRAM, and user approval to run an expensive inference path.
