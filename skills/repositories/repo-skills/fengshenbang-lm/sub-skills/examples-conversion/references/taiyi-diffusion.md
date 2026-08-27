# Taiyi Stable Diffusion recipes

This reference supports safe planning for Taiyi Stable Diffusion inference, fine-tuning, DreamBooth, and format conversion. It does not launch `diffusers`, download weights, generate images, or train models.

## Models and intended use

| Model ID | Use | Notes |
|---|---|---|
| `IDEA-CCNL/Taiyi-Stable-Diffusion-1B-Chinese-v0.1` | Chinese text-to-image generation and Chinese fine-tuning | Initial Chinese Stable Diffusion release; examples use Chinese prompts. |
| `IDEA-CCNL/Taiyi-Stable-Diffusion-1B-Chinese-EN-v0.1` | Chinese/English bilingual text-to-image generation | Bilingual variant; examples use mixed Chinese/English style prompts. |
| `IDEA-CCNL/Taiyi-CLIP-RoBERTa-102M-ViT-L-Chinese` | CLIP scoring/text encoder context | Used as source evidence for Taiyi alignment; model internals route to `../model-zoo/SKILL.md`. |

Treat all model IDs as possible network downloads unless the user confirms a local cache or provides a local model directory.

## Inference path choice

| Path | When to choose | Dependencies | Device/memory notes | Caveats |
|---|---|---|---|---|
| CPU/full precision planning | User has no CUDA, wants safest static code or a very slow local smoke after confirming cached weights | `torch`, `diffusers`, compatible tokenizer/text encoder deps | Large RAM; image generation may be very slow | Source examples focus on CUDA, but diffusers can run full precision on CPU if the model and dependencies fit. Do not promise speed. |
| CUDA/full precision | User has CUDA and enough VRAM, wants simpler precision behavior | `torch` with CUDA, `diffusers` | Around 1B-param diffusion pipeline; practical VRAM depends on resolution and scheduler | Slower and more memory-heavy than FP16. |
| CUDA/FP16 | User has CUDA, compatible `torch`, and wants lower VRAM/faster inference | `torch`, `diffusers`, often `accelerate`; model weights must support FP16 load | Use `torch_dtype=torch.float16` and move pipeline to CUDA | Not a CPU path; avoid on CPU/MPS unless the stack explicitly supports it. |

### Safe decision helper

```bash
python ../scripts/check_recipe_requirements.py --recipe taiyi-inference --device cpu --precision fp32
python ../scripts/check_recipe_requirements.py --recipe taiyi-inference --device cuda --precision fp16 --gpus 1 --vram-gb 16
```

### Sanitized inference skeletons

Do not run these until model cache/download permission is settled.

CPU/full precision shape:

```python
from diffusers import StableDiffusionPipeline

model_path = "<local Taiyi model directory or permitted model ID>"
pipe = StableDiffusionPipeline.from_pretrained(model_path)
pipe = pipe.to("cpu")
image = pipe("飞流直下三千尺，油画", guidance_scale=7.5).images[0]
image.save("taiyi_example.png")
```

CUDA/FP16 shape:

```python
import torch
from diffusers import StableDiffusionPipeline

model_path = "<local Taiyi model directory or permitted model ID>"
pipe = StableDiffusionPipeline.from_pretrained(model_path, torch_dtype=torch.float16)
pipe = pipe.to("cuda")
image = pipe("小桥流水人家，Van Gogh style", guidance_scale=10.0).images[0]
image.save("taiyi_example.png")
```

## Fine-tuning requirements

The Taiyi fine-tune example trains a 1B-parameter diffusion pipeline on paired image/text data.

### Data shape

- A dataset directory contains image files and text captions.
- The example describes each sample as an image plus a `.txt` caption sidecar.
- Confirm resolution, caption encoding, image formats, and train/validation split before training.

### Resource table from example guidance

| Mode | Batch size assumption | VRAM | RAM | Notes |
|---|---:|---:|---:|---|
| FP32 fine-tune | 1 | 26GB+ | 64GB+ | Heavy; full precision. |
| FP16 fine-tune | 1 | 21GB+ | 64GB+ | Requires compatible CUDA/FP16 stack. |
| FP16 + Deepspeed offload | 1 | 6GB+ | 80GB+ | Saves VRAM by using host RAM; Deepspeed/toolchain must work. |

### Important knobs

- `model_path`: Taiyi model directory or permitted model ID.
- `datasets_path`: directory containing image/text samples.
- `datasets_type`: example uses text caption sidecars.
- `resolution`: example uses 512.
- `precision`: examples include BF16 or FP16 depending script.
- `save_ckpt_path` / `load_ckpt_path`: mutating checkpoint paths; require fresh directories or backup.
- `freeze_unet`, `freeze_text_encoder`, `text_model_path`, `use_local_token`, `use_local_unet`: model-component choices; route architecture details to `../model-zoo/SKILL.md`.

Do not copy source shell scripts as-is; they include local scheduler/resource assumptions. Build a new command from user-approved paths.

## DreamBooth requirements

DreamBooth examples adapt Taiyi Stable Diffusion to a specific subject.

### Data shape

| Item | Meaning |
|---|---|
| `instance_data_dir` | Directory of subject images. |
| `instance_prompt` | Prompt token/phrase identifying the subject. |
| `class_data_dir` | Optional class images for prior preservation. |
| `class_prompt` | Class prompt for prior preservation. |
| `with_prior_preservation` | Enables prior loss; may require generating or collecting class images. |
| `num_class_images` | Number of class images expected for prior preservation. |

### Resource notes

- Base DreamBooth example guidance: FP32 on the 1B Taiyi model needs about 26GB+ VRAM and 64GB+ RAM at batch size 1-2.
- Prior-preservation training can require more memory and may need Deepspeed on a 40GB-class A100 in the documented setup.
- Recommended steps in the example include higher quality images, simple backgrounds, smaller learning rates for complex subjects, and more steps for difficult faces/objects.

## Diffusers-to-original checkpoint conversion

If the user asks to export a Diffusers pipeline to an original Stable Diffusion `.ckpt` style file, use [conversion-utilities.md](conversion-utilities.md). This is mutating and may write a large checkpoint. Required preflight:

1. Confirm `model_path` points to a local Diffusers pipeline directory with `unet`, `vae`, and `text_encoder` weights.
2. Confirm `checkpoint_path` is a new output file, not an input file.
3. Confirm whether half precision output is desired.
4. Verify storage space and dependencies.

## Troubleshooting matrix

| Symptom | Likely cause | Safe fix |
|---|---|---|
| `ModuleNotFoundError: diffusers` | Diffusers not installed in the active env | Use requirement checker; install only in an approved environment. |
| `accelerate` warning or FP16 device map issue | FP16/CUDA path often expects accelerate-compatible stack | Add `accelerate` to dependency plan; verify before generation. |
| CPU path is extremely slow | Stable Diffusion on CPU is compute-heavy | Offer static planning or one tiny low-resolution smoke only if the user accepts slow runtime. |
| CUDA OOM | Resolution, precision, batch size, or model component training too large | Reduce resolution/batch, use FP16/BF16 if supported, freeze components, or use Deepspeed offload. |
| Training resumes from wrong checkpoint | `load_ckpt_path` points to stale or incompatible state | Require explicit resume path and match it to model/data/precision choices. |
| Fine-tune saves unexpected pipeline directories | Lightning callback saves model components on checkpoints | Require a dedicated output root and storage estimate. |
| Model ID tries to download | No local cache and network not disabled | Ask permission for downloads or require local model path. |
| DreamBooth prior images missing | `with_prior_preservation` enabled without class images or generation plan | Ask for class images, number of class images, and whether class-image generation is allowed. |

## Handoff template

When planning Taiyi execution, return:

- selected path: CPU/full precision, CUDA/full precision, CUDA/FP16, fine-tune, DreamBooth, or conversion;
- model source and cache/download status;
- dependency list and backend requirement;
- data/checkpoint/output paths using user placeholders;
- expected VRAM/RAM and precision;
- all side effects that would occur if executed;
- unresolved blockers or approvals needed.
