---
name: online-serving
description: "Operate vLLM-Omni HTTP serving, --omni CLI routing,
  OpenAI-compatible payloads, stage head/headless launches, realtime/streaming
  routes, and serving recovery without reopening repository evidence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vLLM-Omni online serving

Use this sub-skill when the task involves starting a vLLM-Omni HTTP server,
building OpenAI-compatible request payloads, choosing a streaming/realtime route,
or recovering a failed serving launch.

## Fast route

1. Always include `--omni` when serving an Omni model. Without it, the command
   routes to ordinary upstream vLLM behavior and Omni-specific endpoints or flags
   may be missing.
2. Choose a launch shape:
   - Single runtime: `vllm serve MODEL --omni --port 8091` or
     `vllm-omni serve MODEL --omni --port 8091`.
   - Stage head plus headless worker processes: read
     [CLI and OpenAI API](references/cli-and-openai-api.md#stage-head-and-headless-launches).
3. Choose an endpoint from
   [CLI and OpenAI API](references/cli-and-openai-api.md#endpoint-chooser):
   chat completions, image generation/edit, videos, text-to-speech, text-to-audio,
   or OpenAI-style model listing/health.
4. For streaming and realtime use cases, read
   [Realtime and streaming](references/realtime-and-streaming.md) before writing
   a WebSocket or Server-Sent Events client.
5. To generate a safe no-network payload scaffold, run the bundled helper from
   this sub-skill directory:

   ```bash
   python scripts/build_openai_payload.py --endpoint chat \
     --model Qwen/Qwen3-Omni-30B-A3B-Instruct \
     --prompt "Describe this scene" \
     --extra-json '{"modalities":["text"]}'
   ```

6. If the server rejects the command, ignores request fields, cannot register a
   stage, or the client gets connection errors, read
   [Troubleshooting](references/troubleshooting.md).

## Boundaries

- Offline `Omni` / `AsyncOmni` Python generation, output objects, and local
  prompt dictionaries -> use `offline-inference`.
- Deploy YAML schema, connector design, stage memory placement, and overlay
  validation -> use `stage-configuration`.
- Model-family selection, hardware/backends, quantization/offload/cache recipes,
  and benchmark route selection -> use `model-recipes`.
- Editing vLLM-Omni model implementations, custom pipelines, or TTS adapters ->
  use `model-integration`.

## Safety notes

- Do not run model-serving examples, download checkpoints, or open gated model
  licenses unless the user explicitly approves the GPU, network, cache, and time
  budget.
- Treat repository examples that require a live server, browser, model weights, or
  service ports as evidence only; reproduce their payload intent with the bundled
  references and helper.
- Do not reopen the original repository just to find routes, flags, or payload
  shapes. This sub-skill and its references are the runtime source of truth.
