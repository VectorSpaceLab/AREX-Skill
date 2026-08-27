---
name: cli-and-services
description: "Use Agent Lightning agl CLI commands, store and Prometheus
  services, LLMProxy/vLLM service patterns, metrics, and safe endpoint checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLI and services

Use this sub-skill when the user asks about `agl` commands, store servers, Prometheus metrics, LLM proxying, vLLM integration, OpenAI-compatible endpoint checks, or service startup failures.

## Route by task

| Request | Read/run |
| --- | --- |
| Check `agl`, `agl store`, or `agl prometheus` flags | [references/cli-reference.md](references/cli-reference.md) |
| Start or connect to a LightningStore service | [references/service-workflows.md](references/service-workflows.md#store-service) |
| Use LLMProxy with OpenAI-compatible/vLLM endpoints | [references/service-workflows.md](references/service-workflows.md#llm-proxy) |
| Check a LiteLLM/OpenAI-compatible proxy safely | `python scripts/check_litellm_proxy.py --base-url ... --model ...` |
| Emit local demo metrics or check Prometheus dependencies | `python scripts/check_prometheus_metrics.py --duration 1 --host 127.0.0.1` |
| Debug CLI/service failures | [references/troubleshooting.md](references/troubleshooting.md) |

## Key rules

- Always run `agl --help` and subcommand `--help` before relying on remembered flags.
- `agl store` supports in-memory and optional Mongo backends.
- `agl prometheus` requires Prometheus client support and `PROMETHEUS_MULTIPROC_DIR` when starting the exporter.
- `agl vllm` imports vLLM and is optional; expect it to fail in CPU/base environments without vLLM.
- `LLMProxy` wraps LiteLLM and can route `/rollout/<id>/attempt/<id>/v1/...` requests so spans are attributed to the correct attempt.
- Do not print API keys. Endpoint checkers should show model IDs and status, not secrets.

## Safe checks

```bash
agl --help
agl store --help
agl prometheus --help
python scripts/check_litellm_proxy.py --help
python scripts/check_prometheus_metrics.py --duration 1 --host 127.0.0.1
```

The LiteLLM proxy checker makes network requests only when `--base-url` and `--model` are explicitly supplied. The metrics checker binds localhost by default in examples and exits quickly.

## Boundary

This sub-skill owns command syntax and service surfaces. For rollout status semantics use [runner-store-training](../runner-store-training/SKILL.md). For interpreting spans or token IDs use [tracing-and-instrumentation](../tracing-and-instrumentation/SKILL.md). For optional example selection use [examples-and-recipes](../examples-and-recipes/SKILL.md).
