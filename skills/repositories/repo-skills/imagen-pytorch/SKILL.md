---
name: "imagen-pytorch"
description: "Routes Imagen-Pytorch workflows for image and video diffusion,
  config-driven training, and CLI usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# imagen-pytorch

Use this repo skill when a task names `imagen-pytorch`, `Imagen`, `ElucidatedImagen`, `ImagenTrainer`, `Unet`, `Unet3D`, `imagen config`, `imagen train`, `imagen sample`, checkpoint loading, T5 conditioning, image inpainting, or video diffusion.

## Start here

- Install the published package with `pip install imagen-pytorch`.
- For practical generation, training, or video workflows, use a CUDA-capable PyTorch runtime. Tiny CPU checks are still useful for import and config validation.
- Minimal import smoke:

  ```bash
  python -c "from imagen_pytorch import Imagen, Unet, ImagenTrainer, ElucidatedImagen, Unet3D; print('imagen_pytorch ok')"
  ```

- If import or optional dependencies fail, run [scripts/check_imagen_pytorch_env.py](scripts/check_imagen_pytorch_env.py) before deeper debugging.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches the current checkout or before refreshing it.

## Route map

| If the task is mainly about... | Start with |
| --- | --- |
| Building `Unet`, `Imagen`, `ElucidatedImagen`, or direct sampling/training tensors | [image-generation](sub-skills/image-generation/SKILL.md) |
| `ImagenTrainer`, EMA, dataloaders, distributed training, save/load, or resume | [training-and-checkpointing](sub-skills/training-and-checkpointing/SKILL.md) |
| `imagen config`, `imagen train`, `imagen sample`, config JSON, or validator logic | [configuration-and-cli](sub-skills/configuration-and-cli/SKILL.md) |
| Local image folders, Hugging Face rows, URL/image/text collation, T5 text conditioning, or precomputed embeddings | [data-and-text-conditioning](sub-skills/data-and-text-conditioning/SKILL.md) |
| `Unet3D`, text-to-video, temporal downsampling, or image/video inpainting | [video-and-inpainting](sub-skills/video-and-inpainting/SKILL.md) |

## Public entry points worth knowing

- `imagen_pytorch.imagen_pytorch`: core image diffusion models.
- `imagen_pytorch.elucidated_imagen`: Elucidated/Karras-style diffusion variant.
- `imagen_pytorch.trainer`: `ImagenTrainer` and checkpoint orchestration.
- `imagen_pytorch.configs`: Pydantic config objects.
- `imagen_pytorch.data`: folder and Hugging Face data helpers.
- `imagen_pytorch.t5`: text tokenization / encoding helpers.
- `imagen_pytorch.utils`: checkpoint loading helpers.
- `imagen_pytorch.imagen_video`: `Unet3D` and video-specific layers.
- Console script: `imagen` with `config`, `train`, and `sample` commands.

Use [references/api-overview.md](references/api-overview.md) when you need a quick map from a symbol to its owning module and the correct sub-skill.

## When to read the repo-level references

- [references/troubleshooting.md](references/troubleshooting.md) for install/import issues, missing optional dependencies, and package-wide runtime pitfalls.
- [references/api-overview.md](references/api-overview.md) for the verified package surface and routing hints.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is for managed router import; do not edit router Markdown by hand.

## Practical guidance

- Choose the most specific sub-skill that matches the user's primary task, then follow the route map above for secondary concerns.
- If the task spans multiple areas, start where the user-facing action happens first. For example, a command-line configuration task starts in `configuration-and-cli`, then follows into `training-and-checkpointing` or `image-generation` as needed.
- Do not assume text prompts are free: raw strings can trigger T5 downloads or Hugging Face cache access. Use `data-and-text-conditioning` if the task needs safe precomputed text embeddings.
- Do not assume CPU smoke proves practical quality. CPU checks can validate import and control flow, but realistic image/video generation is a CUDA-scale task.
