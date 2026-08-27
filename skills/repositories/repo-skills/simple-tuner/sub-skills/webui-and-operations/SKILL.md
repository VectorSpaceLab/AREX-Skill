---
name: webui-and-operations
description: "Operate SimpleTuner WebUI, REST API, local job queue, workers,
  cloud jobs, auth, quotas, metrics, and webhooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# webui-and-operations

Use this sub-skill when a SimpleTuner task is about running the WebUI/API server, scripting the REST API, managing local or worker queues, submitting or inspecting cloud jobs, configuring auth and user access, handling quotas/approvals, reading metrics/audit logs, or wiring webhooks.

Do not start servers, submit jobs, upload datasets, rotate credentials, approve spend, or stop active training unless the user explicitly confirms the target server, config name, credentials/auth method, and operational impact.

## Router

1. **WebUI server and REST API**: read [webui-server-and-api](references/webui-server-and-api.md) for `simpletuner server`, WebUI onboarding, config environments, API training flow, status/events, manual validation/checkpoint triggers, reverse proxy notes, and curl planning.
2. **Queue, cloud, and workers**: read [job queue, cloud, and workers](references/job-queue-cloud-workers.md) for local GPU-aware queueing, cloud job lifecycle, concurrency, approvals, provider constraints, worker orchestration, worker labels, and CLI/API management commands.
3. **Auth, security, quotas, and audit**: read [security and auth](references/security-and-auth.md) for first-admin setup, API keys, user levels, OIDC/LDAP, registration policy, audit logs, cost limits, and approval governance.
4. **Operational failures**: read [troubleshooting](references/troubleshooting.md) for server launch, authentication, SSE/log streaming, job queue, worker, cloud, webhook, external auth, and audit-chain failures.

## Safe curl skeleton builder

Use the bundled helper to print command skeletons only; it never makes network calls:

```bash
python skills/disco/simple-tuner/sub-skills/webui-and-operations/scripts/build_api_training_plan.py --help
python skills/disco/simple-tuner/sub-skills/webui-and-operations/scripts/build_api_training_plan.py --base-url http://localhost:8001 --config-name flux-lora --mode both --include-stop
```

## Boundaries

Handle here:

- WebUI onboarding, server process options, OpenAPI discovery, REST-driven config activation/validation/start/status/stop, and webhooks.
- Queue status, GPU allocation, local job submission, worker dispatch targets, cloud job CLI/API operations, provider setup, cost limits, and approvals.
- First-admin setup, users, permission levels, API keys, OIDC/LDAP providers, audit log inspection, and security posture for shared services.

Reroute out:

- Dataloader JSON, dataset schema, captions, caches, and dataset upload contents: use data-and-config.
- Training hyperparameters, model-family choices, memory/distributed runtime, and direct CLI training commands: use training-workflows.
- Adapter conversion, model registry, LoRA/LyCORIS extraction/merge, and model tooling: use model-and-adapter-tooling.
- Source code edits, WebUI implementation changes, repository tests, docs/translations, and public-text privacy checks: use repo-development.

## Evidence base

This sub-skill distills repository-relative evidence from `documentation/webui/TUTORIAL.md`, `documentation/api/TUTORIAL.md`, `documentation/api/WEBHOOKS.md`, `documentation/JOB_QUEUE.md`, `documentation/experimental/cloud/README.md`, `documentation/experimental/server/README.md`, `documentation/experimental/server/WORKERS.md`, `documentation/experimental/server/EXTERNAL_AUTH.md`, `documentation/experimental/server/AUDIT.md`, `simpletuner/cli/server.py`, `simpletuner/cli/jobs.py`, and `simpletuner/cli/cloud/__init__.py`. Source evidence is cited by repo-relative name only; this runtime sub-skill should be usable without reopening the source checkout.
