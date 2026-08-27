---
name: data-and-text-conditioning
description: "Prepare Imagen-Pytorch image folders, Hugging Face dataset items,
  collators, and T5 or precomputed text conditioning inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data and Text Conditioning

Use this sub-skill for the preprocessing path that turns local image collections or Hugging Face rows into Imagen-ready batches and text-conditioning inputs.

## Owns
- Local image-folder validation for unconditional training.
- `Dataset(folder, image_size, exts, convert_image_to_type)` and `get_images_dataloader(...)`.
- `Collator(image_size, url_label, text_label, image_label, name, channels)` and its URL/image/text row handling.
- Raw texts, `text_embeds`, `text_masks`, and image-channel conversion for Imagen / ImagenTrainer.
- Shape and mode checks for precomputed text conditioning.

## Route elsewhere
- Training loop, optimizers, EMA, checkpoints, and `train_step`: [`../training-and-checkpointing/SKILL.md`](../training-and-checkpointing/SKILL.md)
- Config files and CLI flags: [`../configuration-and-cli/SKILL.md`](../configuration-and-cli/SKILL.md)
- Image generation and sampling APIs: [`../image-generation/SKILL.md`](../image-generation/SKILL.md)
- Video and inpainting sampling APIs: [`../video-and-inpainting/SKILL.md`](../video-and-inpainting/SKILL.md)

## Short workflow
1. Identify the input path: local folder, HF row schema, or precomputed text tensors.
2. Check the folder or tensor metadata with the bundled scripts:
   - [`scripts/check_image_folder.py`](scripts/check_image_folder.py)
   - [`scripts/text_embedding_shape_check.py`](scripts/text_embedding_shape_check.py)
3. For local folders, use `Dataset(...)` or `get_images_dataloader(...)` to produce image-only batches.
4. For HF rows, use `Collator(...)` to produce image tensors and encoded text tensors.
5. For text conditioning, choose raw texts or precomputed `text_embeds` / `text_masks` and verify the shapes before training.
6. Hand the validated batches to the training or sampling sub-skill.

## Key contracts
- The local-folder path is image-only.
- The collator path can download URLs, skip failing rows, and return `None` if every row in a batch fails.
- Trainer dataloaders are consumed by keyword order, so tuple layout must match the configured output names.
- T5 text handling truncates at 256 tokens and uses the configured T5 model name.
- Channel conversion must match the requested `channels` value and the input image modes.

## References
- [`references/data-formats.md`](references/data-formats.md)
- [`references/text-conditioning.md`](references/text-conditioning.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
