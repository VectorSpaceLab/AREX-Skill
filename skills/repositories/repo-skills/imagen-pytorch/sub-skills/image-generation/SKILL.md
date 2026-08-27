---
name: image-generation
description: "Construct and use imagen-pytorch image diffusion models for
  text-conditioned, unconditional, super-resolution, ElucidatedImagen, sampling,
  and tiny smoke workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# image-generation

Use this sub-skill when a task asks for image-only `imagen-pytorch` model construction or direct image diffusion calls with `Unet`, `NullUnet`, `BaseUnet64`, `SRUnet256`, `SRUnet1024`, `Imagen`, or `ElucidatedImagen`.

## Use when

- Building text-to-image, unconditional, cascade, or super-resolution-only Imagen models.
- Choosing `condition_on_text`, `cond_drop_prob`, `cond_scale`, `timesteps`, `noise_schedules`, `pred_objectives`, `lowres_sample_noise_level`, or Karras / `ElucidatedImagen` sampling hyperparameters.
- Calling `Imagen.forward`, `ElucidatedImagen.forward`, `.sample(...)`, `return_pil_images`, `return_all_unet_outputs`, `start_at_unet_number`, `stop_at_unet_number`, `start_image_or_video`, or image inpainting arguments.
- Running a safe no-network API smoke with synthetic tensors.

## Route elsewhere

- Trainer state, optimizers, dataloaders, EMA, checkpoint save/load, and resume flows: [training-and-checkpointing](../training-and-checkpointing/SKILL.md).
- Config classes, JSON config files, and `imagen` CLI commands: [configuration-and-cli](../configuration-and-cli/SKILL.md).
- Folder datasets, Hugging Face datasets, T5 helpers, text tokenization, and precomputing text embeddings: [data-and-text-conditioning](../data-and-text-conditioning/SKILL.md).
- `Unet3D`, video tensor dimensions, temporal conditioning, and video inpainting: [video-and-inpainting](../video-and-inpainting/SKILL.md).

## Quick workflow

1. Pick the conditioning mode first:
   - Unconditional: set `Imagen(..., condition_on_text=False)` / `ElucidatedImagen(..., condition_on_text=False)` and do not pass `texts` or `text_embeds`.
   - Text-conditioned without network surprises: pass precomputed `text_embeds` (and optional `text_masks`) whose final dimension matches `text_embed_dim`.
   - Text strings: expect the package's T5 path to be used; route text preparation details to [data-and-text-conditioning](../data-and-text-conditioning/SKILL.md).
2. Match cascade length: `len(unets)` must equal `len(image_sizes)`. The first unet is base generation; every later unet is automatically cast as low-resolution-conditioned.
3. For cascade training, always provide `unet_number`; train `NullUnet` stages never.
4. For upscaler-only sampling, pass both `start_at_unet_number > 1` and a low-resolution `start_image_or_video`.
5. Treat CPU as API smoke only. Realistic generation or training is practical CUDA-scale; quality was not proven by the construction smoke.

## References and helper

- [API reference](references/api-reference.md) lists public image API signatures, tensor contracts, defaults, and important assertions.
- [Workflows](references/workflows.md) gives task recipes for unconditional smoke, precomputed text embeddings, super-resolution-only branches, `ElucidatedImagen`, and output modes.
- [Troubleshooting](references/troubleshooting.md) maps common assertion messages and runtime symptoms to fixes.
- [tiny_image_smoke.py](scripts/tiny_image_smoke.py) runs a short no-network unconditional API check with optional sampling.
