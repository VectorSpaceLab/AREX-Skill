# Vision-Language Input Formats

LMDeploy accepts multimodal data in two common forms: a compact pipeline tuple for image-centric VLMs and OpenAI-style chat messages for server-compatible multimodal payloads.

## Offline Pipeline Tuple Forms

Use tuple prompts for simple offline VLM inference through `lmdeploy.pipeline`:

```python
from lmdeploy import pipeline
from lmdeploy.vl import load_image

pipe = pipeline("org/vlm-or-local-folder")
image = load_image("/path/to/image.jpg")
response = pipe(("Describe this image.", image))
```

Supported tuple patterns:

- `("prompt text", image)` where `image` is a `PIL.Image.Image` returned by `load_image`.
- `("prompt text", "/path/to/image.jpg")`; LMDeploy loads string image sources before preprocessing.
- `("prompt text", [image1, image2])` for multi-image prompts.
- `(image, "prompt text")` is normalized by the multimodal processor, but prompt-first form is clearer.
- `[('Describe image A.', image_a), ('Describe image B.', image_b)]` for a batch of independent image prompts.

Multiple images increase visual tokens. Pair them with a larger context window, for example `TurbomindEngineConfig(session_len=8192)`, when prompts or images are long.

## OpenAI-Style Message Content

LMDeploy’s multimodal parser accepts message dictionaries whose `content` is a list of typed blocks. Text-only content is handled by the text pipeline, but multimodal content is detected when a user message contains a supported media block.

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "image_url", "image_url": {"url": "/path/to/image.jpg"}},
        {"type": "text", "text": "Describe this image."},
    ],
}]
response = pipe(messages)
```

Supported content block types:

| Modality | Type values | Data field | Notes |
| --- | --- | --- | --- |
| Text | `text` | `text` | Multiple text blocks are merged with newlines when falling back to text-only processing. |
| Image | `image_url`, `image`, `image_data` | `image_url.url`, direct string, or `image_data.data` | String sources may be HTTP(S), data URLs, file URLs, or existing local paths. `image_data` accepts a `PIL.Image.Image`. |
| Video | `video_url`, `video` | `video_url.url` or direct string | Native video support is model-specific; use `media_io_kwargs` for frame count or FPS. |
| Audio | `audio_url`, `audio` | `audio_url.url` or direct string | Audio support is model-specific and requires optional audio dependencies. |
| Time series | `time_series_url`, `time_series` | `time_series_url.url` or direct string | Time-series requests should include processor-required fields such as `sampling_rate` when the model expects them. |

A value may be either a direct value or a dictionary containing `url` or `data`:

```python
{"type": "image_url", "image_url": "/path/to/image.jpg"}
{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
{"type": "image_data", "image_data": {"data": pil_image}}
```

## OpenAI API Payloads

For OpenAI-compatible `/v1/chat/completions`, keep the same content blocks inside the request body. The server launch, auth, proxy, and client transport details belong to `serving-apis`; this sub-skill owns the multimodal `messages` shape.

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Compare these two images."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "image_url", "image_url": {"url": "/path/to/second.jpg"}},
    ],
}]
```

Use `extra_body` for multimodal processing controls when calling through an OpenAI client:

```python
extra_body = {
    "mm_processor_kwargs": {"image": {"min_pixels": 4 * 32 * 32, "max_pixels": 256 * 32 * 32}},
    "media_io_kwargs": {"video": {"num_frames": 16, "fps": 2}},
}
```

Use the same keyword arguments directly with `pipe(...)` for offline pipeline calls.

## Local Files, HTTP URLs, and Data URLs

LMDeploy’s media loader accepts:

- HTTP(S) URLs after safety checks block private, loopback, link-local, reserved, multicast, and DNS-rebinding-style mixed private/public resolutions.
- `data:<mime>;base64,<payload>` URLs for base64 media; only base64 data URLs are supported.
- `file://` URLs and existing local paths for local files.

Image helpers:

```python
from lmdeploy.vl import encode_image_base64, load_image

image = load_image("/path/to/image.jpg")
b64 = encode_image_base64(image, format="PNG")
data_url = f"data:image/png;base64,{b64}"
```

Video helpers encode JPEG frame sequences by default, returning comma-separated JPEG frame payloads for `data:video/jpeg;base64,...`. Audio helpers default to 16 kHz unless overridden. Time-series helpers encode NumPy arrays in NPY format.

## Multi-Turn Chat

For image-grounded multi-turn offline chat, put the image in the first user turn, then continue with text turns using the returned session:

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline
from lmdeploy.vl import load_image

pipe = pipeline("org/vlm-or-local-folder", backend_config=TurbomindEngineConfig(session_len=8192))
image = load_image("/path/to/image.jpg")
config = GenerationConfig(max_new_tokens=256, do_sample=False)

session = pipe.chat(("Describe this image.", image), gen_config=config)
print(session.response.text)
session = pipe.chat("What object is most prominent?", session=session, gen_config=config)
print(session.response.text)
```

Keep media on the first turn unless the model documentation explicitly supports adding fresh media later in the same conversation.

## `IMAGE_TOKEN` Placement

LMDeploy defines `lmdeploy.vl.constants.IMAGE_TOKEN` as `<IMAGE_TOKEN>`. Many VLM templates insert image placeholders automatically. Some models require manual placement or benefit from explicit placement for multiple images.

```python
from lmdeploy.vl.constants import IMAGE_TOKEN
prompt = f"Image-1: {IMAGE_TOKEN}\nImage-2: {IMAGE_TOKEN}\nCompare the images."
response = pipe((prompt, [image1, image2]))
```

Rules of thumb:

- Do not add manual tokens unless the model’s LMDeploy docs or template behavior requires it.
- If manual tokens are required, the number and order of `IMAGE_TOKEN` placeholders should match the number and order of image items.
- DeepSeek-VL-style prompts commonly require `<IMAGE_TOKEN>` in the prompt text.
- For InternVL-style multi-image prompts, explicit labels such as `Image-1: <IMAGE_TOKEN>` and `Image-2: <IMAGE_TOKEN>` can avoid ambiguous grounding.

## Custom VLM Folders and Templates

LMDeploy chooses a built-in chat template from the model path when possible. If a local folder name hides the original model family, pass `ChatTemplateConfig`:

```python
from lmdeploy import ChatTemplateConfig, pipeline

pipe = pipeline(
    "local_model_folder",
    chat_template_config=ChatTemplateConfig(model_name="llava-v1"),
)
```

If OpenAI-style messages fail with a base-template error, choose a template name from the installed LMDeploy registry or use an official model folder name that LMDeploy recognizes.
