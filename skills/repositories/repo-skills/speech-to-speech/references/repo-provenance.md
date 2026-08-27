# Repo provenance and refresh baseline

Schema: `disco.repo-provenance.v1`

## Source identity

| Field | Value |
| --- | --- |
| Repository | `https://github.com/huggingface/speech-to-speech.git` |
| Branch | `main` |
| Commit | `0071d7d0be64d77f7c66db410781109d5a2bf5b7` |
| Tag | none available from the inspected checkout |
| Distribution | `speech-to-speech` |
| Package version | `0.2.12` |
| Import root | `speech_to_speech` |
| Python requirement | `>=3.10` |
| Console entry point | `speech-to-speech = speech_to_speech.cli:main` |

The inspected source tree was clean before generated `skills/` production
artifacts were added. Generated skill files and review artifacts are not source
evidence for runtime behavior.

## Primary evidence paths

These relative source paths were distilled into this self-contained skill:

- `README.md`
- `pyproject.toml`
- `MANIFEST.in`
- `src/speech_to_speech/__init__.py`
- `src/speech_to_speech/cli.py`
- `src/speech_to_speech/s2s_pipeline.py`
- `src/speech_to_speech/backend_registry.py`
- `src/speech_to_speech/arguments_classes/`
- `src/speech_to_speech/api/openai_realtime/`
- `src/speech_to_speech/pipeline/`
- `src/speech_to_speech/VAD/`
- `src/speech_to_speech/STT/README.md`
- `src/speech_to_speech/LLM/README.md`
- `src/speech_to_speech/TTS/README.md`
- `src/speech_to_speech/TTS/qwen3_tts_handler.py`
- `demo/README.md`
- `demo/CONTEXT.md`
- `demo/DESIGN.md`
- `demo/server.py`
- `demo/main.js`
- `demo/ws/`
- `demo/rtc/`
- `demo/ui/`
- `demo/worklets/`
- `demo/tool-call-batcher.js`
- `examples/gemma4-12b-macos/README.md`
- `scripts/synthetic_conversation_realtime_client.py`
- `scripts/benchmark_stt.py`
- `scripts/benchmark_tts.py`
- `tests/`
- `Dockerfile`, `Dockerfile.arm64`, `docker-compose.yml`, `demo/Dockerfile`

## Excluded or reference-only source areas

- `archive/`: deprecated implementations not wired into the current CLI.
- `assets/`, `docs/assets/`, images/logos: visual/static assets not needed for
  runtime operating guidance.
- release/publish automation and star-history scripts: maintainer automation
  outside the selected runtime/package operation scope.
- full native benchmark runs, model downloads, live endpoint soaks, and Apple
  Silicon-only local Gemma/Qwen3 execution: preserved as optional/reference
  guidance rather than verified as required runtime capability in this skill.

## Installed-package facts used

Read-only installed-package inspection verified public package behavior without
recording local environment paths in this runtime skill. Verified facts included:

- distribution and package version `0.2.12`;
- imports for `speech_to_speech`, CLI, backend registry, Realtime server/client;
- CLI help for root, `serve`, `talk`, and `local`;
- backend registry names:
  - STT: `none`, `whisper`, `whisper-mlx`, `mlx-audio-whisper`,
    `faster-whisper`, `parakeet-tdt`, `paraformer`;
  - LLM: `transformers`, `mlx-lm`, `responses-api`, `chat-completions`;
  - TTS: `chatTTS`, `facebookMMS`, `pocket`, `kokoro`, `qwen3`;
- default profile: `parakeet-tdt` + `responses-api` + `qwen3`;
- safe CUDA smoke on the host was available, but full model inference was not
  selected as a required verification target.

## Refresh triggers

Refresh this repo skill when source changes affect:

- package version, Python support, dependencies, optional extras, or console
  entry points;
- command family, CLI flags, legacy mode handling, default component profile,
  or backend registry names;
- Realtime event schemas, WebSocket/WebRTC endpoints, session update merge
  behavior, cancellation/barge-in, LLM proxy, or pool release behavior;
- Qwen3-TTS wheel/model/backend/language/voice-reference rules;
- browser demo connection modes, env vars, search/camera tools, OAuth/limits,
  or design-language constraints;
- native tests that contradict the guidance in this skill.
