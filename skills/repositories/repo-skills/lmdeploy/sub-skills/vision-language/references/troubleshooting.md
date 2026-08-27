# Vision-Language Troubleshooting

Use symptom-first diagnosis. Route backend internals, server launch failures, and quantized artifact creation to their owning sub-skills.

## Optional Dependency ImportError

Symptoms:

- `ImportError: Please install librosa via pip install librosa` for audio.
- `ImportError: Please install soundfile via pip install soundfile` for audio or time-series `.wav`/`.mp3`/`.flac` loading.
- `No video backend found. Install either opencv-python-headless, decord, torchcodec, or torchvision.`
- Model-family docs mention extra packages such as `timm`, model-specific repositories, or constrained `transformers` versions.

Recovery:

- Install only the optional dependencies needed for the requested modality/model.
- For video, choose one supported backend and optionally set `LMDEPLOY_VIDEO_BACKEND` to `cv2`, `decord`, `torchcodec`, or `torchvision`.
- For model-specific processor dependencies, follow the selected model family’s LMDeploy documentation and avoid adding unrelated extras.

## Unsafe or Blocked URL

Symptoms:

- `ValueError: URL is blocked for security reasons`.
- Reasons include unsupported scheme, hostname resolution failure, loopback/private/link-local IPs, metadata service IPs, IPv6 local addresses, or DNS answers containing any non-global IP.

Recovery:

- Use `https://` or `http://` public URLs only when remote fetch is intended.
- Prefer `file://` or `data:<mime>;base64,...` for local and controlled deployments.
- Do not disable safe URL checks to fetch intranet, localhost, or cloud metadata addresses.
- Validate payload syntax with `scripts/check_vl_media_inputs.py` before server-side execution.

## Fetch Timeout or Redirect Failure

Symptoms:

- Request timeout during image or video loading.
- HTTP errors after redirects.
- Large media fetches hang or fail intermittently.

Recovery:

- Download media out-of-band and pass `file://` or a base64 data URL.
- For images, adjust `LMDEPLOY_IMAGE_FETCH_TIMEOUT` if a trusted public image is slow.
- For videos, adjust `LMDEPLOY_VIDEO_FETCH_TIMEOUT`, reduce size, or lower `media_io_kwargs={"video": {"num_frames": ...}}`.
- Remember LMDeploy limits redirects through its HTTP session; use stable final URLs.

## Image Token Placement Problems

Symptoms:

- Model ignores images, grounds the wrong image, or reports a mismatch between image placeholders and media items.
- DeepSeek-VL-style prompts fail unless `<IMAGE_TOKEN>` appears in prompt text.
- Multi-image prompts answer only one image or confuse image order.

Recovery:

- Import `IMAGE_TOKEN` from `lmdeploy.vl.constants` when manual placement is required.
- Match the number and order of `IMAGE_TOKEN` placeholders to the number and order of image items.
- For most VLMs, start without manual tokens and let LMDeploy’s template insert them.
- For models whose docs require explicit placeholders, use labeled prompts such as `Image-1: <IMAGE_TOKEN>` and `Image-2: <IMAGE_TOKEN>`.

## `session_len` Too Small for Multi-Image or Video

Symptoms:

- Context length, max token, prefill, or KV-cache errors on multi-image/video prompts.
- A prompt works with one image but fails with several images or many video frames.

Recovery:

- Increase `TurbomindEngineConfig(session_len=...)` or the equivalent backend setting if memory allows.
- Reduce `media_io_kwargs` video `num_frames`/`fps`.
- Reduce `mm_processor_kwargs` pixel budgets when supported by the model processor.
- Shorten prompt history for multi-turn image chat.

## Batch Media Shape Mismatch

Symptoms:

- Batched VLM call fails when entries mix single images, image lists, and malformed nested lists.
- Processor errors mention unexpected image type or invalid multimodal item.

Recovery:

- Keep each batch element as a complete independent prompt: `[('Prompt A', image_a), ('Prompt B', image_b)]`.
- For a single prompt with multiple images, use `('Prompt', [image_a, image_b])`, not a batch list of bare images.
- In OpenAI-style messages, each media block should be its own content item with a valid `type` and matching field name.
- Validate that string media sources are URLs, data URLs, file URLs, or existing local paths.

## Chat Template Mismatch

Symptoms:

- Error says the base template cannot handle OpenAI messages and suggests specifying `--chat-template`.
- A renamed local VLM folder behaves like text-only inference or inserts the wrong media placeholder.
- Responses include raw template markers or ignore VLM media.

Recovery:

- Pass `ChatTemplateConfig(model_name="template-name")` when creating `pipeline(...)` for custom local folders.
- Use official model folder names when possible so LMDeploy can infer the template.
- If serving through CLI, pass the matching chat-template option documented by `lmdeploy serve api_server --help` and the serving sub-skill.

## Unsupported Modality for Selected Model

Symptoms:

- Image works but video/audio/time-series content fails.
- Error reports unknown processor fields, unsupported content type, or missing modality token support.

Recovery:

- Confirm the selected model family supports the requested modality in LMDeploy.
- Use image-only prompts for image VLMs; route video/audio/time-series requests to a model family that supports them.
- Keep `mm_processor_kwargs` keys aligned with the modality, for example `{"video": {...}}` for `video_url` items.

## Chemistry or Molecular Media Gaps

Symptoms:

- Chemistry-related prompts, molecular diagrams, SMILES, or RDKit-backed media processing fail with missing optional chemistry packages.
- The selected VLM treats a molecule image as generic pixels without chemistry-specific parsing.

Recovery:

- Treat molecule diagrams as normal images unless the selected model explicitly supports chemistry-aware inputs.
- Install chemistry-specific optional packages, such as RDKit, only if the model’s own documentation requires them.
- Do not assume LMDeploy’s generic media loader supplies chemistry semantics; validate with a targeted model-level test.

## When to Escalate

Escalate to `backend-extension` when failures require changing packaged VLM model implementations, adding a new processor, modifying multimodal token expansion, or debugging backend tensor wrappers. Escalate to `serving-apis` when the payload is valid but the API server, proxy, auth, or client transport fails.
