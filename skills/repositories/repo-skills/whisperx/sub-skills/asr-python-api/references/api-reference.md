# ASR Python API reference

This reference distills the WhisperX `3.8.7rc1` Python API surface for ASR workflows. It is self-contained for runtime use and includes the signatures and schemas needed by future agents.

## Top-level lazy API

The package import name is `whisperx`. The public functions below are available at top level and lazy-import their implementation modules when called.

| Top-level function | Scope here | Notes |
| --- | --- | --- |
| `whisperx.load_model(*args, **kwargs)` | ASR model loading | Lazy wrapper for `whisperx.asr.load_model`; use the detailed signature below. |
| `whisperx.load_audio(*args, **kwargs)` | Audio decoding | Lazy wrapper for `whisperx.audio.load_audio`; requires the `ffmpeg` executable for file paths. |
| `whisperx.load_align_model(*args, **kwargs)` | Route elsewhere | Alignment model loading; use the alignment sub-skill. |
| `whisperx.align(*args, **kwargs)` | Route elsewhere | Forced alignment; use the alignment sub-skill. |
| `whisperx.assign_word_speakers(*args, **kwargs)` | Route elsewhere | Speaker assignment; use the diarization sub-skill. |
| `whisperx.setup_logging(*args, **kwargs)` / `whisperx.get_logger(*args, **kwargs)` | Support | Optional logging helpers. |

## `whisperx.asr.load_model`

Verified signature:

```python
load_model(
    whisper_arch: str,
    device: str,
    device_index=0,
    compute_type="default",
    asr_options: dict | None = None,
    language: str | None = None,
    vad_model=None,
    vad_method: str | None = "pyannote",
    vad_options: dict | None = None,
    model=None,
    task="transcribe",
    download_root: str | None = None,
    local_files_only=False,
    threads=4,
    use_auth_token: str | bool | None = None,
) -> FasterWhisperPipeline
```

| Argument | Runtime meaning | Practical guidance |
| --- | --- | --- |
| `whisper_arch` | Whisper/faster-whisper model identifier or compatible local model location. | Examples include model sizes such as `small`, `base`, `large-v2`, or a compatible cached/local model. A real load can touch the model cache or network. |
| `device` | Backend string passed into the Faster Whisper/CTranslate2 model and VAD setup. | Common values are `"cuda"` and `"cpu"`. Prefer `"cpu"` when CUDA is unavailable or unverified. |
| `device_index` | Device index for CUDA-style device selection. | Default `0`. With the default Pyannote VAD on CUDA, it is used to build a VAD device such as CUDA device zero. |
| `compute_type` | CTranslate2 compute type. | `"default"` becomes `"float16"` on `device == "cuda"` and `"float32"` otherwise. Use explicit `"int8"` or another supported CTranslate2 type for memory reduction after checking compatibility. |
| `asr_options` | Overrides for the default `TranscriptionOptions` plus WhisperX's `suppress_numerals` switch. | Use for beam/search settings, prompts, hotwords, and `suppress_numerals`. Unsupported keys raise through `TranscriptionOptions`. |
| `language` | Preset language code for tokenizer construction. | Set it when known to avoid per-audio language detection overhead. Model names ending in `.en` force `language="en"`. |
| `vad_model` | Manually supplied VAD object. | Has higher priority than `vad_method`; it should implement the VAD contract used by the pipeline. |
| `vad_method` | Built-in VAD backend selector. | `"pyannote"` is the default. `"silero"` uses `torch.hub` and may need network/cache availability. Any other value raises `ValueError`. |
| `vad_options` | VAD chunk/threshold overrides. | Defaults are `chunk_size=30`, `vad_onset=0.500`, `vad_offset=0.363`. |
| `model` | Preconstructed `WhisperModel`. | Advanced use to inject an already-created compatible model and avoid constructing one inside `load_model`. |
| `task` | Tokenizer task. | Usually `"transcribe"`; use `"translate"` only when the downstream workflow expects translation. |
| `download_root` | Model cache/download root. | Set to a project-controlled cache directory when reproducibility or offline use matters. |
| `local_files_only` | Cache-only loading switch. | `True` prevents downloads and fails if required files are absent. Pair with `download_root` and a populated cache. |
| `threads` | CPU threads per worker passed to Faster Whisper. | Matters most on CPU; increasing it can compete with `num_workers` and other jobs. |
| `use_auth_token` | Optional token forwarded for model retrieval. | Only use when a model requires credentials; do not print or store tokens in generated artifacts. |

### Default ASR options worth knowing

`load_model` creates default Faster Whisper transcription options and then applies `asr_options`. Common defaults include:

| Option | Default | Notes |
| --- | ---: | --- |
| `beam_size` | `5` | Beam search size. Lower values can be faster but may reduce quality. |
| `best_of` | `5` | Sampling candidate count for non-zero temperatures. |
| `temperatures` | `[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]` | Fallback schedule used by Faster Whisper options. |
| `condition_on_previous_text` | `False` | Reduces hallucination risk but differs from OpenAI Whisper defaults. |
| `without_timestamps` | `True` | Required by WhisperX's batched ASR path; use alignment later for word timestamps. |
| `word_timestamps` | `False` | Word timestamps are not produced by this ASR pass. |
| `suppress_blank` | `True` | Passed into generation. |
| `suppress_tokens` | `[-1]` | Can be extended when `suppress_numerals` is enabled. |
| `initial_prompt`, `prefix`, `hotwords` | `None` | Optional prompt/search controls supported by Faster Whisper options. |
| `suppress_numerals` | `False` | WhisperX-specific option consumed before building `TranscriptionOptions`; see below. |

## `FasterWhisperPipeline.transcribe`

Verified signature:

```python
FasterWhisperPipeline.transcribe(
    self,
    audio: str | numpy.ndarray,
    batch_size: int | None = None,
    num_workers=0,
    language: str | None = None,
    task: str | None = None,
    chunk_size=30,
    print_progress=False,
    combined_progress=False,
    verbose=False,
    progress_callback=None,
) -> TranscriptionResult
```

| Argument | Runtime meaning | Practical guidance |
| --- | --- | --- |
| `audio` | Audio path string or mono waveform NumPy array. | Path strings call `load_audio`. Arrays must already be 16 kHz mono floating-point audio in the expected range. |
| `batch_size` | ASR feature batch size for VAD chunks. | Overrides the batch size stored at model construction. Reduce for low GPU memory. |
| `num_workers` | DataLoader worker count for feature batches. | Default `0` is safest. Higher values can increase CPU/memory pressure. |
| `language` | Per-call language override. | Avoids detection if set or if the model was loaded with a tokenizer language. |
| `task` | Per-call tokenizer task override. | Usually leave as `None` or `"transcribe"`. Changing task/language rebuilds the tokenizer. |
| `chunk_size` | Maximum merged VAD chunk length in seconds. | Default `30`, matching model input chunk length. Lower values can reduce memory per segment but may alter segmentation. |
| `print_progress` | Print text progress to stdout. | Useful in scripts; for applications prefer `progress_callback`. |
| `combined_progress` | Halve printed progress for multi-stage CLI-like workflows. | Affects printed percentage only; callback receives ASR-stage percent. |
| `verbose` | Print each segment transcript with timestamps. | Avoid in libraries when logs must be structured or privacy-sensitive. |
| `progress_callback` | Callable receiving a float percentage. | Called once per produced VAD segment with values scaled from 0 to 100. |

Transcription flow:

1. Path input is decoded with `load_audio`.
2. The configured VAD backend creates speech regions and merges them into chunks.
3. If no tokenizer language was preset, language detection runs on the first 30 seconds before decoding.
4. Each VAD chunk is converted to a log-Mel spectrogram and decoded through batched Faster Whisper generation.
5. Return shape is a `TranscriptionResult` dictionary.

## `WhisperModel.generate_segment_batched`

Verified signature:

```python
WhisperModel.generate_segment_batched(
    self,
    features: numpy.ndarray,
    tokenizer,
    options,
    encoder_output=None,
)
```

This is the lower-level batched generation method used by `FasterWhisperPipeline`. It encodes a batch of log-Mel features, builds one prompt shared by the batch, calls the CTranslate2 model, and returns a dictionary shaped like:

```python
{"text": ["...", "..."], "avg_logprob": [float, float]}
```

It is mainly useful for advanced testing or custom pipelines. It does not produce word timestamps; use the alignment workflow after ASR if word-level timings are needed.

## `find_numeral_symbol_tokens`

```python
find_numeral_symbol_tokens(tokenizer) -> list[int]
```

This helper decodes tokenizer ids below end-of-transcript and returns token ids containing digits or the symbols `%`, `$`, or `£`. `FasterWhisperPipeline.transcribe` uses it when `suppress_numerals=True` was set through `asr_options`; the pipeline temporarily extends `suppress_tokens` for the call and then restores the previous options.

## Audio helpers and constants

Verified signatures:

```python
load_audio(file: str, sr: int = 16000) -> numpy.ndarray
log_mel_spectrogram(audio: str | numpy.ndarray | torch.Tensor, n_mels: int, padding: int = 0, device=None)
```

| Name | Value / behavior |
| --- | --- |
| `SAMPLE_RATE` | `16000` samples/second. |
| `N_FFT` | `400`. |
| `HOP_LENGTH` | `160`. |
| `CHUNK_LENGTH` | `30` seconds. |
| `N_SAMPLES` | `480000`, a 30-second waveform chunk at 16 kHz. |
| `N_FRAMES` | `3000`, frames per 30-second log-Mel input. |
| `FRAMES_PER_SECOND` | `100`. |
| `TOKENS_PER_SECOND` | `50`. |

`load_audio` invokes the `ffmpeg` executable to decode, down-mix to mono, resample to 16 kHz by default, and return `float32` samples normalized from signed 16-bit PCM.

`log_mel_spectrogram` accepts a path, NumPy array, or torch tensor, optionally pads on the right, computes STFT with WhisperX constants, applies bundled mel filters for 80 or 128 mel bins, and returns a torch tensor. When a path is supplied, it calls `load_audio` first.

## `TranscriptionResult` schema

The ASR result is a typed dictionary:

```python
TranscriptionResult = {
    "segments": list[SingleSegment],
    "language": str,
}

SingleSegment = {
    "start": float,
    "end": float,
    "text": str,
    "avg_logprob": float,  # may be omitted by some downstream transforms
}
```

ASR segments contain segment-level start/end times from VAD chunking, text, and average log probability. They do not contain word timings or speakers until separate alignment and diarization workflows add them.
