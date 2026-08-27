---
name: agent-runtime
description: "Implement/debug Yuxi agent runtime, APIs, tools, skills, MCP,
  subagents, queue, streaming, and middleware behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Yuxi Agent Runtime

Use this sub-skill when the task touches Yuxi's LangGraph/FastAPI agent execution path: agent configuration and context, run submission, request queue and steer behavior, worker/SSE streaming, middleware, attachments, built-in tools, Skills, MCP, subagents, sandbox file boundaries, API-key access, or Langfuse/evaluation runtime hooks.

Do not use it as the primary guide for deployment topology, knowledge-base ingestion internals, OCR engine selection, CLI usage, or general repo development; route those to the sibling sub-skills and use this one only for the agent-facing boundary.

## First decisions

1. **Classify the failing layer.** Use `references/agent-runtime-map.md` to decide whether the change belongs in context/config, request intake and queueing, run execution, stream serialization, middleware, sandbox/files, tools/Skills/MCP, or subagents.
2. **Apply safety gates before probing.** API keys, provider keys, Langfuse keys, MCP endpoints, remote Skill sources, Tavily, non-local OCR, and live model calls are service/credential gated. Do not print secrets or run side-effectful external calls without explicit approval.
3. **Prefer CPU-safe unit proofs first.** Most runtime contracts are covered by backend unit tests. E2E stream/subagent/personal-Skill checks require a running Docker Compose stack and sometimes admin credentials.
4. **Keep HTTP routes thin.** Route code should validate request/auth/response shape and delegate stateful behavior to services/repositories.

## Quick route map

- **Agent definition/config:** inspect BaseAgent/BaseContext/ChatBotContext/SubAgentContext, Agent repository serialization, and `config_json.context` normalization.
- **Run submission and queue:** start at `POST /api/agent/runs`, `RunSubmissionCommand`, and the request queue service for `enqueue`, `reject`, and `steer` semantics.
- **Worker execution and streaming:** follow AgentRun creation, ARQ enqueue, `stream_agent_chat`/resume, Redis stream events, and `/api/agent/runs/{run_id}/events` SSE serialization.
- **Middleware behavior:** inspect the built-in Chatbot/SubAgent graph assembly, then the specific middleware in question: filesystem, attachments, Skills, subagent task tools, summary/offload, image-input compatibility, token usage, model retry, or tool approval.
- **Tools, Skills, MCP, subagents:** use `references/tools-skills-mcp-subagents.md` for activation, gating, storage, async subagent lifecycle, and sandbox boundaries.
- **Known failure modes:** use `references/troubleshooting.md` before making broad changes.

## Safe command entry points

Run commands from the repository root. Docker Compose is the canonical development runtime.

```bash
# Non-mutating service/log probes
docker compose ps
docker logs api-dev --tail 100
docker logs worker-dev --tail 100
docker logs sandbox-provisioner --tail 100
curl -s http://localhost:5050/api/system/health
curl -s http://localhost:8002/health

# CPU-safe unit coverage for this sub-skill
docker compose exec api uv run --group test pytest \
  test/unit/routers/test_skill_router.py \
  test/unit/services/test_skill_service.py \
  test/unit/backends/test_sandbox_backends.py \
  test/unit/services/test_agent_request_queue_service.py \
  test/unit/middlewares/test_steer_middleware.py \
  test/unit/middlewares/test_subagent_task_middleware.py \
  test/unit/services/test_subagent_run_service.py \
  test/unit/routers/test_mcp_router.py \
  test/unit/services/test_mcp_service.py \
  test/unit/toolkits/test_install_skill.py
```

Only run the E2E candidates when the stack is intentionally running and test credentials are available:

```bash
docker compose exec api uv run --group test pytest -m e2e \
  test/e2e/test_subagent_stream_e2e.py \
  test/e2e/test_personal_skill_agent_e2e.py
```

## Native proof candidates

- Required CPU/any: skill router, skill service, sandbox backend/path rules, request queue/steer service, subagent middleware/service, MCP router/service, and `install_skill` unit tests.
- Optional service-required: subagent streaming E2E and personal Skill agent E2E. These require Docker Compose services and should not be treated as proof when services, admin user, worker, Redis/Postgres, MinIO, or sandbox-provisioner are unavailable.
- Optional external credentials: API-key/SSE examples, live model provider calls, Langfuse/evaluation, Tavily search, remote MCP, and remote Skill installs.

## Reference files

- `references/agent-runtime-map.md` — execution architecture, layer ownership, APIs, middleware, streaming, tests, and backend gates.
- `references/tools-skills-mcp-subagents.md` — tool registry, built-in/KB tools, Skill install/activation/storage, MCP integration, subagent lifecycle, and sandbox file semantics.
- `references/troubleshooting.md` — targeted symptoms, probes, fixes, safety boundaries, and test selection.
