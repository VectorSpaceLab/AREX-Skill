# Transcription Troubleshooting

## Purpose

Use this reference when a `faster-whisper` transcription call imports correctly
but fails, returns unexpected output, or behaves differently across ordinary,
batched, CPU, and CUDA execution.

## Nothing happens or output is empty

Symptoms:

- `segments, info = model.transcribe(...)` returns quickly and no text appears.
- Timing or GPU use starts only later.

Likely cause: `segments` is a generator. The transcription work starts when the
generator is consumed.

Fix:

```python
segments, info = model.transcribe("audio.mp3")
segments = list(segments)
```

For streaming-style code, iterate once with a `for` loop and do not expect to
reuse the same generator afterward.

## Model download, cache, or offline errors

Symptoms:

- Hugging Face download errors, network timeouts, authorization failures, or
  `local_files_only` errors.
- A model alias works on one machine but not offline on another.

Likely causes:

- The model alias or repository id has not been cached locally.
- Network access or Hugging Face credentials are unavailable.
- A converted CTranslate2 model directory is missing required files such as
  `model.bin`, `config.json`, `tokenizer.json`, or `preprocessor_config.json`.

Fixes:

- Use a local converted model directory for offline jobs.
- Use `download_root` or `cache_dir` intentionally rather than relying on an
  unknown default cache.
- Set `local_files_only=True` only when the files are already present.
- Use root [model management](../../../references/model-management.md) guidance to
  pre-download or convert models.

## Audio decode or PyAV failures

Symptoms:

- Errors from `av.open`, invalid audio stream, unsupported container, or empty
  decoded arrays.
- Stereo input produces unexpected mixed transcript.

Likely causes:

- The input file is corrupt, has no decodable audio stream, or is a rare codec
  not handled by the installed PyAV wheel.
- The task needs channel-specific transcription but `split_stereo=True` was not
  used.

Fixes:

- First verify `decode_audio(path)` returns a non-empty `float32` array.
- Use `decode_audio(path, split_stereo=True)` for independent left/right channel
  transcription.
- Convert unusual audio to a common WAV/FLAC/MP3 container outside
  `faster-whisper` if PyAV cannot read it.

## VAD or ONNX runtime errors

Symptoms:

- `RuntimeError: Applying the VAD filter requires the onnxruntime package`.
- VAD removes too much speech or keeps too much silence.
- Batched transcription unexpectedly changes segment boundaries.

Likely causes:

- `onnxruntime` is missing or broken.
- VAD defaults differ: ordinary `WhisperModel.transcribe` has `vad_filter=False`,
  while `BatchedInferencePipeline.transcribe` has `vad_filter=True`.
- `min_silence_duration_ms`, `speech_pad_ms`, or threshold values are not suited
  to the audio.

Fixes:

- Install/repair the base package dependencies so `onnxruntime` imports.
- Set `vad_filter=False` explicitly when comparing batched and non-batched
  behavior.
- Tune `vad_parameters`, for example
  `dict(min_silence_duration_ms=500, speech_pad_ms=200)`.
- Enable `faster_whisper` debug logging to inspect VAD-kept chunks.

## CUDA, cuDNN, and compute type failures

Symptoms:

- CUDA device initialization errors.
- Missing cuBLAS/cuDNN library messages.
- `compute_type` is not supported on the selected device.
- CUDA works for another framework but not for CTranslate2.

Likely causes:

- NVIDIA CUDA/cuBLAS/cuDNN runtime libraries required by CTranslate2 are not on
  the runtime library path.
- Installed CTranslate2 wheel does not support the host's CUDA/runtime stack.
- A GPU-only compute type such as `float16` was requested on CPU, or an overly
  slow/unsupported type was selected.

Fixes:

- Read root [installation and backend](../../../references/installation-and-backends.md)
  guidance before changing packages.
- For CPU fallback, use `device="cpu"` with `compute_type="int8"` or
  `"float32"`.
- For CUDA, try `compute_type="float16"`, `"int8_float16"`, or CTranslate2's
  reported supported CUDA compute types.
- Keep GPU troubleshooting separate from model quality: first prove that a tiny
  model loads and one short audio clip transcribes.
- Do not claim full CUDA verification from a CPU import check alone.

## Language or task mismatch

Symptoms:

- English-only model warns about non-English language selection.
- Translation output is expected but transcription appears in the source
  language.
- Language detection probabilities are low or inconsistent.

Likely causes:

- `task` defaulted to `"transcribe"`; translation requires `task="translate"`.
- An English-only `.en` model was used for multilingual audio.
- The first detection window is silent or not representative.

Fixes:

- Choose a multilingual model alias for multilingual input.
- Set `language` explicitly when known.
- Use `task="translate"` only when English translation is desired.
- Enable VAD or set clip timestamps so detection uses speech-heavy regions.

## Clip timestamp format errors

Symptoms:

- Type errors around clip timestamps.
- Batched pipeline ignores or mishandles string clip timestamp values.

Likely cause: `WhisperModel` and `BatchedInferencePipeline` expect different
clip timestamp shapes.

Fix:

- `WhisperModel`: use a comma-separated string such as `"0,30,45,90"`.
- `BatchedInferencePipeline`: use a list of dicts such as
  `[{"start": 0.0, "end": 30.0}]`.

## Batching changes text or timestamps

Symptoms:

- Batched output is similar but punctuation, spaces, timestamp boundaries, or
  segment counts differ from non-batched output.

Likely causes:

- `BatchedInferencePipeline` uses batched chunking and VAD defaults.
- `without_timestamps` defaults to `True` in batched mode.
- Larger `batch_size` changes throughput and memory pressure, not the model
  checkpoint.

Fixes:

- Set shared options explicitly in both calls: `language`, `vad_filter`,
  `without_timestamps`, `word_timestamps`, `beam_size`, and `temperature`.
- Reduce `batch_size` if memory pressure causes failures.
- Compare normalized transcript text before treating punctuation differences as
  model failures.

## Long audio and repeated text

Symptoms:

- Repetitions, hallucinated text after silence, drifting timestamps, or very long
  segments.

Likely causes:

- Previous-window conditioning carries bad context.
- Silence or non-speech segments are not filtered.
- Chunking settings are not suited to the audio.

Fixes:

- Try `condition_on_previous_text=False`.
- Enable or tune VAD.
- Use `clip_timestamps` for known regions.
- Set `hallucination_silence_threshold` when word timestamps are enabled and
  long silent periods correlate with hallucinations.
- Validate generated segments with start/end monotonicity and spot-check text
  against the audio.
