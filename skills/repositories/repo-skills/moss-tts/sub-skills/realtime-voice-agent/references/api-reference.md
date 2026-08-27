# MOSS-TTS-Realtime API Reference

## Purpose

Use this reference for exact Realtime operating constants, public class responsibilities, method contracts, and FastAPI schemas. It is distilled for runtime use and intentionally omits internal implementation details that are not needed to operate a voice-agent workflow.

## Constants and defaults

| Name | Value / behavior |
|---|---|
| Realtime checkpoint | `OpenMOSS-Team/MOSS-TTS-Realtime` |
| Codec checkpoint | `OpenMOSS-Team/MOSS-Audio-Tokenizer` |
| Architecture summary | Qwen3-1.7B-derived backbone plus a 4-block local transformer that generates RVQ audio tokens. |
| Sample rate | 24,000 Hz for Realtime audio. |
| Audio codebooks/channels | 16 RVQ layers. |
| Token layout | Mixed text/audio arrays usually have shape `[T, 17]`: text channel plus 16 audio channels. |
| Audio channel pad/BOS/EOS | pad `1024`, BOS `1025`, EOS `1026`. |
| Text/audio pad ids | text pad `151655`, audio pad `151654`. |
| Default streaming delay | `delay_tokens_len=12`; `MossTTSRealtimeStreamingSession` default `prefill_text_len=12`. |
| Recommended sampling | temperature `0.8`, top-p `0.6`, top-k `30`, repetition penalty `1.1`, repetition window `50`. |
| Long context claim | Up to 32K context tokens for extended conversations. |
| Primary service limit | Batch size `1` for the provided streaming service/bridge. |

## Model and codec loading

```python
import torch
from transformers import AutoModel, AutoTokenizer
from mossttsrealtime.modeling_mossttsrealtime import MossTTSRealtime

MODEL_ID = "OpenMOSS-Team/MOSS-TTS-Realtime"
CODEC_ID = "OpenMOSS-Team/MOSS-Audio-Tokenizer"

device = torch.device("cuda:0")
dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = MossTTSRealtime.from_pretrained(
    MODEL_ID,
    attn_implementation="sdpa",
    torch_dtype=dtype,
).to(device).eval()
codec = AutoModel.from_pretrained(CODEC_ID, trust_remote_code=True).to(device).eval()
```

Use `flash_attention_2` only when FlashAttention 2 is installed, CUDA is available, the GPU compute capability is suitable, and the dtype is `float16` or `bfloat16`. Use `sdpa` for the standard CUDA path and `eager`/none-like settings only for debugging or fallback.

## `MossTTSRealtimeProcessor`

Import:

```python
from mossttsrealtime.processing_mossttsrealtime import MossTTSRealtimeProcessor
```

Constructor defaults:

```python
MossTTSRealtimeProcessor(
    tokenizer,
    audio_pad_token="<|audio_pad|>",
    text_pad_token="<|text_pad|>",
    tts_system_prompt=None,
    channels=16,
    audio_channel_pad=1024,
    audio_bos_token=1025,
    audio_eos_token=1026,
    delay_tokens_len=12,
)
```

Methods:

| Method | Contract |
|---|---|
| `make_ensemble(prompt_audio_tokens=None) -> np.ndarray` | Builds the system/context prompt. With prompt tokens, injects audio-codebook rows into `<|audio_pad|>` positions. Returns `[T, 17]`. |
| `make_voice_clone_prompt(prompt_audio_tokens_len: int) -> str` | Builds the text portion that tells the assistant section to use the reference timbre. |
| `make_user_prompt(text: str, audio_tokens: np.ndarray) -> np.ndarray` | Builds a user turn from user text plus user speech tokens and appends the assistant prefix. |

Audio token normalization accepts `[T, 16]` or `[16, T]` 2D arrays and rejects shapes that cannot be interpreted as 16-channel RVQ tokens.

## `MossTTSRealtimeInference` for streaming

Import:

```python
from mossttsrealtime.streaming_mossttsrealtime import MossTTSRealtimeInference
```

Constructor defaults:

```python
MossTTSRealtimeInference(
    model,
    tokenizer,
    max_length=1000,
    channels=16,
    audio_channel_pad=1024,
    audio_bos_token=1025,
    audio_eos_token=1026,
    text_pad_id=151655,
    aud_pad_id=151654,
)
```

Key methods:

| Method | Contract |
|---|---|
| `reset_generation_state(keep_cache=True)` | Clears generated-token state. If `keep_cache=False`, also drops `past_key_values` and `attention_mask`. |
| `prefill(input_ids, text_prefix_ids, max_prefill_len=None, past_key_values=None, device=None, temperature=0.8, top_p=0.6, top_k=30, do_sample=True, repetition_penalty=1.1, repetition_window=50) -> torch.Tensor` | Runs the initial prompt plus first stable text prefix. Requires at least one prefix token. Updates KV cache and returns first audio-token frame. |
| `step(text_token, temperature=0.8, top_p=0.6, top_k=30, do_sample=True, repetition_penalty=1.1, repetition_window=50) -> torch.Tensor` | Adds one text token or a text-pad token and returns the next audio-token frame. Requires prior `prefill()`. |
| `finish(max_steps=None, ...) -> list[torch.Tensor]` | Continues stepping with text-pad tokens until EOS, `max_steps`, or `max_length`. |
| `is_finished` | True when all batch items have emitted audio EOS. |

The local transformer uses a dynamic local cache for FlashAttention 2 and a static local cache otherwise. The non-FlashAttention path may use `torch.compile` for the local transformer, causing a cold first-call pause.

## `MossTTSRealtimeStreamingSession`

Import:

```python
from mossttsrealtime.streaming_mossttsrealtime import MossTTSRealtimeStreamingSession
```

Constructor defaults:

```python
MossTTSRealtimeStreamingSession(
    inferencer,
    processor,
    codec=None,
    codec_sample_rate=24000,
    codec_encode_kwargs=None,
    prefill_text_len=12,
    text_buffer_size=32,
    min_text_chunk_chars=8,
    temperature=0.8,
    top_p=0.6,
    top_k=30,
    do_sample=True,
    repetition_penalty=1.1,
    repetition_window=50,
)
```

Methods:

| Method | Contract |
|---|---|
| `set_voice_prompt_tokens(audio_tokens)` | Stores pre-encoded reference voice tokens. |
| `set_voice_prompt(audio, sample_rate=None)` | Accepts audio tokens, waveform, or path-like audio. Waveform/path input requires `codec`; non-24 kHz input is resampled when sample rate is known. |
| `clear_voice_prompt()` | Removes the stored reference voice prompt. Use before generic-voice turns. |
| `reset_turn(user_text=None, user_audio_tokens=None, input_ids=None, include_system_prompt=None, reset_cache=False)` | Prepares a new user/assistant turn. If `input_ids` is absent, both `user_text` and `user_audio_tokens` are required. `include_system_prompt` defaults to true only for the first turn. `reset_cache=True` starts a fresh conversation. |
| `push_text_tokens(tokens) -> list[torch.Tensor]` | Pushes token ids directly and drains any generated audio frames. |
| `push_text(text_fragment) -> list[torch.Tensor]` | Appends text deltas, segments on punctuation/length, tokenizes stable segments, and drains generated frames. |
| `end_text() -> list[torch.Tensor]` | Marks the assistant text stream complete, tokenizes any remaining text cache, and forces prefill if needed. |
| `drain(max_steps=None) -> list[torch.Tensor]` | After prefill, continues audio generation using text-pad tokens. |

Streaming starts only after enough pending text tokens reach `prefill_text_len` or after `end_text()` is called. For text deltas, prefer `push_text()` over naive per-fragment tokenization because it buffers unstable boundaries.

## `AudioStreamDecoder`

Import:

```python
from mossttsrealtime.streaming_mossttsrealtime import AudioStreamDecoder
```

Constructor defaults:

```python
AudioStreamDecoder(
    codec,
    chunk_frames=40,
    overlap_frames=4,
    initial_chunk_frames=None,
    decode_chunk_duration=None,
    decode_kwargs=None,
    device=None,
)
```

Methods:

| Method | Contract |
|---|---|
| `push_tokens(audio_tokens)` | Accepts `[T, 16]` audio-token rows as `np.ndarray` or `torch.Tensor`. |
| `audio_chunks() -> Iterable[torch.Tensor]` | Decodes when enough frames are buffered. Applies optional crossfade. |
| `flush() -> Optional[torch.Tensor]` | Decodes remaining buffered frames and returns the final chunk. |

For low-latency demos, `chunk_frames=3` to `6` and `overlap_frames=0` are common. Larger chunks can improve smoothness at the cost of time to first audio.

## `TextDeltaTokenizer`

Import:

```python
from mossttsrealtime.streaming_mossttsrealtime import TextDeltaTokenizer
```

Contract:

- `TextDeltaTokenizer(tokenizer, hold_back=3)` accumulates full text, re-encodes it on each delta, and returns only newly stable token ids.
- `push_delta(delta) -> list[int]` returns stable token ids and may return an empty list.
- `flush() -> list[int]` returns all remaining token ids at the end of the stream.

Use this when an upstream component wants token-id streaming. For normal LLM text deltas, `MossTTSRealtimeStreamingSession.push_text()` already performs safer text buffering and segmentation.

## `MossTTSRealtimeTextStreamBridge`

Import:

```python
from mossttsrealtime.streaming_mossttsrealtime import MossTTSRealtimeTextStreamBridge
```

Constructor:

```python
MossTTSRealtimeTextStreamBridge(
    session,
    decoder,
    codebook_size=None,
    audio_eos_token=None,
    batch_size=1,
)
```

Methods:

| Method | Contract |
|---|---|
| `push_text_delta(delta) -> Iterator[torch.Tensor]` | Calls `session.push_text(delta)` and yields decoded waveform chunks. |
| `push_text_tokens(token_ids) -> Iterator[torch.Tensor]` | Pushes token ids directly and yields decoded chunks. |
| `finish(drain_step=1) -> Iterator[torch.Tensor]` | Calls `end_text()`, drains, flushes decoder, and yields final chunks. |
| `stream_from_text_deltas(deltas, drain_step=1) -> Iterator[torch.Tensor]` | Wraps `codec.streaming(batch_size=1)`, consumes all deltas, and finalizes. |

The bridge validates batch size during decoding and raises if a frame does not represent a single batch item.

## FastAPI schemas

```python
SessionStartReq = {
    "session_id": str,
    "user_text": str | None,
    "assistant_text": str | None,
    "prompt_audio": str | None,
    "user_audio": str | None,
    "new_turn": bool,  # must be true
}

SessionPushReq = {
    "session_id": str,
    "text": str,
    "is_final": bool,
}

SessionCloseReq = {
    "session_id": str,
}
```

Read `fastapi-service.md` for the request order and audio response headers.
