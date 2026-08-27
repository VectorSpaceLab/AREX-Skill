# Multimodal Inputs and Media Safety

Use this reference for image, audio, video, and precomputed media embeddings in vLLM. General `LLM.generate`/`LLM.chat` mechanics belong in the offline inference skill; this file covers multimodal-specific payload structure, limits, and safety checks.

## Model and runner checks

- Multimodal support is model-specific. Check the model family supports the requested media type and prompt format before assuming `<image>`, video frames, audio arrays, or OpenAI content parts are accepted.
- Some multimodal models require `trust_remote_code=True`, a custom tokenizer/chat template, or model-specific placeholders such as `<image>`, `<|image_1|>`, or vision/video tokens.
- GPU execution and model downloads are hardware/user-gated. Static payload validation can run without a GPU, but real inference should be verified on the target backend.
- `LLM(...)` accepts multimodal-related constructor fields including `allowed_local_media_path`, `allowed_media_domains`, `mm_processor_kwargs`, and `pooler_config`; additional engine/model kwargs may also be passed through.

## Offline prompt schema

For offline generation, pass a prompt object rather than a plain string when supplying media:

```python
from vllm import LLM

llm = LLM(
    model="llava-hf/llava-1.5-7b-hf",
    limit_mm_per_prompt={"image": 1},
)

outputs = llm.generate({
    "prompt": "USER: <image>\nWhat is in this image?\nASSISTANT:",
    "multi_modal_data": {"image": image_pil},
})
text = outputs[0].outputs[0].text
```

Common offline `multi_modal_data` values:

- `{"image": image}` for one PIL image or a model-accepted image object.
- `{"image": [image1, image2]}` for multiple images, paired with the model's multi-image prompt placeholders and `limit_mm_per_prompt={"image": 2}` or higher.
- `{"audio": (audio_array, sample_rate)}` or model-accepted audio arrays. Audio normalization/resampling is model/processor dependent.
- `{"video": video_frames}` for model-accepted video frame arrays/lists, or processor-specific video data.
- Precomputed embeddings may be accepted by some chat processors as content parts such as `image_embeds`, but validate hidden size and expected model format.

## OpenAI/chat content parts

For `LLM.chat` and OpenAI-compatible requests, multimodal data is expressed as content parts. Typical shape:

```json
{
  "model": "vision-model",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
      ]
    }
  ]
}
```

Supported content part patterns in vLLM include text, `image_url`, `image_pil` in Python chat flows, `image_embeds` for compatible processors, and video content parts for models/endpoints that support them. Scoring multimodal inputs use the same idea without chat roles: `{"content": [{"type": "text", ...}, {"type": "image_url", ...}]}`.

## URL and local file rules

vLLM's media connector accepts only these URL categories for URL-backed media:

- `data:<media-type>;base64,<payload>`: parsed locally; only base64 data URLs are supported.
- `http://` or `https://`: fetched by the server/client media connector. Use domain allowlists for safety.
- `file://...`: allowed only when `allowed_local_media_path`/`--allowed-local-media-path` is set and the resolved file is under that directory.

Safety flags:

```bash
vllm serve MODEL \
  --allowed-local-media-path /srv/vllm-media \
  --allowed-media-domains upload.wikimedia.org example-cdn.invalid
```

Python constructor equivalents:

```python
llm = LLM(
    model="vision-model",
    allowed_local_media_path="/srv/vllm-media",
    allowed_media_domains=["upload.wikimedia.org"],
)
```

Security guidance:

- Do not allow arbitrary local paths. Use a narrow media directory owned by the deployment.
- Prefer `data:` URLs for small test payloads and trusted object storage/CDN domains for production media.
- If relying on remote domains, consider disabling media URL redirects in the deployment environment so redirects cannot bypass the allowlist.
- The bundled `scripts/validate_multimodal_payload.py` helper statically detects local file URLs, remote domains, unsupported schemes, and malformed content parts without downloading media.

## Media limits and processor kwargs

Use `limit_mm_per_prompt` to raise or enforce per-prompt media counts:

```python
llm = LLM(
    model="microsoft/Phi-3.5-vision-instruct",
    trust_remote_code=True,
    max_model_len=4096,
    limit_mm_per_prompt={"image": 2},
)
```

When the model processor needs extra controls, pass `mm_processor_kwargs` or media IO kwargs at model construction. Examples depend on the processor; common categories include image/video resize limits, frame counts, audio sampling behavior, or model-specific switches. If the error says metadata, frame count, image count, or processor kwargs are missing, consult the model card and set those kwargs explicitly rather than changing the prompt alone.

For RGBA images, `media_io_kwargs={"image": {"rgba_background_color": [R, G, B]}}` controls the background used when converting transparency to RGB.

## Shape and content validation checklist

Before running inference:

1. Prompt placeholders match media count and model syntax.
2. `limit_mm_per_prompt` is at least the number of images/audio/video items per prompt.
3. `multi_modal_data` keys use expected modality names: usually `image`, `audio`, or `video`.
4. Chat/OpenAI content is a list of parts, not a raw string when media is present.
5. Every media URL is `data:`, `http(s):`, or `file:`; bare local paths should be converted to `file://` or loaded into Python objects.
6. Local file URLs are under the configured local media root.
7. Remote media hostnames are present in `allowed_media_domains` when a domain allowlist is used.
8. Video/audio arrays include metadata or sample rates when the processor requires them.

## Static payload inspection

From this sub-skill directory, run the bundled validator against an OpenAI/chat-style JSON payload:

```bash
python scripts/validate_multimodal_payload.py payload.json \
  --allowed-local-media-path /srv/vllm-media \
  --allowed-media-domain media.example.com \
  --pretty
```

Expected result fields:

- `ok`: `true` when no blocking errors were found.
- `media_count`: number of URL-like media references discovered.
- `required_flags`: suggested `--allowed-local-media-path` and `--allowed-media-domains` values.
- `errors`: malformed parts, unsupported URL schemes, local files outside allowlist, or remote domains not allowed.
- `warnings`: payload smells such as media-looking raw strings or missing allowlist flags.
