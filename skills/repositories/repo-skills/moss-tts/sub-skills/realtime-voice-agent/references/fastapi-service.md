# MOSS-TTS-Realtime FastAPI Service

## Purpose

Read this file to operate the MOSS-TTS-Realtime split request/audio HTTP service: launch settings, environment variables, JSON payloads, session lifecycle, streaming audio response, and client behavior. The service is intended for low-latency voice-agent clients that send text deltas while reading a PCM audio stream.

## Service shape

- Default bind: `0.0.0.0:8083`.
- Main model default: `OpenMOSS-Team/MOSS-TTS-Realtime`.
- Tokenizer default: `OpenMOSS-Team/MOSS-TTS-Realtime`.
- Codec default: `OpenMOSS-Team/MOSS-Audio-Tokenizer`.
- Output media: raw mono PCM16 bytes (`pcm_s16le`) with sample-rate headers.
- Batch caveat: current server/session decoding is designed for batch size `1`.
- Startup loads the model, tokenizer, processor, and codec into the configured CUDA device; failed warmup is printed and later session workers still surface backend load errors.

## Launch configuration

The server CLI accepts these flags and mirrors them into process globals before starting uvicorn:

| Flag | Default | Meaning |
|---|---|---|
| `--host` | `0.0.0.0` | Network interface for uvicorn. |
| `--port` | `8083` | HTTP port. |
| `--target_sr` | env/default `24000` | PCM stream output sample rate. |
| `--model_path` | `OpenMOSS-Team/MOSS-TTS-Realtime` | Realtime checkpoint or local model id. |
| `--tokenizer_path` | `OpenMOSS-Team/MOSS-TTS-Realtime` | Tokenizer id. |
| `--codec_model_path` | `OpenMOSS-Team/MOSS-Audio-Tokenizer` | Codec id; loaded with remote-code support. |
| `--device` | env/default `cuda:0` | CUDA device string. |
| `--attn_impl` | env/default `sdpa` | Attention implementation; common values are `sdpa`, `flash_attention_2`, `eager`, or empty/none-like. |

Equivalent service launch from an installed Realtime app environment:

```bash
python fast_api.py --host 0.0.0.0 --port 8083 --device cuda:0 --attn_impl sdpa
```

Environment variables recognized before CLI overrides:

| Variable | Default | Use |
|---|---|---|
| `MOSS_TTS_TARGET_SR` | `24000` | PCM output sample rate. |
| `MOSS_TTS_MODEL_PATH` | `OpenMOSS-Team/MOSS-TTS-Realtime` | Main model path/id. |
| `MOSS_TTS_TOKENIZER_PATH` | `OpenMOSS-Team/MOSS-TTS-Realtime` | Tokenizer path/id. |
| `MOSS_TTS_CODEC_MODEL_PATH` | `OpenMOSS-Team/MOSS-Audio-Tokenizer` | Codec path/id. |
| `MOSS_TTS_DEVICE` | `cuda:0` | CUDA device. |
| `MOSS_TTS_ATTN_IMPL` | `sdpa` | Attention implementation. |
| `MOSS_TTS_RESAMPLED_AUDIO_DIR` | `./tmp` | Cache directory for resampled prompt WAV files. |
| `MOSS_TTS_AUDIO_PROMPTS_DIR` | `./audio` | Directory used to resolve relative prompt-audio names when the direct path does not exist. |

## Endpoints

| Method/path | Request body | Response | Notes |
|---|---|---|---|
| `GET /health` | none | JSON with status, model ids, target sample rate, device, attention implementation | Use first when diagnosing wrong port/device/model. |
| `POST /tts/session/start` | `SessionStartReq` | `{"ok": true, "session_id": ..., "message": "turn started"}` | Creates/gets a session and queues a new turn. `new_turn` must be true. |
| `POST /tts/session/push` | `SessionPushReq` | accepted length and `is_final` | Sends text deltas. `is_final=true` queues finalization. |
| `GET /tts/session/{session_id}/audio` | none | streaming `application/octet-stream` | Streams raw PCM16; ends after finalization sentinel. |
| `POST /tts/session/close` | `SessionCloseReq` | `{"ok": true, "session_id": ..., "message": "session closed"}` | Sends worker shutdown and removes the session. |

## JSON schemas

### Start a turn

```json
{
  "session_id": "voice-agent-demo",
  "user_text": null,
  "assistant_text": "First text delta can go here.",
  "prompt_audio": "prompt.wav",
  "user_audio": null,
  "new_turn": true
}
```

Fields:

- `session_id` is required and must not be blank.
- `user_text` is optional conversational context for the user turn.
- `assistant_text` is optional initial assistant text. Put the first text delta here to start generation earlier.
- `prompt_audio` is optional reference voice audio. It is resolved relative to the server process; if the path is not found, the service also checks `MOSS_TTS_AUDIO_PROMPTS_DIR`.
- `user_audio` is optional user speech context for the turn.
- `new_turn` must be `true`; if a previous turn is active for the same session id, the server queues finalization before starting the next one.

### Push text deltas

```json
{
  "session_id": "voice-agent-demo",
  "text": "next text delta",
  "is_final": false
}
```

Send `is_final=true` on the last push. If all text was provided in `assistant_text` at start, send a final push with empty text:

```json
{
  "session_id": "voice-agent-demo",
  "text": "",
  "is_final": true
}
```

### Close the session

```json
{
  "session_id": "voice-agent-demo"
}
```

Close after the audio stream has ended. Closing early stops the worker and may truncate audio.

## Audio stream contract

`GET /tts/session/{session_id}/audio` returns raw bytes with headers:

```text
X-Audio-Codec: pcm_s16le
X-Audio-Sample-Rate: 24000
X-Audio-Channels: 1
X-Session-Id: <session_id>
```

Client handling:

1. Interpret chunks as little-endian signed 16-bit PCM.
2. Use the header sample rate when writing WAV.
3. Keep reading until the HTTP iterator ends; the server emits an internal sentinel after finalization.
4. Treat zero chunks plus normal HTTP status as a finalization or decoding issue, not as a valid audio result.

## Recommended client flow

1. Generate or choose a stable `session_id`.
2. Split assistant text into deltas. A practical default is 20-50 characters or sentence-aware chunks.
3. `POST /tts/session/start` with `assistant_text` set to the first delta and optional `prompt_audio`.
4. Start the audio reader thread/process with `GET /tts/session/{session_id}/audio`.
5. For each remaining delta, call `POST /tts/session/push` with `is_final=false` except on the last delta.
6. If there are no remaining deltas, call `POST /tts/session/push` with empty `text` and `is_final=true`.
7. Wait for the audio stream to end and write the bytes as PCM/WAV.
8. `POST /tts/session/close`.

Use the bundled payload planner to produce a safe request sequence without importing the server or model:

```bash
python scripts/realtime_session_payloads.py \
  --text "Welcome to MOSS-TTS-Realtime. This text will be streamed." \
  --chunk-chars 50 \
  --session-id voice-agent-demo \
  --json
```

## Operational caveats

- Batch size is effectively `1` for service decoding and `codec.streaming(batch_size=1)`.
- The service session id coordinates one active turn and its audio queue. For strict multi-turn KV-cache reuse across turns, use the Python session workflow in `streaming-workflows.md`; the bundled service creates a fresh streaming session for each `new_turn`.
- Prompt audio may be resampled and cached. If the underlying prompt changes but path/mtime handling is unusual, restart the service or clear the resample cache.
- If the audio reader connects after `start`, the server uses a pending queue so it does not attach to a previous turn's stream.
- Do not rely on HTTP close alone to finalize synthesis; always send `is_final=true` before close.
