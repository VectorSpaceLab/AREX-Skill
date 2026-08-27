---
name: stt
description: "Operate the STT local speech-to-text app for setup, browser
  uploads, HTTP transcription APIs, and CUDA-aware troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# STT repo skill

Use this skill when the task is about the `jianchang512/stt` local speech-to-text app: installing it, launching the local server, transcribing audio/video through the browser UI, calling its HTTP APIs, or debugging ffmpeg/model/CUDA failures.

The app is a Flask/gevent service around `faster-whisper`. It exposes a browser UI plus a legacy `/api` endpoint and an OpenAI-compatible `/v1/audio/transcriptions` endpoint. It can run on CPU by default and can use NVIDIA CUDA when the runtime and model stack are prepared.

## First route the task

- **Setup, launch, config, and backend checks:** read `sub-skills/setup/SKILL.md` when the user asks how to install dependencies, choose Python, place models, configure `set.ini`, verify `ffmpeg`/`ffprobe`, launch the local server, or enable/diagnose CUDA.
- **Transcription usage and clients:** read `sub-skills/transcription/SKILL.md` when the user wants browser upload steps, batch exports, request fields for `/api`, OpenAI SDK/client integration, or response-format parsing.
- **Cross-cutting diagnosis:** read `references/troubleshooting.md` when symptoms span launch and request handling, such as model downloads, empty output, update-check noise, or backend warnings.
- **Repo context and staleness:** read `references/overview.md` for the component map and `references/repo-provenance.md` before assuming the generated skill matches a newer checkout.

## Quick operating context

- Default local service address is `127.0.0.1:9977` unless the runtime config changes it.
- Supported result formats are `text`, `json`, and `srt`.
- The browser flow uploads files, converts them to mono 16 kHz WAV through ffmpeg, queues transcription, polls progress, and renders/export results.
- The legacy API wraps results in `{code, msg, data}`; the OpenAI-compatible endpoint uses the `/v1/audio/transcriptions` route and OpenAI-style multipart fields.
- Model choices are controlled by the runtime model list; larger models improve quality but raise CPU/GPU memory pressure.
- Once model files and ffmpeg are present, transcription can run locally; first-run model download and update checks may touch the network.

## Install and minimal verification

For a fresh source checkout, create an isolated Python environment, install the runtime dependencies, and run the lightweight runtime probe before launching:

```bash
python -m pip install -r requirements.txt
python scripts/check-runtime.py --repo-root <checkout>
```

If CUDA needs to be checked, use `sub-skills/setup/scripts/check-cuda.py` after the runtime probe. Then route to `sub-skills/setup/SKILL.md` or `sub-skills/transcription/SKILL.md` for the detailed workflow.

## Bundled helpers

Use these helpers instead of relying on source examples directly:

- `scripts/check-runtime.py` checks core imports and `ffmpeg`/`ffprobe` availability from a candidate checkout.
- `sub-skills/setup/scripts/check-cuda.py` reports optional CUDA/CuDNN/CTranslate2 visibility without blocking when CUDA is absent.
- `sub-skills/setup/scripts/launch-server.py` wraps the repo launcher with sanity checks.
- `sub-skills/transcription/scripts/api-smoke.py` adapts the repo's API example into an argument-driven client smoke test.

## What not to use this skill for

- Generic speech AI tasks that do not involve this STT app.
- TTS, voice cloning, diarization, forced alignment, audio enhancement, or model training unrelated to the app.
- Maintaining vendored static assets or release packaging unless the user explicitly asks for repository maintenance rather than app operation.

## Evidence-backed constraints

- The source checkout has no standard Python packaging metadata; prepare dependencies from the documented runtime requirement set and then run the app from a checkout.
- The code currently exposes `cuda_com_type` in config but does not pass that key into `WhisperModel`; do not promise it changes compute type unless the code changes.
- The browser worker path and API helper path do not use every config key identically; check `sub-skills/setup/references/configuration.md` before diagnosing a config setting that appears ignored.

## Router metadata

`references/repo-routing-metadata.json` places this skill in the `speech-ai-modeling-and-audio-workflows` scenario for managed repo-skill import. This run was requested as **not import**, so treat that metadata as ready for later verification/import tooling, not as evidence that import already happened.
