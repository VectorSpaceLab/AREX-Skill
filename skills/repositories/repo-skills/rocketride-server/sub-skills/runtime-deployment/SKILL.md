---
name: runtime-deployment
description: "Start, self-host, debug, and deploy RocketRide runtime and engine."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Runtime Deployment

Use this sub-skill when a task is about starting a RocketRide engine, choosing
Cloud versus self-hosting, checking runtime connectivity, explaining the native
WebSocket/DAP protocol, or deploying the engine with a release archive, source
build, Docker Compose, or Helm.

## Use this for

- Starting a local or on-prem RocketRide engine on port `5565`
- Choosing the right client URI for Cloud, a local binary, Docker, or Kubernetes
- Debugging `/ping`, `/task/service`, WebSocket upgrades, auth, and task events
- Explaining which SDK calls map to which DAP-style runtime commands
- Planning release-archive, source-build, Docker Compose, or Helm deployments
- Reasoning about observability events, trace levels, and runtime metrics
- Placing provider API keys, database credentials, and vector-store settings in
  the engine environment without hardcoding secrets in `.pipe` files

## Do not use for

- Python or TypeScript SDK method details and code examples → `../sdk-clients/`
- `.pipe` design, lane wiring, or pipeline recipes → `../pipeline-authoring/`
- Node provider schemas and generated node docs → `../nodes-catalog/`
- VS Code extension/runtime UX and visual app surfaces → `../ide-and-apps/`
- MCP server, n8n, assistant-tool, or webhook integration details → `../mcp-and-integrations/`

## Route first

- Read [self-hosting and protocol](references/self-hosting-and-protocol.md) for
  release archives, source builds, Linux runtime dependencies, the `engine`
  command, Cloud/local URI rules, `/ping`, `/task/service`, DAP frames, SDK-to-
  command mapping, auth, and observability.
- Read [Docker and Helm](references/docker-helm.md) for Compose services, host
  versus container networking, Kubernetes values, secrets, external databases,
  GPU scheduling, HA, probes, and deployment validation.
- Read [troubleshooting](references/troubleshooting.md) when a runtime does not
  listen, a client cannot connect, auth fails, observability is silent, Docker
  networking is wrong, Helm rendering/deployment fails, or provider credentials
  are missing.

## Safety and execution guardrails

- Do not start long-running engines, Docker stacks, Kubernetes deployments, or
  source builds unless the user explicitly asks for that action and accepts the
  local side effects.
- Prefer static review and command planning when the user only asks what to run.
- Never test real provider credentials or Cloud tokens unless the user supplies
  them for that purpose.
- Treat source builds, Docker, Helm, GPU, database, and external-provider paths
  as optional deployment workflows, not required smoke checks for ordinary skill
  use.

## Quick triage order

1. Identify target: Cloud, release archive, source-built runtime directory,
   Docker Compose, or Helm.
2. Check the expected endpoint:
   - Health: `http://<host>:5565/ping`
   - Task socket: `ws://<host>:5565/task/service`
   - Cloud base URI: `https://api.rocketride.ai` with token auth
3. Verify whether the problem is a listening/binding issue, URI/scheme issue,
   authentication issue, proxy/WebSocket-upgrade issue, or provider/runtime
   dependency issue.
4. Use runtime events only for live observation: RocketRide observability is a
   WebSocket event stream, not a durable metrics database.

## Good output for deployment tasks

- Names the target mode and exact endpoint scheme
- Shows a health check and expected signal
- Separates local auth assumptions from Cloud/production auth requirements
- Keeps provider secrets in environment variables or Kubernetes Secrets
- Notes when a command is heavy or starts services
- Includes rollback/stop or dry-run guidance for Docker and Helm
