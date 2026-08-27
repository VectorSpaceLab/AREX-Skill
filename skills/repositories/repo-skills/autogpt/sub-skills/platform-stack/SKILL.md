---
name: platform-stack
description: "Operate and troubleshoot the self-hosted AutoGPT Platform stack,
  Docker services, environment files, migrations, and local LLM setup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Platform Stack

Use this sub-skill for AutoGPT Platform self-hosting, local development,
Docker Compose, environment-file initialization, service health, migrations,
ports, upgrades, and local OpenAI-compatible AutoPilot endpoints.

## Start here

- Read [workflows](references/workflows.md) for the normal setup, separate
  backend/frontend development, migrations, upgrades, and local LLM routes.
- Read [configuration](references/configuration.md) before editing `.env` files,
  changing ports, or switching auth/model transport.
- Read [troubleshooting](references/troubleshooting.md) before resetting data,
  diagnosing container restarts, or changing an existing installation.
- Run `python scripts/platform_stack_preflight.py --repo <checkout>` before
  starting services. Add `--init-env` only when missing local env files should
  be created without overwriting existing files.

## Safe operating sequence

1. Confirm whether the task is a fresh self-host, active local development,
   an upgrade, or a production-like deployment. Do not mix these paths.
2. From the repository's `autogpt_platform/` directory, verify Docker Compose,
   Node/Corepack, disk space, and the three expected default env files.
3. Initialize only missing `.env` files. Existing files must be diffed against
   current defaults; `cp -n` does not merge newly added variables.
4. Start the smallest service set that proves the next step. Use `make start-core`
   for Postgres, Redis, and RabbitMQ; use full Compose only when the UI or all
   services are required.
5. Apply migrations and generate Prisma artifacts before exercising backend
   features. Confirm `docker compose ps` and service logs before debugging UI
   symptoms.

## Common commands

```bash
cd autogpt_platform
make init-env
make start-core
make logs-core
make migrate
make run-backend
make run-frontend
# Full stack, when explicitly wanted:
docker compose up -d --build
docker compose ps
```

The normal local entry points are frontend `3000`, WebSocket `8001`, and REST
or execution API `8006`, but the active Compose/environment configuration wins.

## Routing boundaries

- Backend routes, blocks, Prisma, API schemas, and Python tests belong to
  [platform-backend](../platform-backend/SKILL.md).
- Next.js pages, generated hooks, Builder/Copilot UI, and browser tests belong
  to [platform-frontend](../platform-frontend/SKILL.md).
- Classic `autogpt`, Forge, and direct benchmark commands belong to
  [classic-agents](../classic-agents/SKILL.md).

Never make a Docker reset, database reset, credentialed provider call, model
pull, or full browser suite a default smoke check. Ask for explicit scope when
those side effects are part of the requested task.
