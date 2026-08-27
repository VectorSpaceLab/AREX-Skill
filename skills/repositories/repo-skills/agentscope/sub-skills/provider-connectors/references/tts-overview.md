# TTS Overview

## Purpose

Read this for the verified text-to-speech constructors, streaming defaults, and provider selection details.

## Verified TTS model families

| Class | Credential | Verified defaults / notes |
| --- | --- | --- |
| `DashScopeCosyVoiceTTSModel` | `DashScopeCredential(api_key=...)` | `model='cosyvoice-v3-flash'`, `stream=True`, optional `cold_start_length` / `cold_start_words` |
| `DashScopeTTSModel` | `DashScopeCredential(api_key=...)` | `model='qwen3-tts-flash'`, `stream=True` |
| `DashScopeRealtimeTTSModel` | `DashScopeCredential(api_key=...)` | `model='qwen3-tts-flash-realtime'`, `stream=True`, optional `cold_start_length` / `cold_start_words` |
| `GeminiTTSModel` | `GeminiCredential(api_key=...)` | `model='gemini-2.5-flash-preview-tts'`, `stream=False` |
| `OpenAITTSModel` | `OpenAICredential(api_key=...)` | `model='tts-1'`, `stream=True` |

## Practical notes

- The DashScope tests cover both streaming and non-streaming byte aggregation.
- Realtime models have lifecycle hooks (`connect`, `close`, `push`) that the tests exercise.
- If a TTS workflow fails, check whether the model family expects streaming or realtime lifecycle management rather than a one-shot call.

## When to use this reference

- Before choosing a voice model for an agent.
- When the API shape is right but the audio output or streaming lifecycle is wrong.
- When you need to compare provider defaults without opening the original source tests.
