---
name: visual-dialogue-tools
description: "Route image upload, click-mask segmentation, OCR, Husky
  VQA/captioning, inpainting, replacement, and ControlNet image workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visual Dialogue Tools

Use this sub-skill when the task is about uploading an image, clicking a region, asking about text or scene content, removing or replacing a masked object, saving a mask for later use, or generating/editing an image from segmentation, canny, scribble, depth, pose, line, or normal control maps.

## Route elsewhere

- App launch/load strings, tab gating, certificates, and service-level model loading belong in `../app-deployment/SKILL.md`.
- ImageBind audio/thermal generation and DragGAN point editing belong in `../cross-modal-generation/SKILL.md`.
- Video upload, captioning, action recognition, dense captioning, and TikTok-style clip generation belong in `../video-understanding/SKILL.md`.

## Read first

- Read [references/controller-state.md](references/controller-state.md) for the ConversationBot state model, upload flow, click-mask handling, memory updates, and path recovery rules.
- Read [references/image-tool-reference.md](references/image-tool-reference.md) when you need the exact tool names, comma-separated input grammar, checkpoint expectations, or output filename conventions.
- Read [references/image-workflows.md](references/image-workflows.md) for end-to-end recipes such as Pick, OCR on a clicked region, remove/replace, save-mask reuse, and control-map generation.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a tool is unloaded, a mask is empty, parent-image recovery fails, a checkpoint is missing, OCR returns no text, or the prompt grammar is ambiguous.
- Run [scripts/validate_mask_inputs.py](scripts/validate_mask_inputs.py) before handing a candidate image/mask pair to removal, replacement, or OCR workflows; it checks file existence, format, dimensions, non-empty masks, and an optional parent relationship.

## Operating notes

- Treat `state` as the chat transcript and `user_state[0]` as the live session cache.
- Uploaded images seed both caption and OCR memory; clicked masks are saved under `image/` with a recoverable parent anchor.
- Use OCR when the user cares about exact characters; use HuskyVQA when the user cares about scene semantics inside a selected region.
- Removal uses the inpainting path; replacement uses the masked-object replacement path; both expect the image path first and the mask path second.
- Many models are e-mode aware and move to CPU between calls, so do not assume GPU residency across turns.
