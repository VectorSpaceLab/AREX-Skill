# Server API

## Verified Surface

The server is FastAPI-based and exposes OpenAI-compatible audio routes plus model management.

### Model Management

- `GET /v1/models`
- `POST /v1/models?model_name=...`
- `DELETE /v1/models?model_name=...`

### TTS

- `POST /v1/audio/speech`

Important request fields include `model`, `input`, `voice`, `speed`, `lang_code`, `ref_audio`, `ref_text`, `temperature`, `top_p`, `top_k`, `response_format`, `stream`, `streaming_interval`, and `max_tokens`.

### STT

- `POST /v1/audio/transcriptions`

Important request fields include `file`, `model`, `language`, `max_tokens`, `stream`, `context`, `verbose`, and timestamp-related flags.

### Separation

- `POST /v1/audio/separations`

Returns base64-encoded separated audio buffers.

### Realtime

- `GET /v1/audio/transcriptions/realtime`
- `GET /v1/realtime?model=<model-id>`

`/v1/realtime` follows a model-selection order:

1. `?model=` query parameter
2. `session.update.model` or `session.audio.input.transcription.model`
3. `--realtime-model` / `MLX_AUDIO_REALTIME_MODEL`

## Environment Variables

- `MLX_AUDIO_ALLOWED_ORIGINS`
- `MLX_AUDIO_REALTIME_MODEL`
- `MLX_AUDIO_REALTIME_TRANSCRIPTION_DELAY_MS`
- `MLX_AUDIO_VAD_MODEL`
- `MLX_AUDIO_TTS_MAX_BATCH_SIZE`

## Practical Behavior

- `server_vad` uses the realtime VAD state machine.
- `semantic_vad` is rejected.
- The server can expose the Studio UI with `--start-ui`.
- CORS defaults to `*` unless the user narrows the origin list.
