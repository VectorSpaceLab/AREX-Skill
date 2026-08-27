# Model Overview

`mlx-audio` organizes model families by workflow rather than by a single backbone.

## TTS Families

Representative model families include:

- Kokoro
- KittenTTS
- Qwen3-TTS
- Higgs Audio v2 / v3
- OmniVoice
- CSM / MisoTTS
- Dia
- OuteTTS
- Spark
- Chatterbox
- Soprano
- Ming Omni TTS
- KugelAudio
- Voxtral TTS
- LongCat-AudioDiT
- MeloTTS
- MOSS-TTS

Use the TTS sub-skill for voice cloning, streaming, and model-specific control tokens or prompts.

## STT Families

Representative model families include:

- Whisper and Distil-Whisper
- Qwen3-ASR and Qwen3-ForcedAligner
- Parakeet
- Nemotron 3.5 ASR
- Voxtral and Voxtral Realtime
- VibeVoice-ASR
- Canary
- Moonshine
- MMS
- Granite Speech
- Qwen2-Audio
- MOSS-Transcribe-Diarize
- MOSS-Music

Use the STT sub-skill for transcription formats, hotwords/context, streaming ASR, alignment, and WER evaluation.

## VAD / Diarization

- Silero VAD
- Sortformer v1
- Sortformer v2.1

Use the VAD and realtime sub-skill for turn detection, server-side `server_vad`, and streaming speech boundaries.

## STS / Audio-to-Audio Families

- DeepFilterNet
- MossFormer2 SE
- SAM-Audio
- LFM2.5-Audio

Use the STS/VAD sub-skill for enhancement, separation, and audio I/O guidance.
