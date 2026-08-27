---
name: serving-api
description: "Operate LightLLM HTTP serving, request payloads, streaming, and
  profiler control."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# serving-api

Use this sub-skill when a user wants to start a LightLLM server, send a
request to one of its HTTP APIs, debug a streaming response, enable profiler
control, or understand the serving-side request/response shapes.

## Covers

- `python -m lightllm.server.api_server` startup for single-node serving.
- LightLLM-native `/generate` and `/generate_stream` calls.
- OpenAI-compatible `/v1/chat/completions` and `/v1/completions` calls.
- Anthropic-compatible `/v1/messages` and OpenAI Responses `/v1/responses`.
- Health, readiness, liveness, model-info, token-load, metrics, and profiler
  endpoints.
- Function calling, reasoning parser settings, and multimodal request payloads.
- Response schema expectations for streamed and non-streamed outputs.

## Does not cover

- Whether a particular model family or backend is supported.
- PD disaggregation or multi-node launch order.
- Benchmark design beyond a single smoke request against a running server.

## Read first

- [../../references/api-reference.md](../../references/api-reference.md)
- [../../references/cli-reference.md](../../references/cli-reference.md)
- [references/workflows.md](references/workflows.md)
- [references/troubleshooting.md](references/troubleshooting.md)

## Use this route when the user says

- “start the LightLLM API server”
- “how do I call `/generate`?”
- “how do I use the OpenAI / Anthropic compatibility APIs?”
- “why is streaming empty or truncated?”
- “how do I enable profiler start/stop or check metrics?”
- “how should I format multimodal or tool-call requests?”

## Minimal working sequence

1. Confirm the package is installed and the CUDA/runtime environment is ready.
2. Read the CLI and API references for the chosen endpoint family.
3. Start the server with the smallest valid `StartArgs` subset.
4. Use `scripts/request_smoke.py` for a single local request before any larger
   integration or benchmark call.
5. If the request shape fails, compare the payload against the request models in
   `references/api-reference.md`.

## Common decision points

- Use `/generate` for the LightLLM-native string input path.
- Use `/v1/completions` for completion-style prompts.
- Use `/v1/chat/completions` for message lists, tool calls, and reasoning-aware
  chat flows.
- Use `/v1/messages` only when Anthropic compatibility is explicitly needed.
- Use `/v1/responses` when a client expects the newer OpenAI Responses schema.
- Use `/readiness` rather than `/health` when a benchmark or deploy script needs
  a real launch signal.

## Bundled helper scripts

- `../../scripts/inspect_api_surface.py` prints the live route table and schema
  signatures.
- `../../scripts/request_smoke.py` can send a tiny request to a running local
  server.
- `../../scripts/inspect_start_args.py` helps when a flag combination is not
  accepted.

## Troubleshooting highlights

- The server may import before the model is ready; check readiness, not only
  health.
- Proxy variables can break local calls to `localhost` or the PD master host.
- Streaming clients must handle SSE-style incremental output.
- Multimodal payloads must use the structured message content blocks described
  in the API reference.
- `/v1/messages` can fail if `litellm` is not installed.

## Review standard

This sub-skill is complete when a future agent can:

- start a serving process,
- select the correct endpoint family,
- construct a minimal valid payload,
- interpret the first response shape,
- and diagnose the common API/path/proxy failures without reopening the source
  repository.
