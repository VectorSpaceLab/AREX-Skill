---
name: taskingai
description: "Operate the TaskingAI self-hosted LLM BaaS platform, including
  deployment configuration, backend APIs, inference providers, plugin bundles,
  retrieval, assistant generation, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TaskingAI

Use this repo skill for TaskingAI tasks: self-hosting the multi-service stack, configuring backend/inference/plugin services, reasoning about TaskingAI backend API objects, provider/model schema catalogs, plugin bundles, retrieval/RAG objects, assistant generation, OpenAI-compatible endpoints, credentials, and service troubleshooting.

TaskingAI is a BaaS-style platform for LLM agent development and deployment. The source repo is a service monorepo, not a single importable Python package: the public stack contains a frontend console, backend API/web services, an inference microservice, a plugin microservice, Postgres/pgvector, Redis, and nginx.

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) before relying on this skill for a checkout refresh or stale-code decision.
2. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting import, Python-version, Docker, service-URL, credential, database, Redis, and storage failures.
3. Use the sub-skill route map below to load focused workflow details.
4. If a user supplies a TaskingAI checkout, run the bundled static helpers in [scripts/](scripts/) for safe route/catalog/env inspection before starting services.

## Sub-skill route map

| User task | Load |
| --- | --- |
| Self-host TaskingAI, inspect Docker Compose topology, audit `.env`, diagnose nginx/ports/health checks, choose local vs S3 storage, or wire service URLs | [deployment-configuration](sub-skills/deployment-configuration/SKILL.md) |
| Work with backend REST objects, `/v1` or `/api/v1` route families, API keys/admin auth, assistants/chats/messages, retrieval collections/records/chunks, model/tool/action objects, OpenAI-compatible backend endpoints, file/image uploads, or backend tests | [backend-api](sub-skills/backend-api/SKILL.md) |
| Work with inference providers, provider/model schemas, `chat_completion`, `text_embedding`, `rerank`, wildcard/custom-host models, local providers such as Ollama/LM Studio/LocalAI, credential verification, provider icons, proxy/URL blacklist behavior, or provider errors | [inference-providers](sub-skills/inference-providers/SKILL.md) |
| Work with plugin bundles, built-in tool schemas, plugin execution payloads, no-credential tools such as arithmetic/calculator, generated image storage, bundle credential validation, or plugin service failures | [plugin-bundles](sub-skills/plugin-bundles/SKILL.md) |

## Safe static helpers

These scripts are bundled with the skill and are safe by default. They read user-supplied files or source trees; they do not start Docker, import TaskingAI modules, call providers, read credentials, or mutate services.

- [scripts/check_taskingai_env.py](scripts/check_taskingai_env.py): validate dotenv-style TaskingAI environment variables for Compose, backend API/web, inference, or plugin profiles.
- [scripts/summarize_taskingai_routes.py](scripts/summarize_taskingai_routes.py): statically list FastAPI route decorators for backend, inference, and plugin services in a TaskingAI checkout.
- [scripts/inspect_taskingai_catalogs.py](scripts/inspect_taskingai_catalogs.py): statically summarize inference provider/model schemas and plugin bundle/plugin catalogs.

Example static checks for a user-provided checkout:

```bash
python scripts/check_taskingai_env.py --env-file ./docker/.env --profile compose
python scripts/summarize_taskingai_routes.py --repo-root ./TaskingAI --service backend
python scripts/inspect_taskingai_catalogs.py --repo-root ./TaskingAI
```

## Installation and runtime stance

- For ordinary self-hosting, prefer the documented Docker Compose path: configure an env file, then start the stack only when the user authorizes Docker image pulls, service startup, port binding, and persistent volumes.
- For service source inspection or backend development, use Python 3.10. The verified backend dependency set includes `aioredis==2.0.1`, which fails on Python 3.11 with a duplicate `TimeoutError` base-class import error.
- Do not treat `pip install taskingai` as installing this service repo. The README's `taskingai` Python package is the client SDK used against a running server.
- Inference/provider and plugin execution often require real credentials, network access, provider quotas, object storage, and running services. Use static checks first; run credentialed or service-native tests only after explicit authorization.

## Common decision points

- **Backend API vs web mode:** API mode uses `/v1`; web-console mode uses `/api/v1` plus admin/web routes. Do not mix route prefixes with the wrong auth mode.
- **Backend orchestration vs delegated services:** backend generation orchestrates retrieval, tools, and model calls, but provider-specific behavior lives in the inference service and bundle-specific behavior lives in the plugin service.
- **Local vs S3 storage:** local storage depends on `HOST_URL` and writable volume paths; S3 depends on endpoint, bucket, access keys, and public-domain behavior. See deployment and plugin troubleshooting before blaming generated URLs.
- **Provider errors:** distinguish local request/schema/proxy validation (`REQUEST_VALIDATION_ERROR`) from upstream provider/auth/quota/network failures (`PROVIDER_ERROR`).
- **No-credential plugin smoke tasks:** prefer arithmetic or calculator-style bundles for synthetic tool checks; image/chart plugins require storage configuration even when they do not require provider credentials.

## What this skill does not cover

- Deep frontend React component development.
- Generic FastAPI, Docker, Postgres, Redis, S3, or provider-SDK tasks that do not involve TaskingAI semantics.
- Running broad native tests, Docker Compose, provider calls, or storage integration without user approval and a suitable environment.
