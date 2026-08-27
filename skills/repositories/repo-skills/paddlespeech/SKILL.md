---
name: paddlespeech
description: "Use PaddleSpeech for ASR, speech translation, Whisper, SSL, TTS,
  punctuation restoration, audio classification, speaker vectors, keyword
  spotting, and PaddleSpeech server/client workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleSpeech

Use this skill when the task names PaddleSpeech, `paddlespeech`, `paddlespeech_server`, `paddlespeech_client`, PP-ASR, PP-TTS, PP-VPR, speech recognition, speech translation, Whisper, SSL speech models, text-to-speech, punctuation restoration, audio classification, speaker embedding or verification, keyword spotting, or PaddleSpeech Serving.

## Start Here

1. Decide whether the user wants **package use**, **recipe planning**, **service deployment**, or **repository maintenance**.
2. For package use, prefer the public CLIs and executor classes before reaching for internal model modules.
3. Treat pretrained model execution, sample-audio downloads, dataset downloads, server warmup, Docker services, C++/mobile builds, and GPU training as side effects. Ask before running them unless the user already approved downloads/services/long jobs.
4. Run `scripts/check_paddlespeech_environment.py` for a safe local preflight. It checks imports, metadata, and command availability without downloading models.
5. Read `references/troubleshooting.md` when import, optional dependency, cache, audio-format, model tag, CLI stats, or server-port failures appear.

## Route by Task

- **ASR, speech translation, SSL, and Whisper**: use `sub-skills/speech-to-text/SKILL.md` for `paddlespeech asr`, `st`, `ssl`, `whisper`, `ASRExecutor`, `STExecutor`, `SSLExecutor`, `WhisperExecutor`, audio sample-rate checks, ASR recipes, and transcript post-processing routes.
- **Text-to-speech and vocoders**: use `sub-skills/text-to-speech/SKILL.md` for `paddlespeech tts`, acoustic/vocoder pair selection, ONNX/static inference, multi-speaker and multilingual options, TTS training/synthesis recipes, voice cloning orientation, and TTS frontend interactions.
- **Text processing and frontends**: use `sub-skills/text-processing/SKILL.md` for `paddlespeech text --task punc`, punctuation restoration models, text normalization, G2P, MFA/rhythm-tag prep, and SentencePiece tokenizer recipes.
- **Audio classification, speaker vectors, and KWS**: use `sub-skills/audio-analysis/SKILL.md` for `paddlespeech cls`, `vector`, `kws`, SSL vector extraction, ESC-50, VoxCeleb, HeySnips, audio augmentation, and audio-search planning.
- **Server, clients, streaming, and deployment**: use `sub-skills/deployment-serving/SKILL.md` for `paddlespeech_server start`, `paddlespeech_client`, HTTP and WebSocket APIs, `application.yaml`, streaming ASR/TTS configs, Paddle Inference, ONNX, C++ runtime, Android/ARM, and service troubleshooting.

## Install and Minimal Checks

Install the package and a compatible PaddlePaddle runtime in the same environment. For a CPU package-user baseline:

```bash
python -m pip install paddlepaddle
python -m pip install paddlespeech
python -I -c "import paddle, paddlespeech; print(paddle.__version__)"
```

Then verify the command surfaces without downloading models:

```bash
paddlespeech help
paddlespeech_server help
paddlespeech_client help
```

## Package Orientation

PaddleSpeech is distributed as `paddlespeech` and exposes these console scripts:

```bash
paddlespeech help
paddlespeech_server help
paddlespeech_client help
```

The main `paddlespeech` commands in this checkout are `help`, `version`, `stats`, `asr`, `cls`, `st`, `text`, `tts`, `vector`, `kws`, `ssl`, and `whisper`. The server command exposes `start` and `stats`; the client exposes `tts`, `tts_online`, `asr`, `asr_online`, `cls`, `text`, `vector`, and `acs`.

For direct Python use, prefer executor classes from the command modules, for example `paddlespeech.cli.asr.ASRExecutor`, `paddlespeech.cli.tts.TTSExecutor`, `paddlespeech.cli.text.TextExecutor`, and server/client executors under `paddlespeech.server.bin`.

## References and Helpers

- `references/install-and-environment.md` covers install modes, PaddlePaddle runtime, optional dependencies, cache roots, and backend limits.
- `references/cli-reference.md` lists safe command patterns, batch/stdin/job behavior, and model-stat caveats.
- `references/model-and-resource-overview.md` explains model tags, aliases, resource download/cache behavior, and core released model families.
- `references/troubleshooting.md` covers cross-cutting install, import, dependency, audio, cache, CLI, and server failures.
- `references/repo-provenance.md` records the source revision and evidence baseline.
- `scripts/check_paddlespeech_environment.py` performs safe import and CLI preflight checks.

## Safety Boundaries

- Do not run full demo `run.sh`, training recipes, benchmark/TIPC scripts, server warmup, Docker Compose apps, or model-download examples unless the user explicitly accepts the download/runtime side effects.
- Do not assume CUDA is required. CPU is sufficient for package inspection, command construction, static config checks, and selected safe unit tests; CUDA is optional for faster training/inference.
- Do not assume model quality from a help/import check. Actual ASR/TTS/Whisper/CLS/vector/KWS outputs require model archives, input audio, and runtime checks.
- If a current checkout differs from `references/repo-provenance.md`, refresh this skill before relying on fine-grained paths, model tags, or CLI behavior.
