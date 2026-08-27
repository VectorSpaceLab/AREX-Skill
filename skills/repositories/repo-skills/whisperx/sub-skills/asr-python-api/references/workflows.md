# ASR Python API workflows

These recipes are written for runtime agents that need WhisperX through Python. They avoid full-run promises: any call to `load_model` can require model files, a compatible backend, and cache/network decisions made by the user or surrounding task.

## Safe environment and API inspection

From this sub-skill directory, run:

```bash
python scripts/inspect_whisperx_api.py
python scripts/inspect_whisperx_api.py --json
```

This imports WhisperX modules, reports signatures, and checks torch CUDA availability. It does not load a Whisper model, download weights, transcribe audio, or require credentials.

For file-audio decoding only:

```bash
python scripts/check_audio_loading.py
```

This creates a tiny temporary WAV with the Python standard library and calls `whisperx.load_audio`; it is a quick way to distinguish Python import problems from missing `ffmpeg`.

## Basic ASR pattern with path audio

Use this shape when the task has a real audio file and model-cache policy has already been decided.

```python
import torch
import whisperx

# Choose backend explicitly; do not assume CUDA exists.
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "float32"

# Cache-only mode is safest for reproducible/offline runs, but it fails if files are absent.
model = whisperx.load_model(
    "small",
    device=device,
    compute_type=compute_type,
    language="en",              # set when known to avoid language detection overhead
    download_root="model-cache", # relative cache location chosen by the caller
    local_files_only=True,       # change only with explicit permission to download
)

audio = whisperx.load_audio("input.wav")  # requires ffmpeg for file paths
progress = []

result = model.transcribe(
    audio,
    batch_size=4,
    language="en",
    progress_callback=progress.append,
)

for segment in result["segments"]:
    print(segment["start"], segment["end"], segment["text"])
print("language:", result["language"])
print("progress events:", progress)
```

Expected output shape is the `TranscriptionResult` dictionary documented in `api-reference.md`. Actual transcript quality, speed, and success depend on model files, ffmpeg, device support, and audio content.

## Cached NumPy-array transcription recipe

Use this when audio was decoded elsewhere or cached as an array. This bypasses `ffmpeg` during `transcribe`, but the array must already match WhisperX expectations: mono, 16 kHz, one-dimensional, `float32` or convertible floating point.

```python
import numpy as np
import torch
import whisperx

# Example: `cached_audio` is supplied by the caller or loaded from an application cache.
cached_audio = get_cached_audio_array()  # must represent 16 kHz mono audio

audio = np.asarray(cached_audio, dtype=np.float32)
if audio.ndim != 1:
    raise ValueError("WhisperX ASR expects a one-dimensional mono waveform")

# Keep cache-only true for reproducible offline jobs; prepopulate the cache first.
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisperx.load_model(
    "small",
    device=device,
    compute_type="float16" if device == "cuda" else "float32",
    language="en",
    download_root="model-cache",
    local_files_only=True,
)

def on_progress(percent: float) -> None:
    # Called once per VAD chunk; values are ASR-stage percentages from 0 to 100.
    print(f"ASR progress: {percent:.1f}%")

result = model.transcribe(
    audio,
    batch_size=2,
    num_workers=0,
    language="en",
    chunk_size=30,
    progress_callback=on_progress,
)

segments = result["segments"]
```

If the cached array uses another sample rate, resample it before calling WhisperX. Passing a NumPy array does **not** make WhisperX infer sample rate metadata.

## Loading with deliberate download allowed

Only use a network-enabled load when the task explicitly permits model downloads and the target environment has enough disk space. Keep the cache location caller-controlled and avoid logging credentials.

```python
import whisperx

model = whisperx.load_model(
    "small",
    device="cpu",
    compute_type="int8",
    language="en",
    download_root="model-cache",
    local_files_only=False,  # explicitly allows cache miss downloads
)
```

For gated/private model sources, pass `use_auth_token` from a secure secret source and never hard-code it in reusable skill content.

## Progress callbacks

`progress_callback` receives a single float percentage per decoded VAD segment. It is independent of stdout printing.

```python
events = []

def collect_progress(percent: float) -> None:
    events.append(round(percent, 2))

result = model.transcribe(audio, batch_size=4, progress_callback=collect_progress)
```

Use `print_progress=True` only for command-line-style scripts. `combined_progress=True` halves printed ASR percentages for multi-stage workflows that reserve later progress for alignment; the callback still receives ASR-stage percentages.

## Memory-conscious ASR recipe

When GPU memory is limited, or when CPU-only operation is required, reduce the amount of work per forward pass before changing task semantics.

```python
import gc
import torch
import whisperx

device = "cuda" if torch.cuda.is_available() else "cpu"

model = whisperx.load_model(
    "base",                         # smaller model than large variants
    device=device,
    compute_type="int8" if device == "cpu" else "float16",
    language="en",                  # avoids language detection pass
    download_root="model-cache",
    local_files_only=True,
)

result = model.transcribe(
    audio,
    batch_size=1,                    # reduce further first when memory fails
    num_workers=0,
    language="en",
    chunk_size=15,                   # optional; smaller VAD chunks can reduce peak memory
)

# Release ASR model before alignment/diarization if the surrounding workflow loads more models.
del model
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

Trade-offs:

- Smaller `batch_size` lowers peak memory but can be slower.
- Smaller ASR models and `int8` compute can lower memory but may reduce accuracy.
- CPU runs are usually much slower than CUDA runs; choose smaller models and explicit language codes for CPU jobs.
- Deleting the ASR model is useful before loading alignment or diarization models in the same process.

## Suppressing numerals and symbols

Use only when the downstream transcript should avoid numeric/currency tokens. This can remove useful numbers such as dates, IDs, percentages, and prices.

```python
model = whisperx.load_model(
    "small",
    device="cpu",
    compute_type="int8",
    language="en",
    asr_options={"suppress_numerals": True},
    download_root="model-cache",
    local_files_only=True,
)
```

Internally, WhisperX finds tokenizer tokens containing digits or `%`, `$`, `£`, temporarily adds them to the suppression list for transcription, and restores the prior options afterward.

## Hand off to other WhisperX workflows

After this sub-skill produces `result = {"segments": ..., "language": ...}`:

- For word/character timestamps, pass `result["segments"]`, `result["language"]`, and the same audio to the alignment sub-skill.
- For speaker labels, pass ASR or aligned results to the diarization sub-skill.
- For subtitle or JSON/TXT/TSV/Audacity files, pass the result dictionary to the outputs sub-skill.
