# Vision-Language Workflows

Use these workflows to assemble LMDeploy VLM inputs without depending on repository source files or downloading models during preflight.

## 1. Offline Single-Image Pipeline

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, VisionConfig, pipeline
from lmdeploy.vl import load_image

backend_config = TurbomindEngineConfig(session_len=8192, tp=1)
vision_config = VisionConfig(max_batch_size=4)
gen_config = GenerationConfig(max_new_tokens=256, do_sample=False)

with pipeline("org/vlm-or-local-folder", backend_config=backend_config, vision_config=vision_config) as pipe:
    image = load_image("/path/to/image.jpg")
    response = pipe(("Describe this image in detail.", image), gen_config=gen_config)
    print(response.text if hasattr(response, "text") else response)
```

Outputs are LMDeploy response objects for most pipeline calls. Use `response.text` when present; batched calls return a list-like collection of response objects.

## 2. Multi-Image Prompt With Context Budget

```python
from lmdeploy import TurbomindEngineConfig, pipeline
from lmdeploy.vl import load_image

pipe = pipeline("org/vlm-or-local-folder", backend_config=TurbomindEngineConfig(session_len=8192))
images = [load_image("/path/to/a.jpg"), load_image("/path/to/b.jpg")]
response = pipe(("Compare these two images and mention key differences.", images))
```

Increase `session_len` when using multiple images, video frames, long system prompts, or long follow-up questions. If the backend reports context-length or token-budget failures, reduce image resolution/frame count or raise `session_len` if memory allows.

## 3. Batch Independent VLM Prompts

```python
from lmdeploy import pipeline
from lmdeploy.vl import load_image

pipe = pipeline("org/vlm-or-local-folder")
prompts = [
    ("Describe image A.", load_image("/path/to/a.jpg")),
    ("Describe image B.", load_image("/path/to/b.jpg")),
]
responses = pipe(prompts)
for response in responses:
    print(response.text if hasattr(response, "text") else response)
```

All batch entries should have compatible prompt/media structure. A common failure is mixing one entry with a single image and another with nested image lists of unexpected depth.

## 4. OpenAI-Style Multimodal Payload

Use this shape for both offline `pipe(messages)` and OpenAI-compatible server requests. Transport setup belongs to `serving-apis`; this workflow covers the payload only.

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe this image."},
        {"type": "image_url", "image_url": {"url": "/path/to/image.jpg"}},
    ],
}]

response = pipe(messages)
```

For an OpenAI client call, pass `messages=messages` to `client.chat.completions.create(...)`. Use `max_completion_tokens`, `temperature`, and `top_p` in the OpenAI request body, and put LMDeploy-specific multimodal controls in `extra_body`.

## 5. Base64 Image Payload With No Remote Fetch

```python
from lmdeploy.vl import encode_image_base64

b64 = encode_image_base64("/path/to/image.jpg", format="PNG")
messages = [{
    "role": "user",
    "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        {"type": "text", "text": "What is shown?"},
    ],
}]
```

Prefer data URLs or local file URLs for controlled deployments where remote media fetches are not allowed.

## 6. Video, Audio, and Time-Series Content

OpenAI-style content supports non-image modalities when the selected model supports them:

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "video_url", "video_url": {"url": "/path/to/video.mp4"}},
        {"type": "text", "text": "Summarize the video."},
    ],
}]

response = pipe(
    messages,
    media_io_kwargs={"video": {"num_frames": 16, "fps": 2}},
    mm_processor_kwargs={"video": {"min_pixels": 4 * 32 * 32, "max_pixels": 256 * 32 * 32}},
)
```

Model-specific support matters:

- Native image input is broadly available across LMDeploy VLM integrations.
- Native video and mixed image/video input are limited to specific model families such as Qwen3-VL, Qwen3.5, Qwen3-Omni, InternS1-Pro, and Intern-S2-Preview.
- Audio input is model-specific, for example Qwen3-Omni, and requires optional audio packages.
- Time-series input is model-specific, for example InternS1-Pro, and may require fields such as `sampling_rate`.

## 7. Multi-Turn Image Chat

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline
from lmdeploy.vl import load_image

pipe = pipeline("org/vlm-or-local-folder", backend_config=TurbomindEngineConfig(session_len=8192))
gen_config = GenerationConfig(max_new_tokens=256, top_p=0.8, temperature=0.8)

session = pipe.chat(("Describe this image.", load_image("/path/to/image.jpg")), gen_config=gen_config)
print(session.response.text)
session = pipe.chat("What detail supports that answer?", session=session, gen_config=gen_config)
print(session.response.text)
```

If later turns fail or ignore the image, confirm the first turn included the media and the chat template supports VLM conversation state.

## 8. Custom VLM Folder or Template

```python
from lmdeploy import ChatTemplateConfig, pipeline

pipe = pipeline(
    "local_model_folder",
    chat_template_config=ChatTemplateConfig(model_name="llava-v1"),
)
```

Use this when a renamed local folder prevents LMDeploy from recognizing a built-in VLM template. If the model family requires `trust_remote_code`, make that a conscious user decision and keep it out of reusable snippets unless required.

## 9. Manual Image Tokens

```python
from lmdeploy.vl.constants import IMAGE_TOKEN

prompt = f"Image-1: {IMAGE_TOKEN}\nImage-2: {IMAGE_TOKEN}\nCompare the images."
response = pipe((prompt, [image1, image2]))
```

Only place `IMAGE_TOKEN` manually when the selected VLM requires it or when its docs show explicit tokens for multi-image grounding. Mismatched token counts can cause preprocessing errors or poor grounding.

## 10. Payload Preflight Without Model Execution

Use the bundled validator before running expensive inference:

```bash
python sub-skills/vision-language/scripts/check_vl_media_inputs.py --print-examples
```

The script checks:

- Installed `lmdeploy.vl` helper imports.
- `VisionConfig` default construction.
- Tiny local `PIL` image encode/decode through `data:image/png;base64,...`.
- Safe rejection expectations for unsupported schemes and private/loopback HTTP URLs.
- Representative OpenAI-style multimodal message blocks.

It intentionally avoids model downloads, GPU execution, and remote HTTP fetches.
