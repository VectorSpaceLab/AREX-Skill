# Model Artifacts and Local Caches

## Purpose

Read this when DreamCraft3D fails while loading pretrained model weights, local caches, or required geometry assets.

## Required and common artifacts

| Artifact family | Expected location or identifier | Used by | Notes |
| --- | --- | --- | --- |
| Stable Zero123 checkpoint | `load/zero123/stable_zero123.ckpt` in stage configs; code defaults also mention `load/zero123/stable-zero123.ckpt` | coarse/geometry 3D guidance | Confirm exact filename in the active config. The README points users to the Stability AI Stable Zero123 weights. |
| Stable Zero123 config | `load/zero123/sd-objaverse-finetune-c_concat-256.yaml` | Stable Zero123 guidance | Present in the repo and paired with checkpoint architecture. |
| DeepFloyd IF | `DeepFloyd/IF-I-XL-v1.0` | coarse/geometry prompt processor and guidance; optional DreamBooth LoRA base | Requires model access/cache and substantial memory. |
| Stable Diffusion 2.1 base | `stabilityai/stable-diffusion-2-1-base` | texture stage `stable-diffusion-bsd-guidance` | Texture config uses both base and LoRA model-name fields. |
| Omnidata depth/normal | `load/omnidata/omnidata_dpt_depth_v2.ckpt`, `load/omnidata/omnidata_dpt_normal_v2.ckpt` | `preprocess_image.py` | Needed only when running full preprocessing. |
| DMTet grids | `load/tets/32_tets.npz`, `64_tets.npz`, `128_tets.npz` | geometry/texture `tetrahedra-sdf-grid` | The canonical geometry/texture configs use resolution 128. |
| Zero123++ | `sudo-ai/zero123plus-v1.1` in a local HF cache | optional multiview generation | Source helper uses `local_files_only=True` and cache directory `load/checkpoints/huggingface/hub`. |
| Stable Diffusion x4 upscaler | `stabilityai/stable-diffusion-x4-upscaler` | optional multiview super-resolution | Only used when `--superres` is requested. |

## Cache and network policy

- Do not assume the runtime can download from Hugging Face or external URLs.
- If a script or config uses `local_files_only=True`, local cache absence is a hard planning failure until the user supplies or approves model acquisition.
- Download scripts are network-mutating helpers; use them only after the user approves network access and destination paths.
- Keep model caches outside the generated skill tree. The skill contains instructions and validators, not model weights.

## CUDA and precision notes

- The README requires an NVIDIA GPU and recommends at least 20GB VRAM; defaults were run on 40GB A100-class GPUs.
- The Dockerfile installs CUDA 11.8-era torch and GPU extensions before `requirements.txt`.
- `stable-diffusion-bsd-guidance` defaults to half precision weights but trains/fine-tunes UNet components, so memory usage can spike.
- xformers is optional in some configs but required by parts of the BSD guidance code path that call memory-efficient attention setup.

## Stable Diffusion BSD guidance facts

The texture config uses:

- `guidance_type: stable-diffusion-bsd-guidance`
- base model `stabilityai/stable-diffusion-2-1-base`
- LoRA model path/name field `pretrained_model_name_or_path_lora`
- `guidance_scale: 2.0`
- `only_pretrain_step: 1000`
- trainable UNet and LoRA UNet branches in the guidance implementation.

These facts matter when a user tries to reuse LoRA artifacts from a different base model: base-model mismatch can produce missing-key errors or poor guidance.

## Stable Zero123 guidance facts

The Stable Zero123 guidance loads an LDM checkpoint and config, prepares image embeddings from `cond_image_path`, and conditions on elevation, azimuth, and camera distance. If the checkpoint/config pair is wrong, failures often happen before any useful 3D optimization begins.
