---
name: multimodal-understanding
description: "Guides Janus-family image question answering, prompt formatting,
  image loading, and multimodal input preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Multimodal Understanding

Use this sub-skill when the task is about image+question prompting, OCR/formula conversion, visual question answering, image placeholder debugging, or adapting the Janus understanding examples.

## Read first

- [`references/workflows.md`](references/workflows.md) for end-to-end understanding recipes.
- [`references/api-reference.md`](references/api-reference.md) for verified processor/model signatures and output fields.
- [`references/troubleshooting.md`](references/troubleshooting.md) for image, template, dtype, and backend failures.
- [`scripts/janus_understanding.py`](scripts/janus_understanding.py) for a safe dry-run helper and an optional real model run.

For installation and model-family selection, use the root [`../../references/installation-and-models.md`](../../references/installation-and-models.md).

## When to use this route

Choose this route when the user asks to:

- Answer a question about an image with Janus, Janus-Pro, or JanusFlow.
- Convert a formula or document image into text or LaTeX.
- Build a conversation containing `<image_placeholder>`.
- Debug processor outputs, image token masks, or `prepare_inputs_embeds`.
- Validate image paths/base64 inputs before a full model download.

## Core workflow

1. Choose the model family and model id.
2. Build a conversation with one user turn containing `<image_placeholder>` and one empty assistant turn.
3. Load images as RGB PIL images.
4. Call `VLChatProcessor(..., force_batchify=True)`.
5. Move the batched processor output to the model device and dtype.
6. Call `vl_gpt.prepare_inputs_embeds(**prepare_inputs)`.
7. Generate from `vl_gpt.language_model.generate(...)` with the attention mask and tokenizer special ids.
8. Decode the first output and inspect the formatted prompt if the answer looks wrong.

## Dry-run before model execution

When the task is only to validate prompt/image layout, use:

```bash
python sub-skills/multimodal-understanding/scripts/janus_understanding.py \
  --family janus-pro \
  --model-id deepseek-ai/Janus-Pro-1B \
  --image ./sample.png \
  --question "Convert the formula into LaTeX."
```

The default mode prints a plan and does not download model weights. Add `--run-model` only when the environment, model access, and GPU/CPU trade-off are acceptable.

## Route elsewhere

- Use [`../image-generation/SKILL.md`](../image-generation/SKILL.md) for Janus or Janus-Pro text-to-image generation.
- Use [`../janusflow-workflows/SKILL.md`](../janusflow-workflows/SKILL.md) for JanusFlow rectified-flow image generation.
- Use [`../demos-and-serving/SKILL.md`](../demos-and-serving/SKILL.md) for Gradio or FastAPI serving.
