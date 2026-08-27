---
name: serving-apis
description: "Serve LMDeploy models through OpenAI-compatible,
  Responses-compatible, Anthropic-compatible, proxy, and client integration
  APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving APIs

Use this sub-skill when the task is to expose an LMDeploy model as a network service or connect an OpenAI/Responses/Anthropic-style client to that service.

## Route Here

- Build `lmdeploy serve api_server` commands, including `--server-name`, `--server-port`, `--model-name`, `--backend`, `--tp`, cache/session flags, `--api-keys`, `--ssl`, docs, and parser flags.
- Operate `lmdeploy serve proxy` for multiple `api_server` nodes and route OpenAI-compatible traffic through the proxy.
- Call `/v1/models`, `/v1/chat/completions`, `/v1/completions`, `/v1/responses`, `/v1/messages`, and `/v1/messages/count_tokens`.
- Use `lmdeploy.serve.openai.api_client.APIClient`, the OpenAI Python SDK, Codex Responses integration, Claude Code Anthropic integration, or `curl`.
- Configure `--tool-call-parser` and `--reasoning-parser` for tool-call and reasoning output extraction.

## Route Elsewhere

- Offline local text inference belongs in `pipeline-inference`.
- Multimodal message/image/video payload details belong in `vision-language`.
- Creating AWQ/GPTQ/SmoothQuant/other quantized artifacts belongs in `quantization`.
- Deep backend performance tuning, new-model support, kernel behavior, or backend config internals belong in `backend-extension`.

## Quick Start

```bash
lmdeploy serve api_server <model-or-path> \
  --backend pytorch \
  --server-name 0.0.0.0 \
  --server-port 23333 \
  --model-name lmdeploy-model \
  --tp 1
```

Validate the exposed model and chat endpoint:

```bash
curl http://127.0.0.1:23333/v1/models
curl http://127.0.0.1:23333/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{"model":"lmdeploy-model","messages":[{"role":"user","content":"Reply with pong"}],"max_tokens":32}'
```

If launched with `--api-keys my-secret`, add `-H "Authorization: Bearer my-secret"` to client requests.

## References

- `references/cli-reference.md`: command construction for `api_server` and `proxy`.
- `references/api-reference.md`: endpoint contracts and request/response notes.
- `references/client-integration.md`: `APIClient`, OpenAI SDK, Codex, Claude Code, and validation curls.
- `references/troubleshooting.md`: symptoms, causes, and recovery steps.
- `scripts/check_server_contract.py`: offline/optional-live contract checker for base URLs and endpoint shape.

## Validation Pattern

1. Run `lmdeploy serve api_server --help` and `lmdeploy serve proxy --help` to verify installed CLI flags.
2. Start `api_server` with an explicit `--model-name` and any needed parser/auth flags.
3. Run `python scripts/check_server_contract.py --base-url http://127.0.0.1:23333 --model <model-name>` for offline request preview.
4. Add `--probe` to perform live `/v1/models`, chat, completions, Responses, and Anthropic contract probes.
