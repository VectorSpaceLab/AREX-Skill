# Local v1.5 API reference

This reference names the public runtime surfaces used by MOSS-TTS-Local-Transformer-v1.5 batch decode and realtime streaming decode.

## Processor contract

Load the processor with remote code and the v2 codec:

```python
from transformers import AutoProcessor

processor = AutoProcessor.from_pretrained(
    "OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5",
    trust_remote_code=True,
    codec_path="OpenMOSS-Team/MOSS-Audio-Tokenizer-v2",
    codec_weight_dtype="fp32",      # or "bf16" / "bfloat16" to lower memory
    codec_compute_dtype="bf16",     # or "fp32"
    codec_attention_implementation="sdpa",  # optional; usually set by runtime resolution
)
```

Key methods:

| Method | Use |
|---|---|
| `processor.build_user_message(...)` | Build direct TTS, voice-clone, and duration-control prompts. |
| `processor.build_assistant_message(audio_codes_list=[...])` | Build the prompt-audio assistant prefix required by continuation. |
| `processor(conversations, mode="generation")` | Convert direct TTS or voice-clone conversations into `input_ids` and `attention_mask`. |
| `processor(conversations, mode="continuation")` | Convert a user message plus assistant prompt audio into continuation inputs. |
| `processor.decode(outputs, return_stereo=True)` | Decode generated rows to assistant messages with stereo audio tensors. |
| `processor.encode_audios_from_path(path_or_paths, n_vq=None)` | Encode reference audio into `[T, 12]` codec-frame IDs. |
| `processor.decode_audio_codes(codes, return_stereo=True)` | Decode `[T, 12]` frame IDs back to waveform tensors. |

`build_user_message` accepts these fields:

```python
processor.build_user_message(
    text="target text",
    reference=["reference.wav"],   # optional for voice clone
    instruction=None,
    tokens=125,                    # optional duration-control hint in expected frames/tokens
    quality=None,
    sound_event=None,
    ambient_sound=None,
    language="English",           # optional but recommended when known
)
```

Notes:

- v1.5 fixes `n_vq` to the model config value. Passing another value raises a validation error. The expected value for the public release is `12`.
- The processor converts mono reference audio to stereo by repetition, truncates >2-channel input to two channels, resamples to 48 kHz, and loudness-normalizes before codec encoding.
- `decode(..., return_stereo=True)` returns `[2, samples]`. `return_stereo=False` downmixes to mono.
- Audio-code tensors passed directly as references must have shape `[T, 12]`.

## Batch model generation

Load the model with the same attention backend selected for the runtime:

```python
from transformers import AutoModel

model = AutoModel.from_pretrained(
    "OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5",
    trust_remote_code=True,
    attn_implementation="sdpa",  # or "flash_attention_2" when supported
    torch_dtype=dtype,
).to(device).eval()
```

Common `generate` fields:

| Field | Meaning |
|---|---|
| `input_ids`, `attention_mask` | Output of the v1.5 processor. |
| `max_new_tokens` | Batch-generation hard ceiling. For generated audio, think in frame rows; oversize enough to avoid truncation. |
| `do_sample` | Usually `True` for natural speech variation. |
| `audio_temperature` | Default app value is `1.7`; lower is more deterministic. |
| `audio_top_p` | Default app value is `0.8`. |
| `audio_top_k` | Default app value is `25`. |
| `audio_repetition_penalty` | Default app value is `1.0`. |

The model emits time-synchronous frame rows. Each generated audio frame row carries 12 RVQ layer values; it is not a delay-pattern schedule.

## Streaming Python API

The streaming helper is built around these dataclasses and functions.

### `load_runtime(...)`

```python
runtime = load_runtime(
    model_dir="OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5",
    codec_dir="OpenMOSS-Team/MOSS-Audio-Tokenizer-v2",
    device="cuda",
    tts_device="cuda:0",
    codec_device="cuda:1",
    dtype="bfloat16",
    attn_implementation="flash_attention_2",
    codec_weight_dtype="fp32",
    codec_compute_dtype="bf16",
    warmup=True,
)
```

`load_runtime` resolves attention as follows: request `flash_attention_2` by default, use it only when CUDA, dtype, package, and GPU capability allow it, otherwise fall back to `sdpa` on CUDA or `eager` on CPU.

The returned runtime includes model, processor, resolved devices, dtype, model and codec identifiers, sample rate, frame rate, `n_vq`, attention backend, and codec dtype settings.

### `StreamingRequest`

```python
request = StreamingRequest(
    text="Text to synthesize or continue.",
    mode="voice_clone",        # "voice_clone" or "continuation"
    prompt_text="",            # required by the app for continuation modes with prompt audio
    prompt_audio_path=None,      # optional uploaded/example/recorded reference audio
    language="English",
    tokens_control=False,
    tokens=0,
    max_new_frames=7500,
    do_sample=True,
    temperature=1.7,
    top_p=0.8,
    top_k=25,
    repetition_penalty=1.0,
    text_temperature=1.0,
    text_top_p=1.0,
    text_top_k=50,
    seed=1234,
    codec_chunk_frames=8,       # 0 enables adaptive scheduling
)
```

Mode behavior:

- `mode="voice_clone"` with `prompt_audio_path` uses direct generation with reference audio.
- `mode="voice_clone"` without `prompt_audio_path` falls back to direct generation.
- `mode="continuation"` with `prompt_audio_path` builds a continuation prompt using `prompt_text + text` and the prompt-audio assistant prefix.
- `mode="continuation"` without `prompt_audio_path` degenerates to direct generation.

### `synthesize_stream(runtime, request, output_dir=...)`

This generator yields `StreamingEvent` values:

| Event type | Data highlights |
|---|---|
| `metadata` | `run_id`, sample rate, frame rate, `n_vq`, devices, resolved attention, processor mode, token hint. |
| `progress` | Generated frames, generated seconds, realtime factors, decode queue depth, pending decode frames. |
| `audio` | `waveform` as `[2, samples]`, sample rate, frame/chunk counters, lead metrics. |
| `result` | Final waveform, WAV path, token tensor path, metadata path, metadata dict, audio-token tensor. |

The final metadata dict includes: `run_id`, `mode`, `processor_mode`, `text`, `prompt_text`, `prompt_audio_path`, `language`, `tokens_control`, `tokens`, `max_new_frames`, `generated_frames`, `sample_rate`, `duration_seconds`, latency/realtime metrics, decode chunk count, and output file paths.

### Lower-level helpers

- `build_processor_inputs(runtime, request)` returns processor batch tensors on the TTS device plus optional prompt-audio codes and resolved processor mode.
- `iter_generate_frames(...)` yields generated frame IDs one frame at a time; it currently supports `batch_size=1` and validates the final input channel dimension as `n_vq + 1`.
- `StatefulCodecDecoder(...).decode_codes(codes)` accepts `[T, 12]` long frame IDs and returns `[2, samples]` float audio.
- `estimate_tokens(text, language)` estimates the duration-control prompt value from text length and language; the bundled script provides a no-torch equivalent plus seconds-to-frame conversion.

## Web app HTTP surface

The FastAPI app exposes:

| Endpoint | Purpose |
|---|---|
| `GET /` | Browser UI. |
| `GET /api/health` | Runtime loading status; includes devices, sample rate, attention, codec dtype, and `n_vq` when ready. |
| `GET /api/runtime` | App configuration and nested runtime status. |
| `POST /api/generate-stream/start` | Start a streaming job from multipart form fields. |
| `GET /api/generate-stream/{job_id}/audio` | Raw `pcm_s16le` stream; response headers declare sample rate and channels. |
| `GET /api/generate-stream/{job_id}/status` | Job status/progress JSON. |
| `GET /api/generate-stream/{job_id}/result` | Final result JSON once ready. |
| `GET /api/generate-stream/{job_id}/result-audio` | Final WAV download once ready. |
| `POST /api/generate-stream/{job_id}/close` | Close a job and stop audio streaming. |

Important `POST /api/generate-stream/start` form fields:

| Field | Default | Notes |
|---|---:|---|
| `mode` | `voice_clone` | Accepted: `voice_clone`, `continuation`, `continuation_clone`; no reference audio means direct generation. |
| `language` | empty | Empty means omit language tag. |
| `text` | required | Target text; whitespace-only is rejected. |
| `prompt_text` | empty | Required when continuation-like mode has reference audio. |
| `max_new_tokens` | `7500` | UI name; internally mapped to `max_new_frames`. |
| `codec_chunk_frames` | `8` | Integer 0-32; 0 means adaptive. |
| `seed` | `1234` | Negative means random in the browser. |
| `tokens_control` | `0` | Enables duration-control prompt field. |
| `tokens` | `0` | If enabled and <=0, runtime estimates from text/language. |
| `temperature` | `1.7` | Audio sampling temperature. |
| `top_p` | `0.8` | Audio nucleus sampling. |
| `top_k` | `25` | Audio top-k sampling. |
| `repetition_penalty` | `1.0` | Audio token repetition penalty. |
| `streaming_generation` | `1` | If false, app still runs generation but does not play live chunks. |
| `prompt_audio` | none | Uploaded/recorded reference audio file. |

## CLI/app configuration names

The app accepts environment variables or equivalent CLI flags for model, codec, runtime, and serving configuration:

- `MODEL_DIR` / `--model-dir`
- `CODEC_DIR` / `--codec-dir`
- `OUTPUT_DIR` / `--output-dir`
- `UPLOAD_DIR` / `--upload-dir`
- `DEVICE` / `--device`
- `TTS_DEVICE` / `--tts-device`
- `CODEC_DEVICE` / `--codec-device`
- `TTS_DTYPE` / `--dtype`
- `ATTN_IMPLEMENTATION` / `--attn-implementation`
- `CODEC_WEIGHT_DTYPE` / `--codec-weight-dtype`
- `CODEC_COMPUTE_DTYPE` / `--codec-compute-dtype`
- `HOST` / `--host`
- `PORT` / `--port`
- `--no-warmup`, `--no-preload` for startup behavior.
