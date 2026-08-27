# STT API Reference

## Verified Entry Points

- `mlx_audio.stt.utils.load_model(model_path, lazy=False, strict=False, **kwargs)`
- `mlx_audio.stt.generate.parse_args(argv=None)`
- `mlx_audio.stt.generate.generate_transcription(model=None, audio=None, output_path='transcript', format='txt', verbose=False, text='', **kwargs)`
- `mlx_audio.stt.utils.merge_hotwords(base, hotwords)`
- `mlx_audio.stt.utils.wired_limit(...)`

## Common Input Fields

- `model`: Hub id or local model path
- `audio`: input file or waveform
- `output_path`: output root without extension
- `format`: `txt`, `srt`, `vtt`, or `json`
- `stream`: stream partial results
- `context`: hotwords or metadata for supported models
- `text`: transcript for forced alignment flows
- `gen_kwargs`: JSON-encoded model-specific generation kwargs

## Important Behavior

- `--format` determines both serialization and file extension.
- `--stream` enables incremental transcription when the backend supports it.
- `--text` is for alignment-style workflows, not ordinary ASR.
- `--context` is the shared route for hotwords or prompt context in models that accept it.
- `--gen-kwargs` is parsed as JSON before being forwarded to the model.

## Evaluation Facts

- `mlx_audio.stt.eval.wer.compute_wer(...)` computes WER for a single pair or token sequence.
- `mlx_audio.stt.eval.wer.aggregate_wer(...)` aggregates micro/macro summaries.
- `mlx_audio.stt.eval.cli.parse_args(...)` supports dataset-repo, revision, output-dir, metrics, language, and model-specific generation kwargs.
