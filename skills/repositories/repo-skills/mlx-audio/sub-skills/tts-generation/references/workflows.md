# TTS Workflows

## Basic Generation

```bash
mlx_audio.tts.generate \
  --model mlx-community/Kokoro-82M-bf16 \
  --text "Hello, world!" \
  --voice Chelsie \
  --lang_code English
```

## Voice Cloning

### CSM / MisoTTS style cloning

```bash
mlx_audio.tts.generate \
  --model mlx-community/csm-1b \
  --text "Hello from Sesame." \
  --ref_audio ./reference_voice.wav \
  --play
```

### Qwen3-TTS cloning

```python
from mlx_audio.tts.utils import load_model

model = load_model("mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16")
results = list(model.generate(
    text="Hello, welcome to MLX-Audio!",
    ref_audio="sample_audio.wav",
    ref_text="This is what my voice sounds like.",
))
```

### OmniVoice cloning gotcha

OmniVoice preprocesses the reference audio before transcription. Transcribe the preprocessed clip, not the raw file, or the transcript can be longer than the actual reference audio and leak extra words into generation.

## Streaming

```bash
mlx_audio.tts.generate \
  --model mlx-community/Kokoro-82M-bf16 \
  --text "This is a streaming example." \
  --lang_code a \
  --stream
```

Notes:

- `--stream` implies playback.
- The default streaming interval is `2.0` seconds.
- Use `--streaming_interval` to trade latency for chunk overhead.

## Streaming plus Save

```bash
mlx_audio.tts.generate \
  --model mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit \
  --text "Stream and save this utterance." \
  --voice Chelsie \
  --stream \
  --save
```

Use `--join_audio` if you want one output file instead of numbered chunks when the model emits multiple segments.

## Practical Decision Checklist

1. Pick the model family first.
2. Decide whether voice cloning is needed.
3. Decide whether the reference transcript is required or should be auto-generated.
4. Decide whether streaming is needed.
5. If a command only needs planning, use `scripts/tts_command_builder.py` instead of starting a model run.
