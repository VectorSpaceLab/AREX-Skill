---
name: cli-and-server
description: "Operate speech-to-speech from the Python CLI, choosing serve,
  local, or talk safely and tuning server binding, audio, endpointing, live
  transcription, session capacity, and the command-level LLM proxy."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# CLI and server operation

Use this sub-skill when the task is to start or connect to the Python package,
choose a command profile, expose the Realtime server, or diagnose command-level
capacity and endpointing behavior.

## Route by intent

- **Build or expose a Realtime service:** use `speech-to-speech serve`.
- **Connect the packaged microphone/speaker client to an existing service:** use
  `speech-to-speech talk --url <full-endpoint>`.
- **Run the service and packaged audio client together on one machine:** use
  `speech-to-speech local`; it is forced to loopback and accepts local audio
  flags, not a public host.
- **Choose STT, LLM, TTS implementations, optional extras, language/voice
  models, or direct-audio model compatibility:** route to
  [components-and-backends](../components-and-backends/SKILL.md).
- **Debug Realtime events, WebSocket/WebRTC transport, tool calls, or protocol
  lifecycle:** route to [realtime-api](../realtime-api/SKILL.md).

## Safe operating sequence

1. Pick exactly one of `serve`, `talk`, or `local`; use the command-specific
   flags rather than mixing server and client options.
2. Start with the default profile unless a local LLM, a provider base URL, or a
   platform preset is intentional. Read [CLI reference](references/cli-reference.md)
   for the profile commands and invalid combinations.
3. Keep `serve` on `127.0.0.1` unless a trusted network or an authenticated
   gateway is already in place. Read [server runtime](references/server-runtime.md)
   before using `--host 0.0.0.0` or `--enable_llm_proxy`.
4. For choppy or premature turns, tune VAD and Smart Turn together rather than
   changing the LLM first. For capacity errors, size `--num_pipelines` to the
   number of concurrent sessions and watch for `session_limit_reached`.
5. Use the bundled safe checker for parser/default smoke checks:
   [`scripts/check_cli_profiles.py`](scripts/check_cli_profiles.py). It does not
   download models or start a server.

## Non-negotiable command rules

- `talk` owns the full Realtime URL and audio-client options; it does not accept
  server host/port, backend selectors, or pipeline flags.
- `serve` owns host/port and pipeline flags; it does not accept `talk`'s
  `--url` or `local`'s `--local_audio_*` flags.
- `local` owns the loopback port and `--local_audio_*` flags; it rejects
  `--host` and always connects to
  `ws://127.0.0.1:<port>/v1/realtime` internally.
- The old top-level `--mode realtime` and `--mode local` are temporary aliases
  with a deprecation warning. Other old mode values are rejected; migrate to
  the three-command family.

Detailed flags, profiles, security notes, endpointing behavior, and failure
handling are bundled in:

- [references/cli-reference.md](references/cli-reference.md)
- [references/server-runtime.md](references/server-runtime.md)
- [references/troubleshooting.md](references/troubleshooting.md)
