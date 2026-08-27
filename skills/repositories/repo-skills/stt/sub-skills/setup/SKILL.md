---
name: setup
description: "Install, verify, configure, and launch the local speech-to-text server."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Setup

Use this sub-skill when the user needs to prepare a local checkout for first launch or recovery: create the environment, install runtime dependencies, verify ffmpeg/ffprobe, place or download models, choose CPU vs CUDA, interpret `set.ini`, and start the server safely.

## Use for
- fresh installs and environment repair
- dependency installation and import failures
- ffmpeg/ffprobe availability checks
- model directory placement and first-run downloads
- CPU vs CUDA startup selection
- launch wrappers and startup troubleshooting

## Do not use for
- browser upload flow
- `/api` or `/v1/audio/transcriptions` request details
- OpenAI-compatible client examples
- post-launch transcription behavior

For those topics, use [`transcription`](../transcription/SKILL.md). For shared launch failures and broader runtime issues, use the [root troubleshooting guide](../../references/troubleshooting.md).

## What this sub-skill owns
- Python version selection and virtual environment setup
- runtime dependency installation
- `ffmpeg` / `ffprobe` checks
- `models/` layout and model download expectations
- `set.ini` startup keys and device selection
- safe launch helpers and startup diagnostics

## Bundled files
- [`references/install-and-launch.md`](references/install-and-launch.md)
- [`references/configuration.md`](references/configuration.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`../../scripts/check-runtime.py`](../../scripts/check-runtime.py)
- [`scripts/check-cuda.py`](scripts/check-cuda.py)
- [`scripts/launch-server.py`](scripts/launch-server.py)

## Working order
1. Read `references/install-and-launch.md` for the normal install and launch path.
2. Read `references/configuration.md` when the user asks about `set.ini`, model selection, or CPU/CUDA toggles.
3. Run `../../scripts/check-runtime.py --repo-root <checkout>` before launch.
4. Run `scripts/check-cuda.py` only when CUDA is expected or needs diagnosis.
5. Use `scripts/launch-server.py --repo-root <checkout>` to start the app from the current checkout.
6. If startup fails, use `references/troubleshooting.md`, then hand off to `transcription` only after the server is reachable.

## Preserved runtime facts
- `start.py` launches a Flask + gevent server, starts a background update check and transcription worker, and opens the browser automatically.
- The GUI worker path uses `WhisperModel(device=sets.get('devtype'), download_root=<project>/models)` and does not pass `temperature` or `cuda_com_type` into `WhisperModel`.
- The API path applies `temperature`, while `devtype` still selects CPU vs CUDA.
- `set.ini` exposes `cuda_com_type`, but the current observed runtime path does not consume it during model creation.
