---
name: deployment-and-configuration
description: "Boot, configure, and operate Yuxi Docker, Lite, production, and
  service-topology workflows safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Deployment and Configuration

Load this sub-skill when the task is about starting, diagnosing, or safely
operating a Yuxi deployment rather than changing agent, knowledge-base, CLI, or
frontend code.

## Owns

- Docker Compose development, Lite, production, and optional OCR profile
  topology.
- `.env` / `.env.prod`, startup environment variables, administrator system
  options, model-provider credentials, CORS, reverse proxy, MinIO public assets,
  sandbox-provisioner, and OCR service configuration.
- Read-only runtime checks for an already started stack.
- Deployment troubleshooting, including logs, health endpoints, image pulls,
  service dependencies, and service-required verification candidates.

## Route elsewhere

- Agent run lifecycle, Skills/MCP/SubAgent behavior, streaming internals, and
  sandbox tool semantics: use the `agent-runtime` sub-skill after confirming the
  stack is healthy.
- Knowledge-base ingestion, parser behavior, OCR engine output, graph retrieval,
  or chunking details: use `knowledge-and-ocr` after confirming required
  services and credentials.
- `yuxi` CLI usage, external API/SSE client examples, and Langfuse evaluation
  commands: use `cli-and-external-integration` after confirming base URL and
  authentication assumptions.
- Repository editing, tests, lint, release, or changelog workflow: use
  `repo-development`.

## Safety gates

- Do not print, paste, commit, or summarize real `.env`, `.env.prod`, JWT,
  sandbox, database, MinIO, model-provider, API-key, OCR, or Langfuse secrets.
  Report only variable names and whether values are missing when necessary.
- Treat initialization, image-pull, reset, seed, and service restart commands as
  side-effectful. Run them only after explicit user approval and only in the
  intended deployment directory.
- Use `scripts/check-runtime-health.sh` for read-only checks. It does not start,
  stop, rebuild, seed, or edit configuration.
- Production API-key traffic must use HTTPS at the external boundary. Do not
  recommend sending `yxkey_...` tokens over plain HTTP except for local-only
  development.
- External model-provider connectivity, Langfuse tracing/evaluation, cloud OCR,
  and web search checks require credentials, network access, and explicit opt-in.
- GPU-backed OCR services (`mineru-api`, `paddlex`) are optional service profiles;
  do not represent them as core verified CPU capabilities.

## Fast operating workflow

1. Identify the deployment flavor:
   - Development: `docker-compose.yml`, web on `http://localhost:5173`, API on
     `http://localhost:5050`.
   - Lite: `make up-lite`, intended to skip heavy knowledge/graph services.
   - Production: `docker-compose.prod.yml`, web and API behind Nginx on port 80.
   - Optional OCR profile: `--profile all` adds MinerU and PaddleX services.
2. Check configuration readiness without exposing values. Use
   `references/configuration-and-secrets.md` for required variables and where
   each layer is read.
3. If a stack is already running, run the bundled read-only probe from a Yuxi
   deployment directory:

   ```bash
   # development stack
   scripts/check-runtime-health.sh --project-dir . --dev

   # production stack
   scripts/check-runtime-health.sh --project-dir . --prod
   ```

   If the script is copied outside the skill tree, keep its relative path local
   to the copied location and pass `--project-dir` to the deployment directory.
4. For failures, gather only bounded diagnostics:
   - `docker compose ps`
   - `docker compose logs --tail=100 api worker web sandbox-provisioner`
   - API health endpoint response from `/api/system/health`
   - Browser-visible web entrypoint status
5. Escalate to the routed sub-skill only after the relevant service health and
   credential gate is understood.

## References

- `references/runtime-topology.md` — service maps, Compose flavors, ports,
  Makefile entries, optional profiles, and native service-required candidates.
- `references/configuration-and-secrets.md` — startup env, administrator system
  options, model providers, CORS/proxy, MinIO, sandbox, OCR, API key, and
  Langfuse safety rules.
- `references/troubleshooting.md` — symptom-driven diagnosis and safe next
  commands.
- `scripts/check-runtime-health.sh` — read-only health/log probe for a running
  deployment.

## Native verification candidates

Use these only as verification candidates in an active Yuxi checkout or
service environment; this sub-skill remains self-contained for operating
context.

| Candidate | Requirement | Proves |
| --- | --- | --- |
| `docker-dev-runtime` | Docker Compose development stack; service-required | Compose health and container logs support dev deployment guidance. |
| `docker-prod-runtime` | Production Compose plus `.env.prod` secrets; service-required/reference-checked | Production topology, Nginx proxy path, and secret gates are understood. |
| `model-provider-connectivity` | Network and explicit provider credentials; optional/external | Real provider calls are only tested when the user enables them. |
| `ocr-config-center-e2e` | Running API/Postgres and authenticated user; optional/service-required | OCR configuration endpoints reflect runtime env/admin settings. |
