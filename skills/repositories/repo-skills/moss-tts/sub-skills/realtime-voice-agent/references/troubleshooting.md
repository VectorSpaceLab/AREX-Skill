# MOSS-TTS-Realtime Troubleshooting

## Purpose

Use this file when a Realtime voice-agent workflow fails, hangs, returns empty audio, loses voice identity, or has unexpectedly high latency or memory use.

## Quick triage

1. Confirm the selected workflow: Python streaming, Gradio, or FastAPI service.
2. Confirm CUDA visibility and the configured device.
3. Confirm model and codec ids: `OpenMOSS-Team/MOSS-TTS-Realtime` and `OpenMOSS-Team/MOSS-Audio-Tokenizer` unless intentionally overridden.
4. Confirm prompt/user audio paths exist from the running process.
5. Confirm finalization: `end_text()`/`drain()`/decoder `flush()` in Python, or `is_final=true` before reading the final HTTP stream.
6. If the issue is context bleed or voice identity carry-over, inspect `reset_turn(..., reset_cache=...)` and prompt clearing.

## Failure modes and recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Prompt audio not found` or `User audio not found` | Path is relative to a different process directory, the server cannot see the file, or `MOSS_TTS_AUDIO_PROMPTS_DIR` does not contain it. | Use an absolute user-supplied path in the request, or place the file under the configured audio prompts directory and send only the filename. Validate the path before starting the turn. |
| Prompt audio loads but speaker identity is weak or inconsistent | Audio is noisy, too short, stereo with imbalance, wrong sample rate, or stale prompt tokens remained from a previous request. | Convert to clean mono 24 kHz, trim long silence, call `set_voice_prompt_tokens()` for the intended speaker, or `clear_voice_prompt()` when no reference should be used. Restart or clear the prompt-token cache if a prompt file changed but cached tokens are still used. |
| Resampling creates unexpected files or repeated work | Prompt WAV sample rate is not 24 kHz; the service writes a resampled cache under its configured resample directory. | Pre-resample prompt audio to 24 kHz mono before serving, or set `MOSS_TTS_RESAMPLED_AUDIO_DIR` to a writable cache location and clear it when prompts are replaced. |
| HTTP audio stream connects but no bytes arrive | Backend load failed, the turn did not start, text is too short to reach prefill, finalization was not sent, or decoding chunk settings are too large. | Call `/health`, inspect service logs, send at least one non-empty `assistant_text` or push text, send a final push with `is_final=true`, and try smaller `decode_chunk_frames` such as `3` to `6`. |
| Python streaming yields no chunks | `push_text()` has not accumulated `prefill_text_len` tokens and `end_text()` was not called; decoder has buffered fewer frames than `chunk_frames`; or all frames were trimmed at EOS/invalid tokens. | Always call `end_text()`, loop over `drain(max_steps=1)`, then `decoder.flush()`. Lower `chunk_frames` for latency tests. Check token sanitization if frames are discarded. |
| Client hangs at the end of a request | Forgot final push/end call; audio reader is waiting for the server sentinel; session was closed before finalization; or a previous stream queue was reused incorrectly by custom code. | For HTTP, send `POST /tts/session/push` with `is_final=true` before close. For Python, call `end_text()`, drain until empty/finished, then flush. Close sessions only after the stream ends. |
| First request is much slower than later requests | Model download/load, CUDA graph/cache warmup, or `torch.compile` on the local transformer. | Warm up with a short request before serving real traffic. Use the Gradio warmup path for manual testing. Keep the model process alive between requests. |
| `reset_turn must be called before streaming text` | `push_text()` or `push_text_tokens()` was called before preparing the turn. | Call `reset_turn(...)` after setting/clearing the voice prompt and before any assistant text deltas. |
| Dialogue content or voice leaks into a new conversation | KV cache was reused when a fresh conversation was intended, or old prompt tokens were not cleared. | Start new conversations with `reset_cache=True`; create a new `MossTTSRealtimeInference` if needed; call `clear_voice_prompt()` when switching away from a reference voice. |
| Multi-turn context disappears | Cache was reset on every turn or a new inferencer/session object was created. | For true Python multi-turn dialogue, reuse the same `MossTTSRealtimeStreamingSession`; use `include_system_prompt=True, reset_cache=True` only on turn 0 and `include_system_prompt=False, reset_cache=False` on later turns. The bundled FastAPI service does not expose strict KV-cache reuse across new turns. |
| CJK, punctuation-heavy, or very small deltas produce stutter or delayed audio | Token boundaries are unstable when text is split character-by-character; CJK has no whitespace fallback; punctuation segmentation may hold text until `min_text_chunk_chars`. | Prefer `session.push_text(delta)` over manual tokenization. Use sentence or phrase chunks, or `TextDeltaTokenizer(hold_back=3)` for token-id streaming. Always call `flush()`/`end_text()` to release the held tail. |
| `Expected [T, C]`, `Expected [B, C]`, or batch-size errors | Audio tokens have wrong rank/orientation, decoder receives a batch larger than 1, or bridge is used with batch generation. | Normalize audio prompt tokens to `[T, 16]` or `[16, T]` before the processor. Keep service/bridge batch size at `1`. Use separate sessions/processes for concurrent clients rather than batching them through one decoder. |
| `CUDA is required` | The bundled Gradio, FastAPI, and example streaming paths explicitly require CUDA. | Run on a CUDA host, select a valid `--device`/`MOSS_TTS_DEVICE`, or route non-Realtime/generic HF tasks to the HF-family sub-skill if CPU-only behavior is acceptable for a different workflow. |
| Server starts on the wrong port or device | CLI flags and environment variables disagree, or another process already owns the port. | Check `/health` for `target_sr`, `model_path`, `codec_model_path`, `device`, and `attn_impl`. Override with `--host`, `--port`, `--device`, or the `MOSS_TTS_*` variables. Use another port if `8083` is busy. |
| Model or codec download fails | Network/Hugging Face access issue, insufficient cache permissions, or `trust_remote_code` omitted for the codec. | Pre-download/check the model cache in the target environment, ensure network/auth is available when required, and load the codec with `trust_remote_code=True`. Retry after transient network failures. |
| FlashAttention errors or unsupported kernel messages | FlashAttention 2 is not installed, GPU compute capability is too old, dtype is not fp16/bf16, or the model/config attention setting conflicts with the package. | Use `--attn_impl sdpa` as the stable default. Select `flash_attention_2` only when the package and GPU support it. Use `eager` or a none-like setting for debugging correctness rather than speed. |
| Torch compile errors or long compile stalls | The non-FlashAttention local transformer path may call `torch.compile`; dynamic shapes or environment limits can trigger compile overhead. | Warm up once, reduce shape variability during benchmarks, or switch attention/debug settings if compile failures block serving. Do not count cold compile time as steady-state TTFB. |
| CUDA out of memory | 1.7B model plus codec plus KV cache and decoder buffers exceed available memory; stale sessions/processes remain alive; `max_length` is too high. | Stop other GPU processes, lower `max_length`, close unused FastAPI sessions, keep batch size `1`, use bf16/fp16 on CUDA, and consider one service process per GPU. Restart the service after OOM because CUDA state can be unreliable. |
| Audio quality has clicks at chunk boundaries | Decoder chunk size/crossfade settings are too aggressive or codec streaming context is repeatedly entered for each delta. | Keep one `codec.streaming(batch_size=1)` context for the whole turn. Increase `chunk_frames` or add a small `overlap_frames` crossfade if latency budget allows. |
| HTTP response is `404 session not found` for push/audio | Client pushed or opened audio before a successful start, or the session was closed/deleted. | Start the session first and check the start response. Preserve the same `session_id` for start, audio, push, and close. |
| HTTP response is `400 start endpoint requires new_turn=true` | `new_turn=false` was sent to the start endpoint. | Always send `new_turn: true`; use `/tts/session/push` for continuation deltas inside the active turn. |

## Stop conditions

Stop retrying locally and escalate the environment issue when:

- CUDA is unavailable for a Realtime streaming task.
- The target model or codec cannot be downloaded or is blocked by credentials/network policy.
- Prompt/user audio is required but the client cannot provide a readable file or pre-encoded tokens.
- OOM persists after reducing max length, closing sessions, and freeing the GPU.
