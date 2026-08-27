# Deployment Configuration

## Purpose

Use this reference for Nexent deployment env files, image-source selection, ports, monitoring, secrets, and service dependencies.

## Shared env model

Docker and Kubernetes use the same deployment env model. Operator-facing values are stored in deployment env files and rendered or loaded by deploy scripts. Backend code should read env vars only through backend constants; deployment files supply values, backend constants parse them.

Important configuration families:

- Service endpoints: PostgreSQL/Supabase, Redis, Elasticsearch, MinIO, data-process, runtime, MCP, northbound.
- Model/provider credentials: LLM, embedding, VLM, STT/TTS, external search, ModelEngine and provider-specific values.
- Authentication: Supabase/JWT, OAuth, CAS, tenant/admin controls.
- Data processing: Ray/Celery/Redis, split timeouts, model cache paths, LibreOffice profile, worker queues.
- Sandbox: default level/scope, Docker image, CPU/memory/time/network/shell policy, output bucket.
- Monitoring: OTLP endpoint/headers/provider, trace content mode, sampling, instrumentation flags.
- Image sources: general, mainland, local latest, or registry prefix for pushed images.

## Port and component policy

Development and production port policies differ. Do not change exposed ports without checking frontend API base paths, backend service URLs, and deployment docs. Optional components may be disabled for smaller deployments, but infrastructure dependencies must still satisfy the selected application behavior.

## Secrets

Treat env values containing keys, tokens, passwords, JWT secrets, OAuth/CAS credentials, registry credentials, MinIO keys, or provider API keys as secrets. Generated skills and reports should mention variable names and purpose, not secret values.

## Configuration change checklist

1. Decide whether the value is backend code configuration, deployment-only configuration, or both.
2. For backend-readable settings, add parsing/defaults in backend constants and tests.
3. For operator-facing settings, update deployment env examples and any Helm/compose rendering.
4. For frontend-visible behavior, update frontend constants/services/types if API payloads or public config changed.
5. For SQL/schema-backed settings, update migration/init files through the migration reference.
