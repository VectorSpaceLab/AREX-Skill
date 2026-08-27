---
name: transcription
description: "Use faster-whisper transcription APIs for ASR, batched inference,
  timestamps, VAD, language detection, audio decoding, and CPU or CUDA runtime
  choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# faster-whisper Transcription

Use this sub-skill when the task is to transcribe, translate, segment, timestamp,
or inspect audio with the `faster-whisper` Python package. It covers the public
`WhisperModel`, `BatchedInferencePipeline`, `decode_audio`, and VAD/timestamp
surfaces. Use the root skill for installation, backend setup, and model
management decisions that are not specific to one transcription call.

## Read first when

- The user mentions `WhisperModel`, `BatchedInferencePipeline`, `decode_audio`,
  VAD, word-level timestamps, hotwords, clip timestamps, language detection,
  translation, `compute_type`, or CPU/CUDA transcription.
- The user has an audio path, file-like object, or NumPy waveform and wants
  text segments, word timestamps, language probabilities, or batched throughput.
- The user reports confusing behavior such as an empty result because the
  segment generator was not consumed, CUDA compute-type errors, audio decode
  failures, VAD needing `onnxruntime`, or mismatched batched defaults.

## Route map

- Read [references/api-reference.md](references/api-reference.md) for verified
  signatures, return objects, option defaults, model aliases, and utility APIs.
- Read [references/workflows.md](references/workflows.md) for copyable recipes:
  standard transcription, batched transcription, VAD, word timestamps, hotwords,
  multilingual/translation, clip timestamps, stereo decoding, logging, and local
  model paths.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  symptoms, likely causes, and recovery steps for model downloads, generator
  consumption, audio/PyAV, VAD/ONNX, CUDA/cuDNN/compute types, language/task
  choices, batching defaults, and long-audio handling.
- Run or adapt [scripts/transcribe_audio.py](scripts/transcribe_audio.py) when a
  future task needs a bundled command-line transcription helper instead of a
  prose-only recipe. The helper is safe to inspect with `--help`; real
  transcription may download or load a model.
- For install and backend setup, read
  [../../references/installation-and-backends.md](../../references/installation-and-backends.md).
- For model aliases, download/cache behavior, local CTranslate2 model paths, and
  conversion recipes, read
  [../../references/model-management.md](../../references/model-management.md).

## Quick workflow

1. Choose a model source:
   - A public alias such as `tiny`, `base`, `small`, `medium`, `large-v3`,
     `turbo`, or `distil-large-v3`.
   - A Hugging Face repository id for a CTranslate2-converted Whisper model.
   - A local CTranslate2 model directory.
2. Choose runtime:
   - CPU: `device="cpu"`, usually `compute_type="int8"` or `"float32"`.
   - CUDA: `device="cuda"`, usually `compute_type="float16"`, `"int8_float16"`,
     or another CTranslate2-supported type when NVIDIA CUDA/cuDNN libraries are
     available.
   - `device="auto"` is convenient for exploratory code, but use an explicit
     device in reproducible instructions or when troubleshooting.
3. Instantiate `WhisperModel` for ordinary transcription or wrap it in
   `BatchedInferencePipeline` for chunked batched inference.
4. Call `transcribe(...)` and always consume the returned segment generator with
   `list(segments)` or a `for` loop. The actual transcription starts when the
   generator is iterated.
5. Validate `TranscriptionInfo` (`language`, `language_probability`, `duration`,
   `duration_after_vad`) and the segment fields (`start`, `end`, `text`,
   optional `words`).

Minimal API pattern:

```python
from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("audio.mp3", beam_size=5, language="en")
segments = list(segments)  # transcription runs here
print(info.language, info.language_probability)
for segment in segments:
    print(f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}")
```

## Important decisions

- Use `word_timestamps=True` when word-level timing is required; then inspect
  `segment.words` and validate monotonic times.
- Use `vad_filter=True` on `WhisperModel.transcribe` only when silence removal is
  desired; `BatchedInferencePipeline.transcribe` defaults to `vad_filter=True`.
- Use `without_timestamps=False` for timestamped output. `WhisperModel` defaults
  to timestamped behavior; `BatchedInferencePipeline` defaults to
  `without_timestamps=True`.
- Set `language` when known to avoid language-detection uncertainty; use
  `task="translate"` only when English translation is desired.
- Prefer `clip_timestamps` for explicit audio windows: `WhisperModel` accepts a
  comma-separated string such as `"0,30,45,60"`; batched transcription accepts a
  list of dictionaries like `[{"start": 0.0, "end": 30.0}]`.
- For stereo diarization-like workflows, call `decode_audio(path,
  split_stereo=True)`, transcribe left and right arrays separately, and keep the
  channel labels outside `faster-whisper`.

## Boundaries and omissions

This sub-skill does not cover heavy speed, memory, or WER benchmarking as a
runtime workflow. Those scripts require large model downloads, benchmark data,
GPU telemetry, or external datasets. Treat benchmark numbers as context, not as
required behavior for normal transcription tasks.
