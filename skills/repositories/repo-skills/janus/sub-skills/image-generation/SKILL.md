---
name: image-generation
description: "Guides Janus and Janus-Pro text-to-image generation,
  classifier-free guidance, and image decoding workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Image Generation

Use this sub-skill when the task is about Janus or Janus-Pro text-to-image generation, classifier-free guidance, output image saving, or adapting the repo's generation scripts.

## Read first

- [`references/workflows.md`](references/workflows.md) for end-to-end generation recipes.
- [`references/api-reference.md`](references/api-reference.md) for verified generation-loop parameters and helper calls.
- [`references/troubleshooting.md`](references/troubleshooting.md) for CUDA, template, padding, and decode failures.
- [`scripts/janus_text_to_image.py`](scripts/janus_text_to_image.py) for a safe dry-run helper and an optional real model run.

For installation and model-family selection, use the root [`../../references/installation-and-models.md`](../../references/installation-and-models.md).

## When to use this route

Choose this route when the user asks to:

- Generate images from text with Janus or Janus-Pro.
- Adapt the classifier-free guidance loop or image decode logic.
- Change seeds, batch size, output directory, image size, or patch size.
- Debug `pad_id`, `past_key_values`, or token/image shapes in generation.
- Save one or more generated samples from a prompt.

## Core workflow

1. Choose Janus or Janus-Pro and the matching model id.
2. Apply the SFT template to a user/assistant conversation.
3. Append `vl_chat_processor.image_start_tag` to the prompt.
4. Encode the prompt to token ids.
5. Duplicate the batch for CFG and mask the unconditional branch.
6. Run the token loop, alternating language-model forward passes and `prepare_gen_img_embeds`.
7. Decode tokens with `gen_vision_model.decode_code`.
8. Convert the decoded tensor into image files.

## Dry-run before model execution

Validate the prompt and generation parameters without downloading weights:

```bash
python sub-skills/image-generation/scripts/janus_text_to_image.py \
  --family janus-pro \
  --model-id deepseek-ai/Janus-Pro-1B \
  --prompt "A glass of red wine on a reflective surface." \
  --output-dir ./generated_samples
```

The default mode prints a plan and does not download model weights. Add `--run-model` only when you are ready for the real generation run.

## Route elsewhere

- Use [`../multimodal-understanding/SKILL.md`](../multimodal-understanding/SKILL.md) for image+question tasks.
- Use [`../janusflow-workflows/SKILL.md`](../janusflow-workflows/SKILL.md) for JanusFlow rectified-flow image generation.
- Use [`../demos-and-serving/SKILL.md`](../demos-and-serving/SKILL.md) for Gradio/FastAPI serving.
