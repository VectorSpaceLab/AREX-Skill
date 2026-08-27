# Transcription API Reference

## Purpose

Read this when a task needs exact `faster-whisper` public APIs, option defaults,
return objects, and behavior differences between ordinary and batched
transcription. The facts here were verified against package version 1.2.1.

## Public imports

```python
from faster_whisper import (
    WhisperModel,
    BatchedInferencePipeline,
    available_models,
    decode_audio,
    download_model,
    format_timestamp,
)
```

The public package exports these names: `available_models`, `decode_audio`,
`WhisperModel`, `BatchedInferencePipeline`, `download_model`,
`format_timestamp`, and `__version__`.

## Model construction

Verified constructor shape:

```python
WhisperModel(
    model_size_or_path: str,
    device: str = "auto",
    device_index: int | list[int] = 0,
    compute_type: str = "default",
    cpu_threads: int = 0,
    num_workers: int = 1,
    download_root: str | None = None,
    local_files_only: bool = False,
    files: dict | None = None,
    revision: str | None = None,
    use_auth_token: str | bool | None = None,
    **model_kwargs,
)
```

Key construction decisions:

- `model_size_or_path` accepts a built-in alias, a Hugging Face repository id for
  a CTranslate2-converted Whisper model, or a local CTranslate2 model directory.
- `device="cpu"` is the most portable path. `device="cuda"` requires compatible
  NVIDIA CUDA/cuDNN runtime libraries and a CTranslate2 build that supports CUDA.
- `compute_type` is passed to CTranslate2. Common choices are `int8` or
  `float32` on CPU and `float16`, `int8_float16`, or `int8` on CUDA. Use the
  root install/backend reference before promising GPU execution.
- `device_index` may be a list of GPU ids. With multiple GPU ids, concurrent
  calls from multiple Python threads can use multiple model workers.
- `cpu_threads` overrides CPU thread count when non-zero. For controlled CPU
  comparisons, also consider setting `OMP_NUM_THREADS` outside Python.
- `num_workers` enables concurrent `generate()` execution when multiple threads
  call `transcribe`; this increases memory use.
- `download_root`, `local_files_only`, `revision`, and `use_auth_token` control
  Hugging Face model resolution. Use a local path or `local_files_only=True` for
  offline runs.

## `WhisperModel.transcribe`

Verified signature:

```python
WhisperModel.transcribe(
    audio,
    language: str | None = None,
    task: str = "transcribe",
    log_progress: bool = False,
    beam_size: int = 5,
    best_of: int = 5,
    patience: float = 1,
    length_penalty: float = 1,
    repetition_penalty: float = 1,
    no_repeat_ngram_size: int = 0,
    temperature = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    compression_ratio_threshold: float | None = 2.4,
    log_prob_threshold: float | None = -1.0,
    no_speech_threshold: float | None = 0.6,
    condition_on_previous_text: bool = True,
    prompt_reset_on_temperature: float = 0.5,
    initial_prompt: str | Iterable[int] | None = None,
    prefix: str | None = None,
    suppress_blank: bool = True,
    suppress_tokens: list[int] | None = [-1],
    without_timestamps: bool = False,
    max_initial_timestamp: float = 1.0,
    word_timestamps: bool = False,
    prepend_punctuations: str = "\"'“¿([{-",
    append_punctuations: str = "\"'.。,，!！?？:：”)]}、",
    multilingual: bool = False,
    vad_filter: bool = False,
    vad_parameters: dict | VadOptions | None = None,
    max_new_tokens: int | None = None,
    chunk_length: int | None = None,
    clip_timestamps: str | list[float] = "0",
    hallucination_silence_threshold: float | None = None,
    hotwords: str | None = None,
    language_detection_threshold: float | None = 0.5,
    language_detection_segments: int = 1,
) -> tuple[Iterable[Segment], TranscriptionInfo]
```

Important behavior:

- `audio` may be a path, file-like object, or a 1-D NumPy waveform sampled at the
  model feature extractor rate. Non-array audio is decoded with `decode_audio`.
- The first return value is an iterable/generator of `Segment` objects. The
  transcription starts when this iterable is consumed.
- If `language` is omitted and the model is multilingual, language detection is
  run on one or more feature windows. Set `language="en"` or another language
  code when known.
- `task` is `"transcribe"` or `"translate"`. `translate` produces English
  translation for supported Whisper models.
- `temperature` can be a scalar or a sequence. For `WhisperModel`, fallback
  decoding can try later temperatures when thresholds are not met.
- `vad_filter` defaults to `False` for `WhisperModel`; enable it explicitly for
  silence removal.
- `clip_timestamps` for `WhisperModel` is normally a comma-separated string of
  start/end seconds, for example `"0,30,45,60"`; the final end can default to
  the end of the file.
- `without_timestamps=False` means timestamp tokens are enabled by default.
- `word_timestamps=True` runs word alignment and fills `segment.words` with
  `Word` objects.

## `BatchedInferencePipeline`

Construction:

```python
batched_model = BatchedInferencePipeline(model=WhisperModel("tiny"))
```

Verified `BatchedInferencePipeline.transcribe` has the same major arguments as
`WhisperModel.transcribe`, plus:

```python
batch_size: int = 8
clip_timestamps: list[dict] | None = None
```

Default differences to remember:

| Option | `WhisperModel.transcribe` | `BatchedInferencePipeline.transcribe` |
| --- | --- | --- |
| `vad_filter` | `False` | `True` |
| `without_timestamps` | `False` | `True` |
| `clip_timestamps` | comma-separated string/list-like seconds | list of dictionaries with `start` and `end` |
| `batch_size` | not present | `8` by default |

Batched transcription is useful for throughput on chunked audio, especially on
GPU. It is not a separate model class; it wraps a `WhisperModel` instance.

## Return dataclasses

`Segment` fields:

```text
id, seek, start, end, text, tokens, avg_logprob, compression_ratio,
no_speech_prob, words, temperature
```

`Word` fields:

```text
start, end, word, probability
```

`TranscriptionInfo` fields:

```text
language, language_probability, duration, duration_after_vad,
all_language_probs, transcription_options, vad_options
```

Both `Segment` and `Word` still expose deprecated `_asdict()` methods, but new
code should prefer dataclass access or `dataclasses.asdict`.

## Audio utilities

```python
decode_audio(input_file, sampling_rate=16000, split_stereo=False)
```

- Uses PyAV, whose wheel bundles FFmpeg libraries, so a system `ffmpeg` binary is
  not required for normal package use.
- Returns a `float32` NumPy array normalized to `[-1, 1]` style audio values.
- With `split_stereo=True`, returns `(left_channel, right_channel)`. Transcribe
  each channel separately for simple stereo speaker separation.

```python
format_timestamp(seconds, always_include_hours=False, decimal_marker=".")
```

Formats non-negative seconds as `MM:SS.mmm` or `HH:MM:SS.mmm`.

## VAD API

```python
from faster_whisper.vad import VadOptions, get_speech_timestamps, collect_chunks
```

`VadOptions` defaults:

```text
threshold=0.5
neg_threshold=None
min_speech_duration_ms=0
max_speech_duration_s=inf
min_silence_duration_ms=2000
speech_pad_ms=400
min_silence_at_max_speech=98
use_max_poss_sil_at_max_speech=True
```

The VAD path uses a bundled Silero ONNX model and `onnxruntime` CPU execution.
For long speech segments, `max_speech_duration_s`, `min_silence_duration_ms`,
and `speech_pad_ms` are the usual tuning knobs.

## Model utilities

`available_models()` returned 19 aliases in the verified package, including:

```text
tiny.en, tiny, base.en, base, small.en, small, medium.en, medium,
large-v1, large-v2, large-v3, large, distil-large-v2,
distil-medium.en, distil-small.en, distil-large-v3,
distil-large-v3.5, large-v3-turbo, turbo
```

`download_model(size_or_id, output_dir=None, local_files_only=False,
cache_dir=None, revision=None, use_auth_token=None)` downloads or resolves a
CTranslate2 Whisper model snapshot with the files needed by `WhisperModel`.
Use the root model-management reference for cache, offline, and conversion
recipes.
