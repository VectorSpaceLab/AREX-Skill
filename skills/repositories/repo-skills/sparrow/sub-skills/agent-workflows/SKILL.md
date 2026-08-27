---
name: agent-workflows
description: "Operate Sparrow Agents FastAPI endpoints, async queues, built-in
  workflow agents, client configuration, payload validation, and
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Agent Workflows

Use this sub-skill when a task involves Sparrow Agents workflow operation: FastAPI sync/async execution endpoints, Prefect-wrapped agent flows, Celery/Redis task polling or cancellation, built-in `medical_prescriptions`, `trading`, and `bonds` agents, agent-side Sparrow API clients, and request payload validation.

Do not use this sub-skill for base document extraction backend selection or Sparrow Parse payloads; route those tasks to [document-extraction](../document-extraction/SKILL.md). Do not use it for Sparrow LLM API engine or CLI operation; route those tasks to [api-engine-and-cli](../api-engine-and-cli/SKILL.md). Do not use it for web UI deployment or dashboard behavior; route those tasks to [ui-and-deployment](../ui-and-deployment/SKILL.md).

## Read first

- [Agents API](references/agents-api.md) for `/execute/data`, `/execute/data/async`, `/execute/file`, `/execute/file/async`, task status, cancellation, agent listing, health, response shapes, and curl patterns.
- [Built-in agents](references/built-in-agents.md) for accepted agent names, file versus data inputs, trading payload rules, medical PDF constraints, and cached bond search usage.
- [Configuration](references/configuration.md) for agent config keys, backend URLs, model option strings, Redis/Celery settings, and async service prerequisites.
- [Troubleshooting](references/troubleshooting.md) for unknown agents, malformed form JSON, missing Sparrow key, Tavily avoidance, Redis/Celery issues, polling states, and cancellation semantics.
- [Payload smoke script](scripts/agent_payload_smoke.py) for local schema checks without starting FastAPI, Prefect, Redis, Celery, Tavily, or Sparrow LLM services.

## Safe operating sequence

1. Confirm whether the task is agent orchestration rather than base extraction, LLM API/CLI, or UI deployment.
2. Confirm the live Sparrow Agents base URL and port; examples usually use `/api/v1/sparrow-agents` under a local FastAPI server, but deployments may choose a different port.
3. Probe `/api/v1/sparrow-agents/health` and `/api/v1/sparrow-agents/agents` before sending workflow jobs.
4. Validate the request shape with `python scripts/agent_payload_smoke.py --case all` or with a custom payload file.
5. Use synchronous endpoints only for quick jobs. Use async endpoints only when Redis and a Celery worker are running and the selected agent is registered in the worker process.
6. For `bonds`, prefer a cached search results payload when credentials or networked Tavily search should be avoided.

## Boundaries and guarantees

This sub-skill distills runtime behavior and payload contracts into self-contained operating guidance. The smoke script checks schemas only; it does not start services, call external credentials, launch Prefect/Celery, or validate model quality. Base document extraction backends and Sparrow LLM inference internals remain owned by their routed sub-skills.
