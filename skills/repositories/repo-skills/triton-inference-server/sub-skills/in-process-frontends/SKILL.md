---
name: in-process-frontends
description: "Use Triton Python packages `tritonserver` and `tritonfrontend` to
  embed Triton and expose KServe or metrics services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# In-Process Frontends

Use this sub-skill when the user wants to run Triton in Python, inspect `tritonserver`/`tritonfrontend` APIs, start KServe HTTP/gRPC services from Python, or debug import/lifecycle problems in the embedded runtime.

## Route Within This Sub-skill

- **Package roles, `KServeHttp`, `KServeGrpc`, `Metrics`, defaults, lifecycle, and option objects**: read [`references/api-reference.md`](references/api-reference.md).
- **Embedding patterns, start/stop order, context-manager usage, and supported/unsupported service surfaces**: read [`references/workflows.md`](references/workflows.md).
- **Import errors, native library mismatch, service shutdown order, and option validation problems**: read [`references/troubleshooting.md`](references/troubleshooting.md).
- **Option-inspection helper**: run [`scripts/inspect_frontend_options.py`](scripts/inspect_frontend_options.py).

If the user wants a server container launch plan, route to [`../server-runtime-and-deployment/SKILL.md`](../server-runtime-and-deployment/SKILL.md). If the user wants an OpenAI-compatible FastAPI frontend, route to [`../openai-llm-frontend/SKILL.md`](../openai-llm-frontend/SKILL.md).

## Safe Default Workflow

1. Confirm the installed Triton Python packages and runtime library alignment.
2. Inspect the default option objects before embedding anything into an application.
3. Start the Triton server first, then start HTTP/gRPC/metrics services, and stop them in reverse order.
4. Use the context-manager pattern when the workflow is short and the server is already configured.
5. Treat an import success as API availability only, not proof of a live model load or inference path.
