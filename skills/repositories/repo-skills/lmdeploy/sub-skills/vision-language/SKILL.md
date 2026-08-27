---
name: vision-language
description: "Use LMDeploy vision-language and multimodal APIs for media
  loading, VLM prompt formats, OpenAI-style multimodal payloads, image token
  placement, and no-download media validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Vision Language

Use this sub-skill when the task involves LMDeploy VLM or multimodal inputs: images, videos, audio, time series, OpenAI `content` lists, tuple prompts such as `(prompt, image)`, or `VisionConfig`.

## Read First

- `references/input-formats.md` for tuple prompts, OpenAI-style content blocks, media URL/data URL formats, batch shapes, multi-turn image chat, `IMAGE_TOKEN`, and modality support.
- `references/workflows.md` for copy-ready offline VLM pipeline patterns, API payload construction, base64/local media handling, `VisionConfig`, `mm_processor_kwargs`, and payload preflight.
- `references/troubleshooting.md` for optional dependency failures, blocked URLs, fetch timeouts, image token placement, session length, batch media mismatches, chat-template issues, and chemistry/media gaps.
- `scripts/check_vl_media_inputs.py` for a no-download smoke check that creates a tiny local image, validates base64/data URLs, and rejects unsafe URL examples.

## Scope

Own these tasks:

- Build VLM prompts for `lmdeploy.pipeline`, including `(prompt, image)`, `(prompt, [image1, image2])`, batch prompt lists, and OpenAI-style message lists.
- Load or encode multimodal media with `lmdeploy.vl.load_image`, `load_video`, `load_audio`, `load_time_series`, and the `encode_*_base64` helpers.
- Construct OpenAI-compatible multimodal request bodies using `text`, `image_url`, `video_url`, `audio_url`, and `time_series_url` content blocks.
- Tune VLM-specific inputs with `VisionConfig(max_batch_size=...)`, `media_io_kwargs`, `mm_processor_kwargs`, and manual `IMAGE_TOKEN` placement where model docs require it.
- Preflight payloads for safe media URL schemes, local/base64 media syntax, multiple images, and server-side multimodal parser expectations without downloading model weights.

Route elsewhere:

- Text-only offline generation, `GenerationConfig` basics, streaming, logits, PPL, and `lmdeploy chat`: `pipeline-inference`.
- Launching API servers/proxies, auth, API clients, endpoint routing, and transport operations: `serving-apis`.
- Creating AWQ/GPTQ/SmoothQuant or other quantized VLM artifacts: `quantization`.
- Adding or debugging VLM model implementation internals, processor classes, backend kernels, or architecture registration: `backend-extension`.

## Fast Start

```python
from lmdeploy import TurbomindEngineConfig, VisionConfig, pipeline
from lmdeploy.vl import load_image

backend_config = TurbomindEngineConfig(session_len=8192)
vision_config = VisionConfig(max_batch_size=4)

with pipeline("org/vlm-or-local-folder", backend_config=backend_config, vision_config=vision_config) as pipe:
    image = load_image("/path/to/image.jpg")
    response = pipe(("Describe this image.", image))
    print(response.text if hasattr(response, "text") else response)
```

For custom local VLM folder names that LMDeploy cannot map to a built-in template, pass `chat_template_config=ChatTemplateConfig(model_name="template-name")` when creating the pipeline.

## Validation

Run the bundled check before recommending a VLM media workflow:

```bash
python sub-skills/vision-language/scripts/check_vl_media_inputs.py --print-examples
```

This check does not download models or fetch remote media. Model execution still requires the user’s selected VLM weights, backend dependencies, accelerator memory, and any model-specific optional packages.
