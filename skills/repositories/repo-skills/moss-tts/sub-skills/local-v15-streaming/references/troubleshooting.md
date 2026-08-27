# Local v1.5 troubleshooting

Use this checklist for MOSS-TTS-Local-Transformer-v1.5 batch inference and realtime streaming decode.

## FlashAttention fallback

**Symptoms**

- Import or runtime errors mentioning `flash_attn` / `flash_attention_2`.
- Loading fails on an older CUDA GPU.
- Attention backend errors appear before generation starts.

**What is happening**

The runtime requests `flash_attention_2` by default, but only uses it when CUDA is available, the `flash_attn` package is installed, the dtype is fp16/bf16, and the GPU capability is high enough. Otherwise it falls back to `sdpa` on CUDA or `eager` on CPU.

**Fixes**

- Set `ATTN_IMPLEMENTATION=sdpa` or pass `--attn-implementation sdpa` for CUDA fallback.
- Use `--attn-implementation eager` only for CPU/correctness debugging.
- In batch scripts, disable the problematic cuDNN SDPA backend while keeping other SDPA choices enabled:

```python
torch.backends.cuda.enable_cudnn_sdp(False)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
torch.backends.cuda.enable_math_sdp(True)
```

Do not assume FlashAttention is required; v1.5 can run with SDPA when FlashAttention is unavailable.

## Codec fp32 vs bf16

**Symptoms**

- Codec load runs out of memory.
- Codec decode emits unstable audio, NaNs, or fails after changing dtype.
- TTS fits on GPU but codec pushes memory over the limit.

**Rules**

- Codec encoder/decoder weights default to `fp32` for stability.
- `CODEC_WEIGHT_DTYPE=bf16` / `--codec-weight-dtype bf16` reduces memory.
- Codec non-quantizer compute defaults to `bf16`; use `CODEC_COMPUTE_DTYPE=fp32` when debugging numerical issues.
- The quantizer stays fp32 even when codec weight dtype is bf16.

**Fixes**

- If memory is the only issue, try codec weights in bf16 first.
- If audio becomes noisy or decode fails after bf16, return codec weights to fp32.
- Keep TTS dtype and codec dtype decisions separate: the TTS model can be bf16 while codec weights remain fp32.

## Two-GPU split vs one GPU

**Symptoms**

- CUDA out-of-memory during runtime load.
- Codec worker stalls or starves generation on one busy GPU.
- Runtime says CUDA was requested but CUDA is unavailable.

**Fixes**

- Two GPU setup: put TTS on one GPU and codec on another, e.g. `TTS_DEVICE=cuda:0 CODEC_DEVICE=cuda:1`.
- One GPU setup: set both to the same GPU, e.g. `TTS_DEVICE=cuda:0 CODEC_DEVICE=cuda:0`.
- Do not set CUDA devices if `torch.cuda.is_available()` is false; use CPU only for short correctness checks.
- If a second GPU is unavailable, reduce `max_new_frames`, increase `codec_chunk_frames`, or disable live playback to reduce contention.

## CPU is too slow for realtime

**Symptoms**

- First audio latency is very high.
- `generation_realtime_factor` stays well below 1.0.
- Browser playback underruns even with adaptive chunks.

**Fixes**

- Treat CPU/eager mode as a smoke test, not a realtime target.
- Use short text and very small `max_new_frames` on CPU.
- Disable live streaming playback and wait for the final WAV if GPU is unavailable.
- Prefer CUDA with bf16 TTS dtype; the Qwen3-4B-derived TTS model plus 48 kHz stereo codec is not a practical CPU realtime workload.

## Continuation requires the reference transcript

**Symptoms**

- The web app rejects a continuation job.
- The continuation starts from the wrong timing or ignores the intended prefix.
- Speaker/style is inconsistent after a prompt audio.

**Rules and fixes**

- Continuation and Continuation + Clone modes require reference audio plus a Reference Audio Transcript.
- The transcript must correspond to the reference audio, not the new text only.
- Programmatic continuation should build the user text as `reference_transcript + continuation_text`, then add `processor.build_assistant_message(audio_codes_list=[reference_audio])` and call the processor with `mode="continuation"`.
- If no reference audio is supplied, the streaming helper degenerates to direct TTS; do not expect continuation conditioning.

## Stereo shape mistakes

**Symptoms**

- Saved WAV has wrong channel count.
- Playback is mono or sounds phase/corruption-like.
- `torchaudio.save` raises a tensor shape error.

**Rules and fixes**

- v1.5 codec returns stereo audio as channel-first `[2, samples]`.
- Save directly: `torchaudio.save(path, audio, sample_rate)`.
- Do not `unsqueeze(0)` around decoded v1.5 stereo audio; that creates a 3-D tensor.
- Streaming PCM is sent as interleaved signed 16-bit little-endian with `channels=2` and `sample_rate=48000` headers.
- Reference audio can be mono; the processor repeats mono references to stereo and truncates >2-channel references to two channels before encoding.

## `max_new_frames` vs `tokens` confusion

**Symptoms**

- Generation cuts off early even though duration control is enabled.
- UI progress says `max_new_tokens`, but streaming code mentions `max_new_frames`.
- User sets `tokens=125` and expects the hard cap to change automatically.

**Rules**

- In the streaming Python API, `max_new_frames` is the hard generation cap.
- In the browser form, `max_new_tokens` is the UI/form name for the same hard cap and is mapped to `max_new_frames`.
- `tokens` is a duration-control prompt hint, not the hard cap.
- At 12.5 frames/sec, `125` frames is roughly `10` seconds.
- Each frame contains 12 RVQ layer values; do not multiply `max_new_frames` by 12 unless you are estimating raw codec code values.

**Fixes**

- For desired duration: set `tokens` to the desired frame count and set `max_new_frames`/UI `max_new_tokens` above that value to avoid truncation.
- For open-ended text: estimate duration tokens from text/language, then use a safety margin for the hard cap.
- Use `scripts/estimate_local_v15_tokens.py --text "..." --language English --seconds 10 --json` to compute both a duration-control value and a safe hard cap without loading the model.

## Model and cache download problems

**Symptoms**

- Runtime fails while resolving the model or codec.
- Remote-code loading asks for trust or cannot find custom classes.
- The TTS model loads but the codec/tokenizer is missing or mismatched.

**Fixes**

- Use `trust_remote_code=True` for both processor/model loading through the Hugging Face APIs.
- Keep model and codec IDs paired: v1.5 TTS with `OpenMOSS-Team/MOSS-Audio-Tokenizer-v2`.
- If network access is restricted, pre-stage both the model checkpoint and codec in accessible local directories and pass those directories as `MODEL_DIR`/`CODEC_DIR` or CLI `--model-dir`/`--codec-dir`.
- Do not mix the older local-transformer codec assumptions with v1.5; v1.5 is 48 kHz stereo and fixed at 12 RVQ layers.
- If a local model directory exists, make sure it contains all remote-code files and config needed by `AutoModel` and `AutoProcessor`.

## Generated output metadata

**Symptoms**

- The stream played but the final result is missing.
- The final WAV is empty or shorter than expected.
- Progress shows frames but the result endpoint is not ready.

**What to check**

Each finished streaming run should produce:

- `generated.wav`: final 48 kHz stereo WAV.
- `audio_tokens.pt`: generated `[frames, 12]` audio-frame IDs.
- `metadata.json`: generation request and runtime metrics.

Metadata fields to inspect:

- `mode` and `processor_mode`: confirm direct/clone/continuation path.
- `tokens_control`, `tokens`, and `max_new_frames`: confirm duration hint and hard cap.
- `generated_frames` and `duration_seconds`: confirm actual output length.
- `sample_rate`: should be `48000`.
- `first_audio_latency_seconds`, `generation_realtime_factor`, `post_first_generation_realtime_factor`: diagnose speed.
- `decode_chunks_submitted`: confirm the codec worker decoded chunks.
- `audio_path` and `tokens_path`: confirm final files were written.

If `generated_frames` is `0`, the model stopped immediately or the prompt made it emit an end token. Shorten or simplify the text, remove an invalid continuation prompt, and ensure the hard cap is positive.
