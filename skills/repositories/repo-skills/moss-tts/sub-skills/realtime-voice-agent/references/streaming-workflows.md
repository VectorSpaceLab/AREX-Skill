# MOSS-TTS-Realtime Streaming Workflows

## Purpose

Read this file to run MOSS-TTS-Realtime as a low-latency voice-agent TTS engine without reopening the repository evidence. It covers model loading, non-streaming generation, Gradio streaming, single-turn streaming from LLM text deltas, true multi-turn streaming with KV-cache reuse, and reference audio prompts.

## Core model facts

| Item | Value |
|---|---|
| TTS checkpoint | `OpenMOSS-Team/MOSS-TTS-Realtime` |
| Codec checkpoint | `OpenMOSS-Team/MOSS-Audio-Tokenizer` |
| Output sample rate | 24,000 Hz mono |
| Audio codebooks | 16 RVQ layers |
| Frame rate | about 12.5 frames/sec |
| Recommended decoding | temperature `0.8`, top-p `0.6`, top-k `30`, repetition penalty `1.1`, repetition window `50` |
| Streaming prefill | `prefill_text_len=12` text tokens by default |
| Main use case | context-aware, voice-consistent real-time voice agents |

The Realtime demo and service paths require CUDA in the current implementation. Use `sdpa` as the practical default attention implementation unless FlashAttention 2 is installed and supported by the GPU/dtype combination.

## Choose the workflow

| User goal | Use this route | Notes |
|---|---|---|
| Save one or more WAV files from complete text | [Basic non-streaming inference](#basic-non-streaming-inference) | Simpler but not lowest latency. |
| Interactive browser demo with warmup and sliders | [Gradio streaming demo](#gradio-streaming-demo) | Good for manual validation and latency tuning. |
| Feed live LLM text deltas to TTS for one answer | [Single-turn streaming](#single-turn-streaming-from-llm-deltas) | Uses one `MossTTSRealtimeStreamingSession` turn and finalizes with `end_text()`/`drain()`. |
| Keep dialogue history across several spoken turns | [Multi-turn streaming with KV-cache reuse](#multi-turn-streaming-with-kv-cache-reuse) | Keep one session object; reset cache only for the first turn or a new conversation. |
| Serve remote clients over HTTP | `references/fastapi-service.md` | The bundled service coordinates one active audio stream per session and batch size `1`. |

## Basic non-streaming inference

Use non-streaming when latency is not the primary concern or when you need a simple batch of generated audio-token sequences.

```python
import importlib.util
from pathlib import Path

import torch
import torchaudio
from transformers import AutoModel, AutoTokenizer

from mossttsrealtime.modeling_mossttsrealtime import MossTTSRealtime
from inferencer import MossTTSRealtimeInference

MODEL_ID = "OpenMOSS-Team/MOSS-TTS-Realtime"
CODEC_ID = "OpenMOSS-Team/MOSS-Audio-Tokenizer"
SAMPLE_RATE = 24000

if not torch.cuda.is_available():
    raise RuntimeError("MOSS-TTS-Realtime inference is intended for CUDA in the bundled workflows.")

device = torch.device("cuda:0")
dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

if importlib.util.find_spec("flash_attn") is not None:
    attn_impl = "flash_attention_2"
else:
    attn_impl = "sdpa"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = MossTTSRealtime.from_pretrained(
    MODEL_ID,
    attn_implementation=attn_impl,
    torch_dtype=dtype,
).to(device).eval()
codec = AutoModel.from_pretrained(CODEC_ID, trust_remote_code=True).to(device).eval()

inferencer = MossTTSRealtimeInference(
    model,
    tokenizer,
    max_length=5000,
    codec=codec,
    codec_sample_rate=SAMPLE_RATE,
    codec_encode_kwargs={"chunk_duration": 8},
)

texts = [
    "Welcome to MOSS-TTS-Realtime.",
    "This second sentence can use the same reference voice.",
]
# Use None or a list of paths. One path can be broadcast to multiple texts.
reference_paths = ["prompt.wav", "prompt.wav"]

generated = inferencer.generate(
    text=texts,
    reference_audio_path=reference_paths,
    temperature=0.8,
    top_p=0.6,
    top_k=30,
    repetition_penalty=1.1,
    repetition_window=50,
    device=device,
)

for index, audio_tokens in enumerate(generated):
    token_tensor = torch.as_tensor(audio_tokens, device=device)
    decoded = codec.decode(token_tensor.permute(1, 0), chunk_duration=8)
    wav = decoded["audio"][0].detach().cpu()
    torchaudio.save(f"realtime_{index}.wav", wav, SAMPLE_RATE)
```

Reference audio is optional. Pass `None` or no path for a generic voice prompt; pass a 24 kHz mono-compatible audio file for voice cloning.

## Gradio streaming demo

The Gradio app is useful for manual streaming inspection because it exposes prompt audio, user audio, assistant text, generation parameters, streaming chunk sizes, warmup state, and final audio.

Launch shape:

```bash
python app.py \
  --model_path OpenMOSS-Team/MOSS-TTS-Realtime \
  --tokenizer_path OpenMOSS-Team/MOSS-TTS-Realtime \
  --codec_model_path OpenMOSS-Team/MOSS-Audio-Tokenizer \
  --device cuda:0 \
  --attn_implementation sdpa \
  --host 0.0.0.0 \
  --port 18082
```

Important app behavior:

- Startup runs a warmup thread before enabling the Generate button; this hides the first torch compile/cold-cache stall from normal traffic.
- Queue concurrency is `1`, matching the Realtime decoder and codec streaming assumptions.
- Prompt WAV and user WAV are optional. If provided, they are encoded by the codec and cached by path, modified time, and chunk duration.
- If user WAV is missing, the app builds a text-only user turn. If user WAV is present, it uses `reset_turn(user_text=..., user_audio_tokens=..., include_system_prompt=True, reset_cache=True)`.
- Streaming options that matter most for latency are text chunk tokens, decode chunk frames, codec chunk duration, prebuffer seconds, and input delay.

## Single-turn streaming from LLM deltas

Use this pattern when an LLM emits text chunks and the voice agent should begin speaking before the full assistant message is available.

### State setup

1. Load the tokenizer, model, and codec on the same CUDA device.
2. Create `MossTTSRealtimeProcessor(tokenizer)`.
3. Encode optional prompt audio to codec tokens and call `session.set_voice_prompt_tokens(prompt_tokens)`.
4. Build a turn input. For a text-only assistant response, concatenate `processor.make_ensemble(prompt_tokens)` with an assistant-prefix prompt.
5. Call `session.reset_turn(input_ids=..., include_system_prompt=False or True, reset_cache=True)` for this new single turn.
6. Create `AudioStreamDecoder(codec, chunk_frames=3..6, overlap_frames=0, decode_kwargs={"chunk_duration": -1}, device=device)`.

### Delta loop

```python
from mossttsrealtime.processing_mossttsrealtime import MossTTSRealtimeProcessor
from mossttsrealtime.streaming_mossttsrealtime import (
    AudioStreamDecoder,
    MossTTSRealtimeInference,
    MossTTSRealtimeStreamingSession,
)

inferencer = MossTTSRealtimeInference(model, tokenizer, max_length=3000)
inferencer.reset_generation_state(keep_cache=False)

session = MossTTSRealtimeStreamingSession(
    inferencer,
    processor,
    codec=codec,
    codec_sample_rate=24000,
    codec_encode_kwargs={"chunk_duration": 0.24},
    prefill_text_len=processor.delay_tokens_len,
    temperature=0.8,
    top_p=0.6,
    top_k=30,
    do_sample=True,
    repetition_penalty=1.1,
    repetition_window=50,
)

# Set or clear a reference voice prompt before reset_turn.
if prompt_tokens is not None:
    session.set_voice_prompt_tokens(prompt_tokens)
else:
    session.clear_voice_prompt()

session.reset_turn(input_ids=turn_input_ids, include_system_prompt=True, reset_cache=True)
decoder = AudioStreamDecoder(codec, chunk_frames=3, overlap_frames=0, decode_kwargs={"chunk_duration": -1}, device=device)

with codec.streaming(batch_size=1):
    for delta_text in llm_text_deltas:
        audio_frames = session.push_text(delta_text)
        for wav_chunk in decode_audio_frames(audio_frames, decoder):
            yield wav_chunk

    final_frames = session.end_text()
    for wav_chunk in decode_audio_frames(final_frames, decoder):
        yield wav_chunk

    while True:
        more_frames = session.drain(max_steps=1)
        if not more_frames:
            break
        for wav_chunk in decode_audio_frames(more_frames, decoder):
            yield wav_chunk
        if session.inferencer.is_finished:
            break

    final_chunk = decoder.flush()
    if final_chunk is not None:
        yield final_chunk
```

The missing helper in the snippet is intentionally small: each audio frame is a `[1, 16]` or `[T, 16]` audio-token tensor. Drop rows at or after the audio EOS token, push valid rows into the decoder with `decoder.push_tokens(tokens)`, then yield `decoder.audio_chunks()`.

### Finalization rule

Always call `end_text()`, repeatedly call `drain(max_steps=1)` until empty or `is_finished`, and flush the decoder. If the stream is shorter than the `12`-token prefill threshold, `end_text()` is what forces generation to start.

## Text-delta bridge

For direct external-LLM integration, prefer `MossTTSRealtimeTextStreamBridge` when you already have a configured `MossTTSRealtimeStreamingSession` and `AudioStreamDecoder`.

```python
from mossttsrealtime.streaming_mossttsrealtime import MossTTSRealtimeTextStreamBridge

bridge = MossTTSRealtimeTextStreamBridge(
    session=session,
    decoder=decoder,
    batch_size=1,
)

with codec.streaming(batch_size=1):
    for wav_chunk in bridge.stream_from_text_deltas(llm_text_deltas, drain_step=1):
        yield wav_chunk
```

Use `bridge.push_text_delta(delta)` for manual loops and `bridge.finish()` when the text stream ends. If your upstream source emits token ids rather than text, use `bridge.push_text_tokens(token_ids)` or `TextDeltaTokenizer(tokenizer, hold_back=3)` to keep unstable tail tokens from being emitted too early.

## Multi-turn streaming with KV-cache reuse

True multi-turn context reuse is a Python-session pattern: keep the same `MossTTSRealtimeStreamingSession` and underlying `MossTTSRealtimeInference` across turns.

First turn:

```python
session.reset_turn(
    user_text=turn0_user_text,
    user_audio_tokens=turn0_user_audio_tokens,
    include_system_prompt=True,
    reset_cache=True,
)
```

Later turns in the same conversation:

```python
session.reset_turn(
    user_text=next_user_text,
    user_audio_tokens=next_user_audio_tokens,
    include_system_prompt=False,
    reset_cache=False,
)
```

Then run the same delta loop as the single-turn workflow for each assistant response.

Cache rules:

- Use `reset_cache=True` for a new conversation, a new speaker/context, or after an error that may have corrupted streaming state.
- Use `reset_cache=False` only when the next turn should condition on previous textual and acoustic context.
- Set `include_system_prompt=True` for the first turn so the model gets the TTS system and optional voice-clone prompt. Use `False` on later turns to avoid repeatedly injecting the same system prompt.
- A new `MossTTSRealtimeInference` object starts with no useful KV cache; reuse the object if cache reuse is required.

The FastAPI session id coordinates request, audio stream, and worker lifetime, but the bundled server constructs a fresh streaming session for each `new_turn`; use the Python API above when strict multi-turn KV-cache reuse is required.

## Reference audio prompts

Reference prompt audio can enter the workflow in three forms:

1. A file path loaded with `torchaudio`, converted to mono, and resampled to 24 kHz before codec encoding.
2. Already-encoded audio tokens passed to `set_voice_prompt_tokens(tokens)`.
3. A waveform or token array passed to `set_voice_prompt(...)`; waveform input requires a codec.

Operational guidance:

- Keep prompt audio short and clean; excessive silence or noise weakens voice identity.
- Match the codec sample rate (`24000`) or resample before encoding.
- Audio-token shapes may be `[T, 16]` or `[16, T]`; the processor normalizes both and rejects non-2D shapes.
- If no reference audio is available, call `clear_voice_prompt()` or pass no prompt path; do not leave a stale prompt from a previous user/session.
