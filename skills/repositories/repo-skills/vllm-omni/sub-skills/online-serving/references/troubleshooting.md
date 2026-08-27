# Online serving troubleshooting

Start with the symptom, then apply the matching checks. Do not run model-loading
examples or download checkpoints unless the user approves the GPU, network, cache,
and time budget.

## `--omni` is missing or ignored

Symptoms:

- `vllm serve MODEL ...` starts but Omni-specific endpoints are absent.
- The server behaves like ordinary vLLM and does not handle image/video/audio
  routes as expected.
- The command reports `unrecognized arguments: --omni`.

Recovery:

1. Use an explicit Omni launch:

   ```bash
   vllm serve MODEL --omni --port 8091
   # or, if the plain vllm executable is stale:
   vllm-omni serve MODEL --omni --port 8091
   ```

2. Confirm the parser can see the Omni group without loading a model:

   ```bash
   vllm-omni serve --omni --help=OmniConfig
   ```

3. If `vllm` does not accept `--omni`, treat it as an installation/version
   alignment problem. Keep using `vllm-omni serve` until the vLLM executable is
   upgraded to the compatible version family.

## Version mismatch warning

Symptoms:

- Importing or starting vLLM-Omni logs a warning that vLLM and vLLM-Omni major or
  minor versions are misaligned.
- `vllm` does not handle `--omni`, even though vLLM-Omni is installed.
- Strange OpenAI route behavior after an otherwise successful import.

Recovery:

1. Check both installed distributions in the active runtime environment:

   ```bash
   python - <<'PY'
   import importlib.metadata as m
   for name in ("vllm", "vllm-omni", "vllm_omni"):
       try:
           print(name, m.version(name))
       except m.PackageNotFoundError:
           pass
   PY
   ```

2. Align vLLM and vLLM-Omni to the same compatible release family. The verified
   extraction environment used vLLM `0.26.0` and a CUDA-capable vLLM-Omni
   editable install; local source-version strings may look different, but the
   functional requirement is that the installed vLLM parser supports `--omni`.
3. Re-run `vllm-omni serve --omni --help=OmniConfig` after changing packages.

## Server not running or wrong port

Symptoms:

- `Connection refused`, `Could not connect to server`, HTTP 404 for an Omni
  route, or WebSocket close before the first session event.

Recovery:

1. Verify the port and base URL. vLLM-Omni examples use several ports; do not
   assume a default.
2. Check liveness:

   ```bash
   curl -sS http://localhost:8091/health
   curl -sS http://localhost:8091/v1/models
   ```

3. If the server is remote or containerized, confirm host binding (`--host
   0.0.0.0` for externally reachable service), firewall rules, container port
   mapping, and reverse-proxy WebSocket upgrade support.
4. For WebSockets, use `ws://host:port/...` or `wss://...` to match the proxy TLS
   endpoint. HTTP URLs are not valid WebSocket URLs.

## Model cache, license, or checkpoint access failures

Symptoms:

- Startup stalls on model download, fails with HTTP authorization errors, or
  reports missing files.
- Hugging Face / ModelScope gated models require an accepted license.
- Startup succeeds in parser-only checks but model-serving examples fail.

Recovery:

1. Ask the user before downloading model weights or accepting model licenses.
2. Confirm the model identifier is correct for the intended endpoint and backend.
3. Confirm cache environment variables, access tokens, and offline cache policy
   in the user's runtime environment.
4. If the user only needs payload construction or launch planning, use the
   bundled payload builder and references without starting a model server.
5. If a model recipe requires model-specific optional packages, install only the
   packages for that selected model family rather than broad demo/dev extras.

## `ignored fields` warning for `height`, `width`, or diffusion parameters

Symptoms:

- Server logs include a warning like `fields were present in the request but
  ignored: {'height', 'width', ...}`.
- A `/v1/chat/completions` image or video request appears to ignore
  `num_inference_steps`, `guidance_scale`, `seed`, or dimensions.

Meaning:

- For chat completions, this warning can be harmless. Upstream OpenAI chat
  schema validation does not include Omni diffusion fields, while vLLM-Omni
  stores and forwards them internally.

Recovery:

1. Check client placement:
   - curl / Python `requests`: put Omni fields under nested JSON
     `"extra_body": {...}`.
   - OpenAI Python SDK: pass `extra_body={...}` as a keyword argument, not as a
     nested dict inside the message body.
2. For dedicated `/v1/images/generations`, `/v1/images/edits`, `/v1/videos`,
   `/v1/audio/speech`, or `/v1/audio/generate`, pass endpoint-specific extension
   fields at top level (or as multipart form fields) rather than nesting them
   under chat-style `extra_body`.
3. Confirm the loaded model actually supports the field. Unsupported diffusion
   or TTS parameters may be ignored by the underlying model or fail in the
   pipeline.

## Endpoint/model mismatch

Symptoms:

- `/v1/images/generations` returns `Diffusion engine not initialized`.
- `/v1/audio/speech` returns no audio or an unsupported speaker error.
- `/v1/videos` creates failed jobs immediately.
- Chat output is text-only when audio/image/video was expected.

Recovery:

1. Match the model family to the endpoint:
   - text/chat/multimodal assistant -> `/v1/chat/completions`
   - image generation -> `/v1/images/generations`
   - image edit -> `/v1/images/edits`
   - video generation -> `/v1/videos` or `/v1/videos/sync`
   - TTS -> `/v1/audio/speech`
   - sound/music/audio generation -> `/v1/audio/generate`
2. For TTS, query voices first:

   ```bash
   curl -sS http://localhost:8091/v1/audio/voices
   ```

3. Ensure model-specific `task_type`, `voice`, `ref_audio`, and `ref_text`
   fields match the loaded checkpoint variant.
4. For chat models that can emit audio or images, include the correct
   `modalities` or model-specific `chat_template_kwargs` in `extra_body`.

## Stage registration, master address, or port errors

Symptoms:

- `--stage-id requires both --omni-master-address and --omni-master-port`.
- Headless worker exits with `--stage-id is required in headless mode`.
- Worker cannot connect/register with the head.
- `No stage config found for stage_id=...`.
- Head starts but no worker stage becomes available.

Recovery:

1. Use the same `MODEL`, `--deploy-config` if any, `--omni-master-address`, and
   `--omni-master-port` for the head and every headless worker.
2. Start the head process first, then workers.
3. Verify the stage id exists in the resolved deploy config.
4. Check that every process has a non-conflicting `CUDA_VISIBLE_DEVICES` mask and
   enough VRAM for its stage.
5. On multi-host or multi-NIC systems, set `--omni-replica-address` only on
   headless workers when auto-detection advertises the wrong local address.
6. Make sure the master port is open between hosts and not already in use.
7. If `--omni-dp-size-local` is greater than 1, include `--stage-id` and plan the
   per-replica devices for that process.

## Prohibited upstream data-parallel flags under `--omni`

Symptoms:

- Parser raises an error listing unsupported CLI args under `--omni`.

Recovery:

Remove the explicit upstream vLLM flags:

- `--data-parallel-size`
- `--data-parallel-size-local`
- `--data-parallel-address`
- `--data-parallel-rpc-port`
- `--data-parallel-start-rank`
- `--data-parallel-backend`
- `--api-server-count`
- `--enable-expert-parallel`

Then configure parallelism through deploy YAML, per-stage `num_replicas`, and
`--omni-dp-size-local` for stage/headless multi-runtime launches.

## Streaming or realtime route is unsupported

Symptoms:

- WebSocket returns `Realtime API is not available`, `Duplex API is not
  available`, `Streaming video is not available`, or closes after an error JSON.
- HTTP streaming request fails with validation errors.

Recovery:

1. Confirm the model/deploy profile supports the route:
   - `/v1/realtime` for OpenAI-style realtime audio/text.
   - `/v1/realtime?duplex=1` or `/v1/duplex` only for native duplex profiles.
   - `/v1/video/chat/stream` for streaming video understanding models.
   - `/v1/realtime/video` only for generated-video chunk streaming.
2. For speech HTTP streaming, set `response_format` to `pcm` or `wav`, keep
   `speed=1.0`, and choose `stream_format="audio"` for raw bytes or
   `stream_format="sse"`/`stream=true` for `speech.audio.*` SSE events.
3. For WebSocket realtime input audio, use mono PCM16 at 16 kHz and base64
   encode raw PCM chunks, not a whole WAV file unless the client explicitly
   strips the WAV header.
4. If a reverse proxy is involved, verify WebSocket upgrade support separately
   from ordinary HTTP routing.

## Image edit or video reference input errors

Symptoms:

- Image edit returns `Field 'image' or 'url' is required`.
- Video generation rejects conflicting reference fields.
- A model allows only one input image but the request sends multiple.

Recovery:

1. For image edit, send at least one uploaded `image` multipart part or an
   extension URL/data reference field supported by the route.
2. For video, use exactly one reference style for each modality:
   - `input_reference=@file` for local upload,
   - `image_reference={"image_url":"..."}` for image URL/data references,
   - `video_reference={"video_url":"..."}` for video URL/data references,
   - `audio_reference={"audio_url":"..."}` for audio URL/data references.
3. Do not combine `input_reference` with `image_reference` or `video_reference`
   for the same reference slot.
4. Respect the loaded model's maximum input-image count.

## Out of memory, timeout, or slow generation

Symptoms:

- CUDA OOM during startup or first request.
- Long generation time or client timeout.
- Video/audio jobs stay queued or fail under high load.

Recovery:

1. Lower request size first:
   - image: smaller `size`, `height`, `width`, lower `n`, fewer steps.
   - video: smaller `size`, fewer `num_frames`, lower `fps`, fewer steps.
   - audio: shorter `audio_length`, fewer steps.
2. Lower server memory pressure with `--gpu-memory-utilization`, stage memory
   overrides, or a multi-stage/multi-GPU deployment plan.
3. Add one optimization at a time. Offload, HSDP, attention backend, cache, and
   quantization choices are model-family decisions; route to `model-recipes` or
   `stage-configuration` before combining them.
4. Increase client timeouts for video/audio generation; these requests can
   legitimately take minutes.

## Unsafe or expensive examples

Many serving examples require a live server, GPUs, model weights, browser
sessions, media files, or long-running WebSockets. In normal skill use:

- Do not instruct future agents to run those examples as smoke tests.
- Use this sub-skill's references and `scripts/build_openai_payload.py` to build
  payloads without network calls.
- Run parser/help checks and static payload checks first.
- Only run live server checks after explicit user approval for ports, model
  downloads/cache, backend, and runtime budget.
