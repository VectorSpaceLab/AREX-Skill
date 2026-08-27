# Model, cache, device, and backend notes

## Package/runtime baseline

- Distribution: `whisperx 3.8.7rc1`.
- Import name: `whisperx`.
- Python support from package metadata: `>=3.10,<3.14`.
- Console entry point exists, but CLI work is owned by the transcription CLI sub-skill.

## Device and `compute_type`

`whisperx.load_model(..., compute_type="default")` resolves the compute type from the `device` string:

| `device` value | Default compute type | Notes |
| --- | --- | --- |
| `"cuda"` | `"float16"` | Fast on compatible NVIDIA GPUs, but may fail with insufficient VRAM or CUDA/cuDNN/CTranslate2 mismatches. |
| Anything else, commonly `"cpu"` | `"float32"` | Safer for CPU compatibility, usually slower and more memory-heavy than int8 CPU inference. |

Practical choices:

- Use `torch.cuda.is_available()` as a first probe, but remember that CTranslate2 can still fail later if CUDA libraries are incompatible.
- Use explicit `compute_type` for reproducibility. Common choices include `"float16"`, `"float32"`, and `"int8"`, subject to CTranslate2 support on the target backend.
- For CPU jobs, `"int8"` can reduce memory and improve speed, but may change accuracy.
- For GPU jobs, lower `batch_size` before switching to smaller models or quantized compute if quality matters.

## Cache and offline operation

`load_model` forwards cache controls to the underlying model loader:

```python
model = whisperx.load_model(
    "small",
    device="cpu",
    compute_type="int8",
    download_root="model-cache",
    local_files_only=True,
)
```

| Setting | Behavior |
| --- | --- |
| `download_root=None` | Uses the default cache behavior of the underlying model libraries. |
| `download_root="model-cache"` | Uses a caller-chosen cache/download location. Prefer caller-controlled relative or configured paths in examples. |
| `local_files_only=True` | Cache-only mode: do not attempt network downloads; fail if files are absent. |
| `local_files_only=False` | Allows downloads on cache misses; use only with explicit permission and enough disk space. |
| `use_auth_token=...` | Token forwarded for model retrieval when needed; handle as a secret. |

Cache-only misses are expected when the model has not been prepopulated. The fix is to pre-stage the exact model files or rerun with downloads deliberately enabled in an approved environment.

## Audio representation

WhisperX ASR expects 16 kHz mono waveforms.

- `whisperx.load_audio(path)` uses `ffmpeg` to decode, down-mix to one channel, resample to 16 kHz, and return a `numpy.ndarray` of normalized `float32` samples.
- `model.transcribe(audio_array, ...)` accepts a NumPy array directly and does not know the original sample rate. Resample before passing arrays.
- `log_mel_spectrogram(audio, n_mels, padding=..., device=...)` accepts a path, NumPy array, or torch tensor and returns model features using WhisperX constants: `SAMPLE_RATE=16000`, `CHUNK_LENGTH=30`, `N_SAMPLES=480000`, `N_FRAMES=3000`.

Use `scripts/check_audio_loading.py` to test the path-audio/ffmpeg path without model execution.

## VAD backend behavior inside ASR

`load_model` creates a `FasterWhisperPipeline` with a VAD backend before transcription.

| Setting | Behavior | Risks |
| --- | --- | --- |
| `vad_method="pyannote"` | Default. Uses WhisperX's packaged VAD segmentation model through pyannote components. | Requires pyannote dependencies and compatible torch/audio stack. |
| `vad_method="silero"` | Uses `torch.hub` to load Silero VAD. | May require network access or a prepopulated torch hub cache. |
| `vad_model=custom_model` | Custom model wins and `vad_method` is ignored. | The object must match WhisperX's expected VAD call/preprocess/merge contract. |
| `vad_options={...}` | Overrides `chunk_size`, `vad_onset`, `vad_offset`. | Bad thresholds can produce empty or overly fragmented speech chunks. |

Default VAD options are `chunk_size=30`, `vad_onset=0.500`, and `vad_offset=0.363`. `transcribe(..., chunk_size=...)` also passes a merge length for chunks; keep it positive.

## Batch size, chunks, and progress

- VAD first splits speech into merged segments, then WhisperX batches those segment waveforms.
- `batch_size` controls how many segment features are decoded together; reducing it is the first memory-reduction lever.
- `chunk_size` bounds merged VAD segment duration. Smaller chunks can reduce per-segment memory but may change segmentation and context.
- `progress_callback` is called per VAD segment with ASR-stage percentages. It will not fire if no speech segments are produced.
- `print_progress=True` prints progress messages to stdout; reserve it for scripts, not libraries.

## Language and task settings

When `language` is not preset at model load or transcribe time, WhisperX detects language from the first 30 seconds of audio. This is convenient but adds latency and can be inaccurate on very short audio.

Recommendations:

- Set `language="en"`, `"de"`, etc. when known.
- Model names ending in `.en` force English.
- Keep `task="transcribe"` unless the requested output is translation.
- If language or task changes between calls, WhisperX rebuilds the tokenizer.

## `suppress_numerals`

`asr_options={"suppress_numerals": True}` asks WhisperX to suppress tokenizer ids containing digits and selected symbols (`%`, `$`, `£`). It is useful for workflows that prefer words over numerals before alignment, but it can remove important content such as dates, IDs, currencies, percentages, and measurements.

Use it only when the downstream task explicitly wants numeral suppression. Leave it `False` for general transcription.

## Memory and process cleanup

For large models or multi-stage pipelines:

1. Reduce `batch_size`.
2. Use a smaller ASR model.
3. Consider `compute_type="int8"` where compatible.
4. Set `language` to avoid detection work.
5. Keep `num_workers=0` unless data loading is the bottleneck.
6. Delete ASR model objects and run garbage collection before loading alignment or diarization models in the same process.
7. On CUDA, call `torch.cuda.empty_cache()` after deleting large model objects.

These steps reduce resource pressure but do not guarantee a specific runtime or accuracy.
