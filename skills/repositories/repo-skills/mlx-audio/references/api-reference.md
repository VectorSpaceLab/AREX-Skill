# API Reference

This reference collects the stable package facts verified during skill generation.

## Registry

- `mlx_audio.registry.kinds()` returns: `('tts', 'stt', 'sts', 'codec', 'lid', 'lm', 'vad')`
- `mlx_audio.registry.SUPPORTED_MODEL_TYPES` maps model families to their supported implementation names.

## Shared Utilities

- `mlx_audio.utils.load_model(...)` loads a model by path or Hub id.
- `mlx_audio.utils.load_config(...)` reads a `config.json` dictionary from a model directory.
- `mlx_audio.utils.load_weights(...)` reads weights from a model directory.
- `mlx_audio.utils.base_load_model(...)` handles category lookup, remapping, and optional lazy/strict loading.
- `mlx_audio.utils.audio_volume_normalize(...)`, `trim_silence(...)`, `random_select_audio_segment(...)`, and `resample_audio(...)` are the main shared audio helpers.

## Audio I/O

- `mlx_audio.audio_io.read(file, always_2d=False, dtype='float64', sample_rate=None, nchannels=None) -> (array, sample_rate)`
- `mlx_audio.audio_io.write(file, data, samplerate, format=None) -> None`

The reader can resample and downmix. The writer supports common audio containers and uses ffmpeg-backed paths when needed.

## TTS

- `mlx_audio.tts.utils.load_model(model_path, lazy=False, strict=True, **kwargs)`
- `mlx_audio.tts.generate.generate_audio(...)` accepts text, voice, prompt/instruct controls, reference audio/text, streaming flags, save/join options, and model-specific kwargs.

## STT

- `mlx_audio.stt.utils.load_model(model_path, lazy=False, strict=False, **kwargs)`
- `mlx_audio.stt.generate.parse_args(argv=None)` parses the CLI flags.
- `mlx_audio.stt.generate.generate_transcription(model=None, audio=None, output_path='transcript', format='txt', verbose=False, text='', **kwargs)`
- `mlx_audio.stt.utils.wired_limit(...)` applies the model-specific stream limit used by some backends.

## Realtime VAD

- `mlx_audio.realtime_vad.parse_turn_detection(turn_detection)` returns `ServerVadConfig` or `None`.
- `ServerVadConfig` defaults match OpenAI-style `server_vad` behavior: threshold `0.5`, prefix padding `300`, silence duration `500`.
- `StreamingVad` and `TurnDetector` implement the server-side turn-detection state machine.

## Server Request Models

- `mlx_audio.server.SpeechRequest` includes `model`, `input`, `voice`, `speed`, `lang_code`, `ref_audio`, `ref_text`, `temperature`, `top_p`, `top_k`, `response_format`, `stream`, `streaming_interval`, `max_tokens`, and `verbose`.
- `mlx_audio.server.TranscriptionRequest` includes `model`, `language`, `verbose`, `max_tokens`, `chunk_duration`, `frame_threshold`, `stream`, `context`, `prefill_step_size`, `text`, `word_timestamps`, and `timestamp_granularities`.

## Evaluation

- `mlx_audio.stt.eval.wer.compute_wer(reference, hypothesis)` computes edit counts and WER.
- `mlx_audio.stt.eval.wer.aggregate_wer(results)` computes micro/macro summaries.
