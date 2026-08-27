# ASR Python API troubleshooting

Use this reference for Python API failures around imports, audio loading, model caches, device/compute choices, memory, and transcription options. It focuses on safe diagnosis before running expensive model inference.

## Quick triage

```bash
python scripts/inspect_whisperx_api.py --strict
python scripts/check_audio_loading.py
```

The first command verifies imports, signatures, public lazy API presence, and torch CUDA visibility without loading ASR weights. The second verifies `whisperx.load_audio` and `ffmpeg` using a tiny generated WAV.

## Common failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: whisperx` | Package is not installed in the active Python environment. | Install the `whisperx` distribution in the runtime environment that will execute the workflow. Verify with `python -c "import whisperx"`. |
| Import fails for `torch`, `pyannote`, `ctranslate2`, `faster_whisper`, or `transformers` | Incomplete or conflicting dependencies. | Reinstall or repair the package environment according to the package metadata. Use `inspect_whisperx_api.py` to identify the first failing module. |
| `FileNotFoundError` for `ffmpeg` or `Failed to load audio` from `load_audio` | The `ffmpeg` executable is missing, not on `PATH`, or cannot decode the input. | Install `ffmpeg`, verify `ffmpeg -version`, or bypass path decoding by passing a pre-decoded 16 kHz mono NumPy array to `transcribe`. |
| `local_files_only=True` fails to load a model | Cache-only mode was requested but required model files are absent or the cache root is wrong. | Prepopulate the exact model in `download_root`, correct the cache setting, or rerun with `local_files_only=False` only when downloads are explicitly allowed. |
| Model load tries to download unexpectedly | `local_files_only` was left `False`, cache miss occurred, or a VAD backend uses its own cache. | Set `local_files_only=True` for ASR model loading. Avoid `vad_method="silero"` unless torch hub cache/network policy is approved. |
| Authentication or gated-model error | The model source requires credentials or accepted terms. | Supply `use_auth_token` from a secure secret source only when authorized. Do not hard-code or log tokens. For diarization-specific gated models, route to the diarization sub-skill. |
| CUDA is visible to torch but model load fails | CUDA, cuDNN, CTranslate2, torch, or driver versions are incompatible. | Fall back to `device="cpu"` for functional work, or repair the CUDA stack. `torch.cuda.is_available()` is necessary but not sufficient proof of CTranslate2 inference readiness. |
| `compute_type="default"` is slower or uses more memory than expected | Default resolves to `float16` only for `device == "cuda"`; otherwise it resolves to `float32`. | Set `compute_type` explicitly. Try `"int8"` for CPU or memory-constrained runs if accuracy trade-offs are acceptable. |
| GPU out-of-memory during transcription | Model is too large, `batch_size` too high, chunking too large, or multiple models are resident. | Reduce `batch_size` first, then use a smaller model or compatible lower-memory compute type. Delete unused models, run garbage collection, and empty CUDA cache before loading alignment/diarization models. |
| CPU transcription is too slow | CPU inference is expected to be much slower than CUDA, especially with large models or `float32`. | Use a smaller model, explicit `language`, `compute_type="int8"` if compatible, lower `num_workers` contention, and avoid unnecessary alignment/diarization in the same pass. |
| First call is slow before decoding | Language detection runs because no language was preset. | Pass `language` to `load_model` or `transcribe` when known. This is especially helpful for short clips and batch jobs with one known language. |
| Language detection warning on short audio | The audio is shorter than the 30-second language detection window. | Pass the known language code explicitly or accept that auto-detection may be inaccurate. |
| `suppress_numerals=True` removes needed numbers | Numeral/currency-like tokens are intentionally suppressed. | Set `asr_options={"suppress_numerals": False}` or omit it when dates, IDs, prices, percentages, or measurements matter. |
| No progress events are emitted | VAD produced no speech segments, transcription failed before the loop, or no callback was passed. | Check VAD thresholds/audio content, use `verbose=True` only for debugging, and ensure `progress_callback` is a callable. |
| Empty `segments` result | VAD found no active speech or the audio is silent/incorrectly scaled. | Confirm audio is mono 16 kHz with nonzero amplitude, try default VAD thresholds, and check that the input array was not accidentally integer-clipped or all zeros. |
| `vad_method="silero"` hangs or downloads | Silero VAD is loaded through torch hub. | Use default `"pyannote"` for no torch-hub dependency, or prepopulate/approve the torch hub cache before selecting Silero. |
| Custom `vad_model` behaves differently from built-ins | Custom object does not implement WhisperX's expected call, preprocess, and merge behavior. | Prefer built-in VAD unless the custom model has matching `preprocess_audio`, `merge_chunks`, and callable output semantics. |

## Local-cache recipe for offline jobs

For an offline ASR job, require both a prepopulated model cache and cache-only loading:

```python
model = whisperx.load_model(
    "small",
    device="cpu",
    compute_type="int8",
    language="en",
    download_root="model-cache",
    local_files_only=True,
)
```

If this fails, do not silently enable downloads. Surface the cache miss and ask whether to stage model files or allow a network-enabled run.

## Low-memory escalation order

1. Reduce `batch_size` in `model.transcribe(...)`.
2. Use a smaller `whisper_arch`.
3. Use a lower-memory `compute_type` supported by the backend.
4. Lower `chunk_size` if VAD chunks are long.
5. Set `language` explicitly to avoid detection work.
6. Release ASR model objects before loading alignment/diarization models.
7. Fall back to CPU when CUDA is unavailable or unstable, while warning about slowness.

## When to route elsewhere

- If the user needs command-line flags, route to `transcription-cli`.
- If the user needs word/character timestamps or align-model errors, route to `alignment-timestamps`.
- If the user needs speakers, pyannote diarization models, Hugging Face diarization tokens, or speaker assignment failures, route to `diarization-speakers`.
- If the user needs result files or subtitle formatting, route to `outputs-subtitles`.
