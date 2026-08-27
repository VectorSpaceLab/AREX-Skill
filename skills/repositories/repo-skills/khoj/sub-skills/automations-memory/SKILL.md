---
name: automations-memory
description: "Use and troubleshoot Khoj scheduled automations, cron
  normalization, scheduler leadership, and user memories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Khoj Automations and Memory

Use this sub-skill when working on Khoj scheduled automations, `/api/automation`, `/api/memories`, cron normalization, background scheduler leadership, user memory settings, or memory scoping by user and agent.

## Route Map

- Use [automations-api.md](references/automations-api.md) for `/api/automation` CRUD, manual trigger behavior, required parameters, cron normalization, response metadata, and `/automated_task` query prefixing.
- Use [memory-api.md](references/memory-api.md) for `/api/memories` behavior, update-as-delete-and-recreate semantics, memory settings, and user/agent scoping rules.
- Use [scheduler-runtime.md](references/scheduler-runtime.md) for APScheduler, `DjangoJobStore`, process-lock scheduler leadership, timezone handling, and asynchronous trigger execution.
- Use [troubleshooting.md](references/troubleshooting.md) for invalid cron strings, minute-level recurrence rejection, duplicate automations, missing conversations, scheduler leader conflicts, missing memories, and disabled or mis-scoped memory.
- Use [validate_cron.py](scripts/validate_cron.py) to safely validate and normalize Khoj-style cron strings without starting the server or touching a database.

## Boundaries

- This sub-skill owns scheduled automation APIs, cron normalization, automation runtime scheduling, scheduler leader behavior, memory APIs, memory settings, and memory user/agent scoping.
- Route ordinary chat payload construction, slash-command response generation, model selection, and chat agent behavior to `chat-agents`.
- Route server startup, database migrations, deployment, authentication setup, Docker, and general REST route orientation to `deployment-api`.
- Route search, content retrieval, indexing, file filters, embeddings, and reranking to `search-retrieval` or `content-indexing`.

## Evidence Basis

This guidance is distilled from Khoj source, docs, and tests for automation routing, memory routing, scheduler setup, process locks, memory settings, and scheduled-chat actor behavior. It is self-contained for future coding agents and does not require reading original repository files at runtime.
