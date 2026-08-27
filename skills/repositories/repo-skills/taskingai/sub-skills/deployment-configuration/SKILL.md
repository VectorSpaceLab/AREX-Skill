---
name: deployment-configuration
description: "Operate TaskingAI self-hosted deployment topology, environment
  configuration, storage choices, health checks, and deployment
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deployment-configuration

Use this sub-skill when the task is to self-host, inspect, configure, or troubleshoot a TaskingAI deployment rather than to reason about TaskingAI business objects or provider/plugin schemas.

## Read when

- A user is starting, upgrading, or diagnosing a self-hosted TaskingAI stack.
- The task mentions Docker Compose, service roles, ports, health checks, nginx routing, image tags, or version skew.
- The task asks whether environment variables are sufficient, especially `TASKINGAI_INFERENCE_URL`, `TASKINGAI_PLUGIN_URL`, `OBJECT_STORAGE_TYPE`, local storage, or S3 storage.
- The console is deployed but cannot reach API routes, generated files, provider icons, plugin icons, inference, plugin execution, Postgres, or Redis.

## Route elsewhere

- Backend object models, REST object semantics, authentication flows, assistant/retrieval/tool/model APIs, database models, and request/response bodies belong to `../backend-api/`.
- Provider/model catalogs, provider credentials, model schema details, credential validation behavior, and provider execution belong to `../inference-providers/`.
- Plugin bundle catalogs, plugin execution semantics, plugin bundle storage details beyond deployment-level storage selection, and bundle-specific failures belong to `../plugin-bundles/`.
- Deep React/frontend implementation is out of scope; the console is treated here only as a deployed service behind nginx.

## Operating pattern

1. Identify the deployment shape: full Compose stack, standalone microservices for development, or a user-modified deployment.
2. Map service reachability before changing application settings: external `HOST_URL`, nginx public port, internal service DNS names or host ports, and health-check paths.
3. Audit the environment against [configuration](references/configuration.md). For `OBJECT_STORAGE_TYPE=s3`, fail the audit if required S3 fields are missing; do not wait for runtime upload failures.
4. Use [deployment workflows](references/deployment-workflows.md) for the Compose topology, service roles, storage mode decisions, upgrade/version-skew checks, and safe native-test skip criteria.
5. Use [troubleshooting](references/troubleshooting.md) to turn symptoms into likely causes and recovery steps. Start with network topology and env mismatches before escalating to backend/provider/plugin semantics.

## Minimum facts to collect from the user or running deployment

- Deployment manager and manifest location, if any, without assuming the original source checkout exists.
- Current image tags for console/server/inference/plugin, and whether they were changed independently.
- External base URL and published HTTP port.
- Storage mode (`local` or `s3`) and whether generated files must be publicly reachable.
- Backend-to-inference and backend-to-plugin URLs as seen from the backend service network.
- Whether Docker/service startup, network image pulls, port binding, external provider calls, or S3 calls are allowed for this task.

## Native-testing stance

The source-backed native deployment case for this sub-skill is a full multi-container stack. Treat it as optional and side-effectful: it pulls images, starts system services, binds ports, creates persistent volumes, and may need network/S3/provider credentials. Prefer static env/topology audits unless the user explicitly authorizes service startup and supplies a suitable deployment environment. Expected native success signals are healthy service checks and a reachable console on the configured public URL.
