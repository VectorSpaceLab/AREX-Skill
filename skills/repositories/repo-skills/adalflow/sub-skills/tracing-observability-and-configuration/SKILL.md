---
name: tracing-observability-and-configuration
description: "Route AdalFlow setup, logging, tracing, MLflow, and debug-artifact workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tracing, Observability, and Configuration

Use this sub-skill when a task needs any of the following:

- `.env` loading and runtime bootstrap with `setup_env`
- logging helpers such as `get_logger` and `printc`
- generator state or call logs, including the tracing decorators
- trace providers, spans, and local callback ordering for debugging
- optional MLflow tracing setup and local troubleshooting
- config-file driven observability settings and artifact hygiene

Do **not** use this sub-skill for:

- evaluation metrics or optimization workflows
- agent streaming semantics or runner event plumbing
- provider-specific `model_kwargs`, prompt shaping, or generator behavior

Start here:

- [Tracing and config notes](references/tracing-and-config.md)
- [Verified API reference](references/api-reference.md)
- [Troubleshooting guide](references/troubleshooting.md)
- [Bundled smoke script](scripts/tracing_smoke.py)

Practical routing hints:

- Use the environment and logging helpers first when traces are missing or noisy.
- Use generator state and call loggers when you need prompt history or failed-call artifacts.
- Use `trace(...)` and nested spans when you need structured execution evidence.
- Use the bundled smoke script when you need a safe, service-free sanity check.
