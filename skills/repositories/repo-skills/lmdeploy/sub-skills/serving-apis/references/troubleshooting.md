# LMDeploy Serving Troubleshooting

Use symptoms first, then verify the command, endpoint, and client base URL.

## Server Fails or Runs Out of Memory

Symptoms:

- Server exits during model load.
- CUDA OOM or allocation failures appear in logs.
- Requests hang or fail after a few long prompts.

Recovery:

1. Lower KV cache pressure with `--cache-max-entry-count`, for example `--cache-max-entry-count 0.4`.
2. Reduce `--session-len`, `--max-batch-size`, or `--max-prefill-token-num`.
3. Use the intended backend explicitly with `--backend pytorch` or `--backend turbomind`.
4. Reduce tensor parallel or deployment size only if the model/backend supports the new shape.
5. For proxy deployments, confirm only healthy nodes remain in `/nodes/status`.

## Responses Stop With `finish_reason: "length"`

Meaning:

- The model reached the request output limit or the server/session context limit.

Recovery:

- Increase request `max_tokens`, `max_completion_tokens`, or `max_output_tokens` when the output cap is too small.
- Increase `--session-len` when the total prompt plus generated tokens exceed the engine session length.
- If increasing `--session-len` causes OOM, lower `--cache-max-entry-count`, batch size, or model size.

## Stop Words Do Not Stop Generation

Cause:

- LMDeploy's OpenAI-compatible stop handling expects stop words that encode to a single token id for reliable behavior.

Recovery:

- Test the stop string with tokenization through `APIClient.encode`.
- Prefer simple single-token stops.
- Use `include_stop_str_in_output` only when the client expects the matched stop text in output.

## Client Cannot Connect or Times Out

Symptoms:

- `curl` cannot connect.
- OpenAI/Anthropic SDK reports connection refused or read timeout.
- Proxy reports node add timeout.

Recovery:

1. Check that the process is listening on the expected port.
2. Use `127.0.0.1` for same-host clients and a real host IP/DNS name for remote clients.
3. Do not use `0.0.0.0` as a client destination or proxy peer URL. It is a bind address only.
4. Probe `GET /v1/models` before generation endpoints.
5. For long streaming clients, increase the client-side idle/read timeout.
6. For proxy nodes, add or register `http://<real-node-ip>:<port>`, then check `/nodes/status`.

## Authentication Fails

Symptoms:

- HTTP 401/403 style failures.
- Client works without `--api-keys` but fails after enabling it.

Recovery:

- Start the server with `--api-keys key-a key-b`.
- Send `Authorization: Bearer key-a` on OpenAI, Responses, Anthropic, and proxy requests.
- For OpenAI SDK, pass `api_key="key-a"`.
- For `APIClient`, pass `APIClient("http://host:port", api_key="key-a")`.
- For Codex, set the configured `env_key` such as `LMDEPLOY_API_KEY` to a matching key.
- For Claude Code, set `ANTHROPIC_AUTH_TOKEN` to a matching key.

## HTTPS Does Not Start

Cause:

- `--ssl` requires `SSL_KEYFILE` and `SSL_CERTFILE` environment variables.

Recovery:

```bash
export SSL_KEYFILE=/path/to/key.pem
export SSL_CERTFILE=/path/to/cert.pem
lmdeploy serve api_server <model> --ssl
```

Use `https://...` in client base URLs after enabling SSL.

## FastAPI Docs or OpenAPI Missing

Cause:

- Server was launched with `--disable-fastapi-docs`.

Recovery:

- Remove `--disable-fastapi-docs` for interactive Swagger UI or OpenAPI schema inspection.
- Keep it enabled for locked-down production deployments and validate with direct endpoint curls instead.

## Endpoint Confusion

Common mistakes:

- Passing `http://host:port/v1` to `APIClient`; it expects `http://host:port`.
- Passing `http://host:port/v1/responses` as Codex `base_url`; Codex expects the `/v1` root.
- Passing `http://host:port/v1` as `ANTHROPIC_BASE_URL`; Claude Code expects the server root.
- Querying only `/v1/models` for Anthropic model discovery when the documented Anthropic model list is `/anthropic/v1/models`.

Recovery:

- OpenAI SDK: `base_url="http://host:port/v1"`.
- Responses/Codex: `base_url = "http://host:port/v1"`, `wire_api = "responses"`.
- Anthropic/Claude Code: `ANTHROPIC_BASE_URL=http://host:port`.
- LMDeploy `APIClient`: `APIClient("http://host:port")`.

## Tool Calls Are Plain Text or Missing

Cause:

- Server was not launched with a matching `--tool-call-parser`.
- The parser does not match the model family or prompt/tool schema.
- The model cannot reliably follow tool-call format.

Recovery:

1. Restart with a model-family parser, for example `--tool-call-parser qwen`, `--tool-call-parser internlm`, or another parser shown by installed `lmdeploy serve api_server --help`.
2. Keep tool schemas valid JSON Schema objects.
3. For Responses tools, use function tools; non-function hosted tools are accepted but ignored.
4. For Anthropic tools, use `input_schema` and check for `tool_use` content blocks.
5. Validate both streaming and non-streaming because streamed tool-call arguments arrive as deltas.

## Reasoning Content Is Missing

Cause:

- Server was not launched with `--reasoning-parser`.
- Parser name does not match model output format.
- Some parsers only start reasoning under model-specific flags; for example DeepSeek V3 reasoning may depend on `enable_thinking`.

Recovery:

- Restart with a documented parser such as `--reasoning-parser deepseek-r1`, `deepseek-v3`, `qwen3`, or `gpt-oss` when appropriate.
- Inspect non-streaming `message.reasoning_content` and streaming `delta.reasoning_content` for OpenAI chat.
- Inspect Anthropic `thinking` content blocks or `thinking_delta` streaming events.
- Avoid promising hidden chain-of-thought behavior; document only the parser-exposed reasoning field content.

## Proxy Routes to Wrong or No Model

Symptoms:

- Proxy returns model-not-found errors.
- `/v1/models` at the proxy lacks expected node models.
- Requests route unevenly or stale nodes remain.

Recovery:

1. Check `curl http://proxy:8000/nodes/status`.
2. Ensure every backend node exposes the expected model in its own `/v1/models`.
3. Register nodes with real reachable URLs using `/nodes/add` or `--proxy-url` during `api_server` startup.
4. Remove dead nodes with `/nodes/remove` or restart proxy with `--disable-cache-status` when stale cache is confusing.
5. Pick `--routing-strategy min_expected_latency` for general load-aware routing, `min_observed_latency` for observed latency routing, or `random` for simple distribution.

## Quick Diagnostic Sequence

```bash
lmdeploy serve api_server --help
lmdeploy serve proxy --help
python sub-skills/serving-apis/scripts/check_server_contract.py --help
python sub-skills/serving-apis/scripts/check_server_contract.py \
  --base-url http://127.0.0.1:23333 \
  --model lmdeploy-model
python sub-skills/serving-apis/scripts/check_server_contract.py \
  --base-url http://127.0.0.1:23333 \
  --model lmdeploy-model \
  --probe
```
