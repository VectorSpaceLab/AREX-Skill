---
name: realtime-voice
description: "Build OpenAI Agents Python realtime sessions, audio event loops,
  telephony attach flows, and optional voice pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Realtime Voice

Use this sub-skill when the task mentions `RealtimeAgent`, `RealtimeRunner`, `RealtimeSession`, `gpt-realtime`, `send_audio`, realtime session events, playback-tracked interruptions, `Twilio`, `SIP`, `VoicePipeline`, or the `openai-agents[voice]` optional extra.

## Start Here

- For realtime agent/session classes, config shapes, event handling, playback tracking, raw events, tools, approvals, handoffs, and guardrails, read [references/realtime-api-reference.md](references/realtime-api-reference.md).
- For speech-to-text/text-to-speech voice pipelines, static vs streamed audio input, model provider choices, and tracing, read [references/voice-pipeline.md](references/voice-pipeline.md).
- For missing optional dependencies, websocket/network failures, audio format mismatches, manual turn control, interruption truncation, telephony deployment concerns, and unsupported structured outputs, read [references/troubleshooting.md](references/troubleshooting.md).
- To validate a small realtime/voice config without network, microphone, speaker, or API calls, run [scripts/check_realtime_config.py](scripts/check_realtime_config.py).

## Routing Boundaries

- Stay here for realtime session lifecycle, `RealtimeAgent` limitations, `RealtimeRunConfig`, `RealtimeSessionModelSettings`, text/audio/image inputs, raw client events, event-loop patterns, playback-tracked interruption, realtime tool approval loops, realtime handoffs, realtime output guardrails, SIP attach flows, Twilio-style media patterns, and voice pipeline workflows.
- Route ordinary HTTP/SSE `Runner.run_streamed` work to ../core-runtime/SKILL.md.
- Route provider setup, OpenAI provider options, base URLs, websocket provider selection, and model retry policy outside realtime-specific session config to ../models-providers/SKILL.md.
- Route general function-tool, approval, handoff, and guardrail declaration basics to ../tools-handoffs-guardrails/SKILL.md.

## Key Decisions

- Use `RealtimeAgent` plus `RealtimeRunner` for low-latency bidirectional sessions over a server-side WebSocket or SIP attach flow; do not expect browser WebRTC transport from this SDK.
- Configure realtime model choice and audio formats at the session level, preferably with nested `audio.input` / `audio.output` settings and `model_name="gpt-realtime-2"` for new realtime agents.
- Use `send_message()` for text and structured text/image messages, `send_audio()` for raw audio chunks, and raw model events only when you need manual turn or response control.
- Add `RealtimePlaybackTracker` when user playback is delayed or remote, especially telephony, so interruption truncation reflects what the user actually heard.
- Use `VoicePipeline` only when the desired shape is STT → normal agent/workflow → TTS; it requires `pip install 'openai-agents[voice]'` and imports `numpy`/`websockets`.

## Safety Notes

- Do not tell future agents to run the original realtime or voice examples as prerequisites; credentialed, networked, microphone, speaker, and telephony patterns are distilled into the bundled references.
- Do not put API keys, webhook secrets, call IDs, phone numbers, base URLs, or local device names in generated skill content or committed config.
- The bundled checker validates imports and static config only; it intentionally never opens a websocket, calls OpenAI, records audio, or plays audio.
