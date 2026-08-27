# CLI Reference

## Console Entry Points

| Command | Purpose |
|---|---|
| `mlx_audio.tts.generate` | text-to-speech generation, streaming, cloning, and save/join workflows |
| `mlx_audio.stt.generate` | speech-to-text transcription, streaming, alignment, and output formatting |
| `mlx_audio.sts.generate` | speech enhancement / separation workflows |
| `mlx_audio.server` | FastAPI/OpenAI-compatible server and Studio UI launcher |
| `mlx_audio.convert` | model conversion and quantization |
| `python -m mlx_audio.stt.eval` | STT evaluation and WER summaries |

## Common TTS Flags

- `--model`, `--text`, `--voice`, `--lang_code`
- `--ref_audio`, `--ref_text`, `--stt_model`
- `--stream`, `--streaming_interval`, `--play`, `--save`
- `--output_path`, `--file_prefix`, `--audio_format`, `--join_audio`

Important behavior:

- `--stream` implies playback.
- `--save` is only valid with `--stream`.
- `--join_audio` controls whether multi-segment output is written as one file or numbered chunks.

## Common STT Flags

- `--model`, `--audio`, `--output-path`, `--format`
- `--stream`, `--context`, `--text`, `--gen-kwargs`
- `--language`, `--max-tokens`, `--max-parallel-segments`
- `--chunk-duration`, `--frame-threshold`, `--prefill-step-size`

## Common Server Flags

- `--host`, `--port`, `--reload`, `--start-ui`
- `--allowed-origins`, `--log-dir`
- `--realtime-model`, `--realtime-transcription-delay-ms`, `--vad-model`, `--tts-max-batch-size`

## Common Conversion Flags

- `--hf-path`, `--mlx-path`
- `--quantize`, `--q-bits`, `--q-group-size`, `--q-mode`
- `--dtype`, `--upload-repo`

## Safe Checks

- Use `--help` on each CLI before starting a long job.
- Use `scripts/check_install.py --check-cli` for a fast smoke check of the command surface.
