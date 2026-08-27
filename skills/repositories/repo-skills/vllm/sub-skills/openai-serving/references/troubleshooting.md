# OpenAI Serving Troubleshooting

Use this page to map symptoms to checks and fixes. Do not assume GPU/server execution is available in the agent environment; ask the user to run hardware-gated commands when model loading is required.

## Fast triage sequence

1. Is the server process running and still logging after model load?
2. Does `curl -f http://HOST:PORT/health` return success?
3. Does `curl http://HOST:PORT/v1/models` return the expected model list?
4. Does the client `base_url` end in `/v1`?
5. Does the client `model` exactly match a returned `data[].id`?
6. If `--api-key` was used, does the client send `Authorization: Bearer TOKEN` with a matching token?
7. Does the failing payload match the endpoint schema and task supported by the served model?

## Symptoms and fixes

| Symptom | Likely cause | Check | Fix |
| --- | --- | --- | --- |
| `Connection refused` | Server is not running, still loading, crashed, wrong host/port, or blocked port. | `curl -v http://HOST:PORT/health`; inspect server logs. | Start/restart `vllm serve`; wait for startup; correct host/port; free the port. |
| 404 from OpenAI client | Base URL missing `/v1`, reverse proxy root path mismatch, or unsupported route. | Print `client.base_url`; curl `/v1/models`. | Use `base_url="http://HOST:PORT/v1"`; set/proxy `--root-path` consistently. |
| 404 model not found | Request `model` does not match served ID or adapter alias. | `curl http://HOST:PORT/v1/models`. | Use an exact `data[].id`; configure served aliases intentionally. |
| 401/403 auth error | Token missing or mismatched. | Compare server `--api-key` with client key source. | Set OpenAI `api_key` or `Authorization: Bearer ...`; remove server auth for local unauthenticated tests. |
| Browser CORS failure | Origin, methods, headers, or credentials not allowed. | Browser devtools preflight response. | Start with JSON CORS flags such as `--allowed-origins '["https://app.example.com"]'`. |
| Port already in use | Existing process occupies port. | `lsof -i :8000` or OS equivalent. | Stop old process or choose `--port 8001`. |
| Client hangs on first request | Model still loading, GPU memory pressure, long prompt, or streaming not consumed. | Server logs; try `/health` and `/v1/models`; send `max_tokens: 1`. | Wait for load; reduce context/model size; route capacity tuning to `../deployment-performance/SKILL.md`. |
| 422/request validation error | Wrong JSON shape for endpoint. | Read error body parameter; compare endpoint examples. | Use `messages` for chat, `prompt` for completions, `input` for responses, JSONL envelope for `run-batch`. |
| Streaming prints objects not text | Client loop is printing chunks directly. | Inspect stream iteration code. | Print `chunk.choices[0].delta.content` for chat or `chunk.choices[0].text` for completions. |
| `run-batch` rejects line | JSONL row missing `custom_id`, `method`, `url`, or `body`; unsupported URL. | Validate one line with `python -m json.tool`. | Use OpenAI Batch-style JSONL and supported URL families. |
| GPU/Triton/runtime unavailable | CPU-only install or hardware/backend not present. | Import/runtime warnings; server load failure. | Install a backend-matched vLLM build and verify drivers; route performance/hardware planning to `../deployment-performance/SKILL.md`. |

## Server logs to request from users

Ask for the smallest useful excerpt:

- The full `vllm serve ...` command with secrets redacted.
- Startup lines showing model name, port, dtype, tensor/data parallel settings, and errors.
- The first stack trace or validation error after the failing request.
- The exact HTTP status and JSON error body from the client.

Do not ask users to paste API keys. Replace tokens with placeholders such as `sk-...redacted`.

## Base URL and model mismatch diagnostic

Run these from the client machine:

```bash
curl -sS http://localhost:8000/v1/models
```

Then in Python:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
print([model.id for model in client.models.list().data])
```

If the model list works but generation fails with model not found, change only the generation `model` string to one of the printed IDs before changing server flags.

## Request shape diagnostics

Chat completions require:

```json
{"model":"MODEL","messages":[{"role":"user","content":"hello"}]}
```

Completions require:

```json
{"model":"MODEL","prompt":"hello"}
```

Responses require:

```json
{"model":"MODEL","input":"hello"}
```

`run-batch` JSONL requires one object per line:

```json
{"custom_id":"req-1","method":"POST","url":"/v1/chat/completions","body":{"model":"MODEL","messages":[{"role":"user","content":"hello"}]}}
```

Endpoint-specific payloads for embeddings, score, rerank, multimodal, audio, and LoRA should be routed to `../modalities-adapters-pooling/SKILL.md`.

## Structured outputs and tools routing

This sub-skill can confirm that structured-output fields belong in the request and that the server route is correct. Route the detailed design to `../structured-tool-reasoning/SKILL.md` when the user needs:

- `response_format` JSON schema, JSON object, regex, or structural tags.
- `structured_outputs` parameters.
- Tool definitions, `tool_choice`, auto tool parsing, or parser plugin flags.
- Responses API tool/stateful behavior beyond basic request transport.

Serving ownership remains: `vllm serve` command, `/v1` base URL, model ID discovery, auth, and request transport.

## Safe bundled script use

`../scripts/openai_client_smoke.py --mode models --no-request-plan` only plans/prints by default and does not require a live server. Remove `--no-request-plan` or use `--mode chat`/`completion` only when the user has a server running.

`../scripts/serve_command_builder.py` prints a command; it does not validate GPU memory or download models. Treat the printed command as a starting point and validate with `vllm serve --help` in the user's installed version.
