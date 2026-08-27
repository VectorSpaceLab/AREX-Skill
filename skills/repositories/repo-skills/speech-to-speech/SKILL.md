---
name: speech-to-speech
description: "Operate and troubleshoot Hugging Face speech-to-speech, a modular
  VAD, STT, LLM, and TTS voice-agent pipeline with an OpenAI Realtime-compatible
  API and browser demo."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# speech-to-speech repo skill

Use this skill for package-specific tasks involving the `speech-to-speech`
Python package: starting its CLI, wiring a voice-agent backend, using its
OpenAI Realtime-compatible WebSocket/WebRTC API, choosing STT/LLM/TTS backends,
or running/modifying the browser demo.

## First decisions

1. **Install or inspect package/runtime basics:** read
   [Install and runtime](references/install-and-runtime.md). The package is
   distributed as `speech-to-speech`, imports as `speech_to_speech`, requires
   Python 3.10+, and exposes the `speech-to-speech` console command.
2. **Start or connect from the CLI:** route to
   [cli-and-server](sub-skills/cli-and-server/SKILL.md).
3. **Build a WebSocket/WebRTC or OpenAI Realtime client:** route to
   [realtime-api](sub-skills/realtime-api/SKILL.md).
4. **Choose or debug VAD/STT/LLM/TTS backends, language, prompts, tools, direct
   audio input, or benchmarks:** route to
   [components-and-backends](sub-skills/components-and-backends/SKILL.md).
5. **Run, deploy, or edit the browser demo:** route to
   [browser-demo](sub-skills/browser-demo/SKILL.md).
6. **Diagnose cross-cutting package/runtime issues:** read
   [Troubleshooting](references/troubleshooting.md), then route to the nearest
   sub-skill for workflow-specific fixes.

## Common task routes

| User asks for... | Use |
| --- | --- |
| `speech-to-speech serve`, `talk`, `local`, host/port, VAD flags, Smart Turn, session pool, or LLM proxy command shape | [cli-and-server](sub-skills/cli-and-server/SKILL.md) |
| Realtime events, `session.update`, `response.create`, tool result flow, barge-in/cancel, endpoint probes, `/v1/realtime`, `/v1/realtime/calls` | [realtime-api](sub-skills/realtime-api/SKILL.md) |
| Backend names, optional extras, Qwen3-TTS, Parakeet/Whisper/Paraformer, `responses-api` vs `chat-completions`, `--stt none`, language prompt | [components-and-backends](sub-skills/components-and-backends/SKILL.md) |
| Demo server, `SPEECH_TO_SPEECH_URL`, `LOAD_BALANCER_URL`, WebSocket vs WebRTC in browser, Serper search, camera tool, HF Space limits, UI design rules | [browser-demo](sub-skills/browser-demo/SKILL.md) |
| Source freshness, evidence baseline, router metadata | [Repo provenance](references/repo-provenance.md) and [routing metadata](references/repo-routing-metadata.json) |

## Minimal install and smoke

```bash
pip install speech-to-speech
python -c "import speech_to_speech; print(speech_to_speech.__version__)"
speech-to-speech --help
```

Default quickstart:

```bash
export OPENAI_API_KEY="..."
speech-to-speech serve
# second terminal
speech-to-speech talk --url ws://127.0.0.1:8765/v1/realtime
```

The default server listens on loopback at `ws://127.0.0.1:8765/v1/realtime`
and uses Parakeet TDT STT, an OpenAI-compatible Responses API LLM, and Qwen3-TTS.

## Safety and verification notes

- Keep `serve` bound to `127.0.0.1` unless a trusted network or gateway is in
  place. `--enable_llm_proxy` adds unauthenticated OpenAI-compatible HTTP proxy
  routes and should not be exposed casually.
- Optional backends may require extra packages, CUDA/MPS runtime support, model
  downloads, audio devices, or provider credentials. Do not claim full model
  inference was verified from import/CLI checks alone.
- For safe local inspection, this skill bundles helper scripts that avoid model
  downloads: [`scripts/package_smoke.py`](scripts/package_smoke.py),
  [`cli-and-server/scripts/check_cli_profiles.py`](sub-skills/cli-and-server/scripts/check_cli_profiles.py),
  [`components-and-backends/scripts/inspect_backend_registry.py`](sub-skills/components-and-backends/scripts/inspect_backend_registry.py), and
  [`realtime-api/scripts/realtime_endpoint_probe.py`](sub-skills/realtime-api/scripts/realtime_endpoint_probe.py).
- Do not rely on deprecated archive implementations or removed legacy transport
  flags. Use the current command family and registered backend names.

## Source baseline

This skill was distilled from `huggingface/speech-to-speech` at commit
`0071d7d0be64d77f7c66db410781109d5a2bf5b7`, branch `main`, package version
`0.2.12`. See [Repo provenance](references/repo-provenance.md) for evidence
paths and refresh signals.
