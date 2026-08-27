---
name: speech-to-text
description: "Use PaddleSpeech ASR, speech translation, SSL, and Whisper
  CLIs/APIs with safe audio validation, model choices, and recipe boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Speech-to-Text

Use this sub-skill for PaddleSpeech speech recognition, speech translation, SSL speech models, Whisper transcription/translation, ASR recipe planning, audio validation, ASR job files, and transcript post-processing routes.

## Choose the Workflow

| User goal | Use |
| --- | --- |
| Mandarin or English ASR with PaddleSpeech models | `paddlespeech asr` and `ASRExecutor` guidance in `references/cli-and-api.md` |
| English-to-Chinese speech translation | `paddlespeech st` and ST recipe notes in `references/asr-st-ssl-whisper-workflows.md` |
| Wav2Vec2/Hubert/WavLM ASR or embeddings | `paddlespeech ssl --task asr|vector` guidance |
| General Whisper transcribe/translate | `paddlespeech whisper` guidance |
| ASR training/evaluation recipe planning | recipe map in `references/asr-st-ssl-whisper-workflows.md`; ask before downloads/training |
| Add punctuation to ASR text | route to `../text-processing/SKILL.md` after ASR output exists |
| Serve ASR over HTTP/WebSocket | route to `../deployment-serving/SKILL.md` |

## Safe Workflow

1. Validate audio before model execution:

   ```bash
   python scripts/validate_audio_inputs.py --sample-rate 16000 audio.wav
   ```

2. Pick the command family:

   ```bash
   paddlespeech asr --input audio.wav --lang zh --sample_rate 16000
   paddlespeech st --input english_16k.wav
   paddlespeech ssl --task asr --model wav2vec2 --lang en --input audio.wav
   paddlespeech whisper --task transcribe --size tiny --input audio.wav
   ```

3. If using pretrained defaults, warn that the first run downloads model archives into the PaddleSpeech cache.
4. Use `--device cpu` for deterministic CPU runs or `--device gpu:0` only when a compatible PaddlePaddle GPU build is installed.
5. For long audio, split before ASR rather than relying on a model-specific max-duration failure.

## References and Helper

- `references/cli-and-api.md` lists ASR/ST/SSL/Whisper commands, options, and executor classes.
- `references/asr-st-ssl-whisper-workflows.md` distills training/evaluation, decoding, and recipe boundaries.
- `references/troubleshooting.md` covers audio, model tag, Kaldi, Whisper resource, and long-audio failures.
- `scripts/validate_audio_inputs.py` checks WAV properties and can build simple `.job` files.

## Do Not Do by Default

- Do not run full ASR/ST recipe `run.sh` scripts, `tests/unit/cli/test_cli.sh`, or demo scripts without approval; they download data/models and can train or run for a long time.
- Do not install Kaldi/KenLM/OpenFST/MFA or mutate system tools unless the user explicitly asks for recipe/toolchain execution.
- Do not present SSL or Whisper `stats` display failures as proof that command execution is impossible; use help/import checks and direct tag references.
