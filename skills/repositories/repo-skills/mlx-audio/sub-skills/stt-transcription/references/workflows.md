# STT Workflows

## Basic Transcription

```bash
python -m mlx_audio.stt.generate \
  --model mlx-community/whisper-large-v3-turbo-asr-fp16 \
  --audio speech.wav \
  --output-path transcript \
  --format json \
  --verbose
```

## Streaming Transcription

```bash
python -m mlx_audio.stt.generate \
  --model mlx-community/parakeet-tdt-0.6b-v3 \
  --audio long_audio.wav \
  --output-path transcript \
  --format txt \
  --stream
```

## Hotwords or Context

```bash
python -m mlx_audio.stt.generate \
  --model mlx-community/VibeVoice-ASR-bf16 \
  --audio technical_talk.wav \
  --output-path transcript \
  --format json \
  --context "MLX, Apple Silicon, PyTorch, Transformer"
```

Use `--context` when the model exposes a prompt or hotword route. Some model files merge hotwords into a native prompt field rather than a generic keyword list.

## Forced Alignment

```bash
python -m mlx_audio.stt.generate \
  --model mlx-community/Qwen3-ForcedAligner-0.6B-8bit \
  --audio speech.wav \
  --output-path aligned \
  --format json \
  --text "The transcript to align"
```

Alignment requires a transcript that matches the spoken content closely enough to be meaningful.

## WER Evaluation

```bash
python -m mlx_audio.stt.eval \
  --model mlx-community/whisper-large-v3-turbo \
  --output-dir ./eval-out \
  --limit 10 \
  --metrics wer
```

The eval CLI can also stream a Seed-TTS dataset, cache audio, and accept JSON generation kwargs.

## Decision Checklist

1. Decide whether you need ordinary ASR or forced alignment.
2. Decide whether streaming is needed.
3. Decide whether the transcript should be user-provided or model-generated.
4. Check the output format before running.
5. Use `scripts/stt_command_builder.py` and `scripts/wer_summary.py` when you only need a safe plan or a quick summary.
