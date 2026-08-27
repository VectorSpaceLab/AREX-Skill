# Realtime and streaming routes

Use this reference when a task asks for incremental audio, video, text, or image
outputs rather than one blocking HTTP response.

## Route chooser

| Need | Route | Protocol | Notes |
| --- | --- | --- | --- |
| Chat text/image/audio deltas from a chat completion | `POST /v1/chat/completions` with `stream=true` where the loaded model/pipeline supports it | Server-Sent Events | For diffusion image edit, streaming is only for multi-stage AR+image pipelines. |
| Text-to-speech audio chunks | `POST /v1/audio/speech` with `stream=true` or `stream_format` | SSE or raw byte HTTP stream | Requires `response_format="pcm"` or `"wav"` and `speed=1.0` for streaming. |
| Incremental text input for TTS | `WebSocket /v1/audio/speech/stream` | WebSocket | Client sends text chunks and flushes with `input.done`; server sends audio frames per utterance. |
| OpenAI-style realtime audio/text | `WebSocket /v1/realtime` | WebSocket JSON | Audio input is PCM16 mono 16 kHz chunks; output audio deltas are incremental. |
| Native duplex realtime when enabled by the loaded pipeline | `WebSocket /v1/realtime?duplex=1` or `/v1/duplex` | WebSocket JSON | Requires a model/deploy profile with duplex support. |
| Streaming video understanding | `WebSocket /v1/video/chat/stream` | WebSocket JSON | Send frames/audio into a session, then `video.query`; best fit for Qwen3-Omni style video QA. |
| Streaming generated video chunks | `WebSocket /v1/realtime/video` | WebSocket plus binary chunks | Requires a video-generation pipeline that supports chunked streaming output. |
| Ordinary async video generation | `POST /v1/videos` then polling | HTTP multipart + GET | Not realtime; safer for long generation jobs. |

Streaming support is model- and pipeline-specific. If a route returns an
`unsupported` error, first verify that the model was started with `--omni` and
that its deploy profile enables the required runtime extension.

## Speech HTTP streaming

`POST /v1/audio/speech` has three output modes:

1. Non-streaming default: returns complete binary audio such as `audio/wav`.
2. Raw audio stream: set `stream_format="audio"`; receives raw PCM/WAV chunks.
3. OpenAI-style SSE: set `stream=true` or `stream_format="sse"`; receives
   `speech.audio.*` events.

Streaming constraints:

- `response_format` must be `"pcm"` or `"wav"`.
- `speed` must be omitted or `1.0`.
- `word_timestamps=true` is not supported on the HTTP streaming path; use the
  WebSocket speech path for streaming timestamp use cases.

SSE event shapes:

```text
event: speech.audio.delta
data: {"type":"speech.audio.delta","audio":"<base64>","response_format":"pcm"}

event: speech.audio.done
data: {"type":"speech.audio.done","usage":{"input_tokens":119,"output_tokens":77,"total_tokens":196}}
```

Errors in a stream are emitted as `speech.audio.error` instead of `done`.

## TTS text-input WebSocket

Endpoint:

```text
WebSocket /v1/audio/speech/stream
```

Client messages:

| Type | Purpose |
| --- | --- |
| `session.config` | First message. Carries the same request fields as `/v1/audio/speech`, plus `stream_audio`. |
| `input.text` | Append text to the current utterance buffer. |
| `input.done` | Flush the current utterance without closing the socket. |
| `session.close` | End the session. |

Server messages:

| Type | Purpose |
| --- | --- |
| `audio.start` | Audio generation started for an utterance/sentence. |
| binary frame | Audio bytes; multiple frames when `stream_audio=true`. |
| `audio.done` | Audio complete for the sentence. |
| `session.done` | The flushed utterance is complete. |
| `error` | Non-fatal protocol/generation error. |

Operational notes:

- `input.done` is a flush, not a disconnect. Reuse the socket for repeated
  utterances.
- `session.config` is sticky; resend it only between utterances when you need to
  change voice, format, or reference audio.
- `stream_audio=true` requires `response_format="pcm"` and `speed=1.0`.

## OpenAI-style realtime audio/text

Endpoint:

```text
WebSocket /v1/realtime
```

The client sends JSON frames. A safe minimal sequence is:

1. `session.update` with the served model name.
2. Optional `input_audio_buffer.commit` with `final=false` to start generation.
3. One or more `input_audio_buffer.append` frames containing base64 PCM16 mono
   16 kHz audio chunks.
4. `input_audio_buffer.commit` with `final=true` to close the input stream.
5. Read events until `response.audio.done` or `error`.

Minimal event skeleton:

```json
{"type":"session.update","model":"MODEL"}
{"type":"input_audio_buffer.commit","final":false}
{"type":"input_audio_buffer.append","audio":"<base64 pcm16 mono 16k>"}
{"type":"input_audio_buffer.commit","final":true}
```

Expected server events include:

- `session.created` / `session.updated`
- `response.audio.delta` with incremental audio in `audio` or `delta`
- `response.audio.done`
- `transcription.delta` / `transcription.done` for text transcription on
  supported paths
- `error` for unsupported route/model or runtime failures

Client-side invariants distilled from the realtime regression tests:

- Treat each `response.audio.delta` as incremental audio and append chunks in
  receive order.
- Save chunk sample rates from `sample_rate_hz` when present; defaulting to
  24 kHz is safer than assuming the input 16 kHz rate.
- For native duplex, ignore `response.listen` events observed before the post-
  commit `input_audio_buffer.committed` acknowledgement; decisions before the
  final commit may only describe streaming state.
- If the final input chunk is not aligned to the model's audio unit size, wait
  for a post-commit listen/speak decision or response drain rather than closing
  immediately.
- Demo clients that require a reference voice should fail fast when `ref_audio`
  is absent; do not silently substitute an arbitrary voice sample.

## Native duplex realtime

Some pipelines expose a native full-duplex runtime. Use either:

```text
WebSocket /v1/realtime?duplex=1
WebSocket /v1/duplex
```

Only use these when the loaded deploy profile and model explicitly support
full-duplex behavior. Otherwise the server returns an unsupported error.

For duplex clients:

- Stream PCM16 mono 16 kHz input.
- Include explicit reference audio when the model/pipeline requires one.
- Expect overlapping `response.listen`, `response.created`,
  `response.audio.delta`, `response.audio_transcript.delta`, and
  `response.done` events.
- Persist output chunks as they arrive when debugging barge-in or interrupt
  behavior; a single final buffer can hide timing errors.

## Streaming video understanding

Endpoint:

```text
WebSocket /v1/video/chat/stream
```

First send `session.config`:

```json
{
  "type": "session.config",
  "model": "MODEL",
  "modalities": ["text", "audio"],
  "max_frames": 64,
  "num_frames": 16,
  "enable_frame_filter": true,
  "frame_filter_threshold": 0.95,
  "use_audio_in_video": true
}
```

Then send frames, optional audio, and a query:

```json
{"type":"video.frame","data":"<base64 jpeg-or-png>"}
{"type":"audio.chunk","data":"<base64 pcm16 16k mono>"}
{"type":"video.query","text":"What is happening in this video?"}
{"type":"video.done"}
```

Server events include `response.start`, `response.text.delta`,
`response.text.done`, `response.audio.delta`, `response.audio.done`,
`session.done`, and `error`.

Known limitations to carry into user guidance:

- Session KV reuse and incremental prefill are not implemented for this route;
  each query rebuilds context from retained frames/audio.
- Back-to-back short replies can expose scheduler idle races; a small delay
  between repeated turns is a practical workaround when clients see idle
  timeouts.
- If the audio buffer exceeds the server limit, the server emits
  `Audio buffer overflow` and clears the current audio buffer for the session.
- The route is intended for models with the matching streaming-video processor;
  do not assume all Omni models support it.

## Streaming image edit

`POST /v1/images/edits` accepts `stream=true` only on multi-stage image-edit
pipelines that generate AR recaption text before the final image. The SSE order
is:

1. `data: {..."type":"ar_delta","delta":"..."...}` one or more times.
2. `data: {..."type":"image","data":[{"b64_json":"..."}]...}` once.
3. `data: [DONE]`.

If the engine fails after SSE has started, it sends an OpenAI-style error chunk
and then `[DONE]`. Single-stage diffusion image edit pipelines reject
`stream=true` with HTTP 400.

## Streaming generated video

`WebSocket /v1/realtime/video` is for generated video chunks. Prefer the simpler
HTTP `/v1/videos` async job route unless the user explicitly needs chunked video
output and the model/deploy profile supports it.

For long-running video generation with ordinary delivery:

1. `POST /v1/videos` to create a job.
2. Poll `GET /v1/videos/{video_id}` until `completed` or `failed`.
3. Download `GET /v1/videos/{video_id}/content`.
4. Use `DELETE /v1/videos/{video_id}` if cleanup is needed.
