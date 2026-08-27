---
name: mlx-audio
description: "Use MLX Audio for local TTS, STT, speech enhancement, VAD,
  realtime speech routing, API serving, and conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MLX Audio Repo Skill

Use this skill for practical work with `mlx-audio` 0.4.8: package installation, model-family selection, CLI routing, shared audio I/O, speech streaming, server endpoints, and conversion/quantization guidance.

## Start Here

1. Check the install and core APIs with [`scripts/check_install.py`](scripts/check_install.py).
2. Read [`references/install-and-dependencies.md`](references/install-and-dependencies.md) for extras, backend notes, and safe setup.
3. Use [`references/api-reference.md`](references/api-reference.md) and [`references/model-overview.md`](references/model-overview.md) for verified package facts.
4. Route the task to the focused sub-skill below instead of treating this root file as a manual.

## Route by Task

- Text-to-speech generation, streaming, voice cloning, or model-specific TTS knobs: [`sub-skills/tts-generation/`](sub-skills/tts-generation/)
- Speech-to-text transcription, hotwords, forced alignment, streaming ASR, or WER: [`sub-skills/stt-transcription/`](sub-skills/stt-transcription/)
- Audio enhancement, source separation, VAD, turn detection, or audio I/O: [`sub-skills/speech-transforms-vad/`](sub-skills/speech-transforms-vad/)
- OpenAI-compatible server, realtime WebSockets, Studio UI, or conversion/quantization: [`sub-skills/server-and-conversion/`](sub-skills/server-and-conversion/)

## Core Safety Defaults

- Prefer package docs and the bundled scripts before launching long jobs.
- Use tiny fixtures, parser checks, and `--help` smoke tests before downloading weights or starting a server.
- Treat real model execution as optional unless the user explicitly wants a full inference run.
- For package import or dependency issues, consult [`references/troubleshooting.md`](references/troubleshooting.md) first.

## Bundled Root References

- [`references/repo-provenance.md`](references/repo-provenance.md): source baseline, package version, dirty state, and evidence paths
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): router placement and selection guidance
- [`references/install-and-dependencies.md`](references/install-and-dependencies.md): core dependencies, extras, and safe install checks
- [`references/api-reference.md`](references/api-reference.md): verified signatures and shared runtime facts
- [`references/model-overview.md`](references/model-overview.md): supported TTS/STT/STS/VAD families
- [`references/cli-reference.md`](references/cli-reference.md): CLI names and route map
- [`references/audio-io-and-dsp.md`](references/audio-io-and-dsp.md): shared audio I/O and DSP behavior
- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting install, import, dependency, and audio issues

## Bundled Root Scripts

- [`scripts/check_install.py`](scripts/check_install.py): import/version/API smoke check
- [`scripts/check_optional_deps.py`](scripts/check_optional_deps.py): optional dependency and backend probe

## Common Entry Points

- `mlx_audio.tts.generate` and `mlx_audio.tts.utils.load_model`
- `mlx_audio.stt.generate` and `mlx_audio.stt.utils.load_model`
- `mlx_audio.sts.generate`
- `mlx_audio.server`
- `mlx_audio.convert`

## When to Escalate

If the request needs model weights, device-specific performance claims, or realtime behavior that depends on unavailable hardware, keep the answer scoped to the bundled docs, parser checks, and safe command planning.
