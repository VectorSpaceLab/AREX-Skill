---
name: proxy-server
description: "Operate OptiLLM as an OpenAI-compatible proxy server, including
  provider selection, API routes, CLI flags, SSL, auth, batching, streaming, and
  Docker deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OptiLLM Proxy Server

Use this sub-skill when the task is to start, call, configure, secure, deploy, or debug the OptiLLM OpenAI-compatible HTTP proxy.

## Read first for these tasks

- Start OptiLLM with OpenAI, Cerebras, Azure OpenAI, LiteLLM, an OpenAI-compatible base URL, or built-in local inference.
- Build client requests for `/v1/chat/completions`, `/v1/models`, or `/health`.
- Configure server auth, provider auth, SSL certificates, host/port, logging, batching, streaming, or multiple completions.
- Diagnose request parsing, approach prefix selection, response shape, `n`, or provider pass-through behavior.
- Choose Docker or source checkout execution paths.

Route approach selection and algorithm tuning to [../optimization-approaches/SKILL.md](../optimization-approaches/SKILL.md). Route plugin-specific setup to [../plugins-and-tools/SKILL.md](../plugins-and-tools/SKILL.md). Route built-in HuggingFace/LoRA/decoding backends to [../local-inference-decoding/SKILL.md](../local-inference-decoding/SKILL.md).

## Core workflow

1. **Choose provider path.** Check whether the user wants external routing or local inference. `OPTILLM_API_KEY` activates local inference; `OPENAI_API_KEY`, `CEREBRAS_API_KEY`, or `AZURE_*` route to external clients.
2. **Start server safely.** Keep default `127.0.0.1` unless the user intentionally exposes the service. Add server auth before binding to external interfaces.
3. **Pick approach mode.** Use `--approach auto` when callers will use model prefixes, request body `optillm_approach`, or prompt tags.
4. **Call via OpenAI-compatible client.** Base URL must end in `/v1` for the OpenAI SDK.
5. **Validate response shape.** For direct `none`, OptiLLM passes through provider responses; for approaches it wraps text into OpenAI-compatible choices and usage metadata.
6. **Escalate to troubleshooting.** Read [references/troubleshooting.md](references/troubleshooting.md) for auth, SSL, provider, batching, and streaming issues.

## Minimal commands

External OpenAI-compatible endpoint:

```bash
export OPENAI_API_KEY="sk-or-placeholder"
optillm --approach auto --model gpt-4o-mini --base-url http://localhost:8080/v1
```

Default OpenAI provider:

```bash
export OPENAI_API_KEY="sk-..."
optillm --approach auto --model gpt-4o-mini
```

Local inference path:

```bash
export OPTILLM_API_KEY=optillm
optillm --model meta-llama/Llama-3.2-1B-Instruct
```

Client call:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="anything")
response = client.chat.completions.create(
    model="moa-gpt-4o-mini",
    messages=[{"role": "user", "content": "Solve this."}],
)
```

## Bundled references and scripts

- [references/server-workflows.md](references/server-workflows.md) gives end-to-end server, client, Docker, and approach-selection workflows.
- [references/api-and-cli.md](references/api-and-cli.md) catalogs routes, request fields, CLI flags, environment variables, and response behavior.
- [references/troubleshooting.md](references/troubleshooting.md) maps observable server/API failures to concrete recovery steps.
- Run `python scripts/proxy_smoke_client.py --help` to build dry-run request payloads or send an explicit opt-in smoke request.

## Decision points

- **Provider supports `n`?** If not, avoid methods that depend on multiple completions or use approaches that make sequential calls themselves.
- **Need server auth?** Use `--optillm-api-key`; remember `/health` remains unauthenticated by design.
- **Corporate/self-signed TLS?** Prefer `--ssl-cert-path` over `--no-ssl-verify`.
- **Streaming?** OptiLLM converts final approach responses into SSE chunks; do not expect identical chunking to the upstream provider.
- **Batch mode?** Use only for non-streaming compatible requests. It is fail-fast when requests differ in model, approaches, operation, or stream mode.

## Validation checklist

- `optillm --version` prints a package version.
- `GET /health` returns `{"status": "ok"}`.
- The client base URL includes `/v1`.
- The selected approach and base model appear correctly in logs or parse output.
- Provider credentials are present only in environment variables or client auth headers, not in logs or committed config.
