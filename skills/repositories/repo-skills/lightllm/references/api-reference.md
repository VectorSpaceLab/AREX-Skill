# API reference

This reference summarizes the public HTTP surface and the key request/response
models exposed by `lightllm.server.api_http`, `lightllm.server.api_openai`,
`lightllm.server.api_anthropic`, and `lightllm.server.api_tgi`.

## Public entry points

| Symbol | Purpose |
| --- | --- |
| `lightllm.server.api_server.launch_server(args: StartArgs)` | Dispatches to `pd_master_start`, `config_server_start`, `visual_only_start`, or `normal_or_p_d_start` based on `args.run_mode`. |
| `lightllm.server.api_cli.add_cli_args(parser)` | Adds the LightLLM server CLI flags to an `argparse.ArgumentParser`. |
| `lightllm.server.api_http.app` | FastAPI app that serves the LightLLM-native and OpenAI-compatible routes. |
| `lightllm.server.api_openai` | OpenAI-compatible implementation used by `/v1/chat/completions` and `/v1/completions`. |
| `lightllm.server.api_anthropic` | Anthropic Messages adapter for `/v1/messages`. |
| `lightllm.server.api_tgi` | TGI-style request adapter and streaming helpers. |

## HTTP routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/generate` | POST | LightLLM-native non-streaming generation. |
| `/generate_stream` | POST | LightLLM-native streaming generation. |
| `/get_score` | POST | Score / reward-style request path. |
| `/` | POST | Compatibility alias for the generation path. |
| `/v1/chat/completions` | POST | OpenAI Chat Completions API. |
| `/v1/completions` | POST | OpenAI Completions API. |
| `/v1/messages` | POST | Anthropic Messages API translation layer. |
| `/v1/responses` | POST | OpenAI Responses API surface. |
| `/v1/models` | GET | Model listing endpoint. |
| `/tokens` | GET/POST | Token utility path used by some client flows. |
| `/health`, `/healthz` | GET | Health checks. |
| `/liveness`, `/readiness` | GET/POST | Readiness and liveness probes. |
| `/get_model_name` | GET/POST | Current model name introspection. |
| `/get_server_info` | GET/POST | Server metadata and runtime info. |
| `/get_weight_version` | GET/POST | Weight version metadata. |
| `/token_load` | GET | Current token load. |
| `/metrics` | GET | Prometheus-style metrics endpoint. |
| `/profiler_start`, `/profiler_stop` | GET | Profiler control endpoints. |

The `api_http` app also mounts router modules for PD and RL flows, so deployed
instances may expose additional paths from `lightllm.server.api_http_pd` and
`lightllm.server.api_http_rl`.

## Request model notes

### `CompletionRequest`
Key fields:
- `model`: model name string.
- `prompt`: `str`, `List[str]`, `List[int]`, or `List[List[int]]`.
- `suffix`: optional suffix string.
- `max_tokens` / `max_completion_tokens`.
- Sampling controls: `temperature`, `top_p`, `n`, `best_of`, `top_k`, `do_sample`, `repetition_penalty`, `presence_penalty`, `frequency_penalty`, `ignore_eos`, `seed`.
- Output controls: `stream`, `stream_options`, `logprobs`, `echo`, `stop`, `logit_bias`, `response_format`.

### `ChatCompletionRequest`
Key fields:
- `model`: default is `"default"`.
- `messages`: list of chat messages, including multimodal message blocks.
- `function_call`, `tools`, `tool_choice`, `parallel_tool_calls`.
- Reasoning controls: `reasoning_effort`, `separate_reasoning`, `stream_reasoning`, `chat_template_kwargs`.
- Sampling controls mirror `CompletionRequest`.
- LightLLM-specific additions: `role_settings`, `character_settings`, `seed`.

### Message / tool content
`lightllm.server.api_models` allows a message content block to be:
- plain text,
- image URL content,
- audio URL content,
- tool call metadata,
- reasoning content fields used by reasoning-aware templates.

Relevant model helpers:
- `MessageContent`
- `Message`
- `Tool`
- `ToolChoice`
- `ToolCall`
- `ResponseFormat`
- `UsageInfo`
- `ChatCompletionResponse`
- `CompletionResponse`
- streaming response variants for both chat and completion flows.

## Behavior notes

- `api_openai` selects `uvloop` and `ujson` when available.
- `api_anthropic` depends on `litellm` for the Messages translation path.
- `api_http` includes the LightLLM-native `/generate` route plus the OpenAI,
  Anthropic, and Responses-style compatibility routes.
- Streaming clients should expect SSE-style incremental output and should not
  rely on a single JSON blob.
- Health endpoints may come up before a model is ready; prefer readiness for
  launch validation.

## Related scripts

- `scripts/inspect_api_surface.py` prints the route table and selected schema
  signatures from the installed package.
- `scripts/request_smoke.py` sends a tiny local request to a running server.
