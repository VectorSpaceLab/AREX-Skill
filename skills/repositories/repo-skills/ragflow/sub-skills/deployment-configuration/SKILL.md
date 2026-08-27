---
name: deployment-configuration
description: "Deploy, configure, validate, and troubleshoot RAGFlow Docker,
  source, and Helm deployments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment Configuration

Use this sub-skill when a user needs help deploying RAGFlow, changing deployment configuration, switching document engines, launching from source, or diagnosing service startup issues.

## Route Here For

- Docker Compose self-hosting, image/version selection, CPU/GPU profiles, service startup, logs, and restart sequencing.
- Source launches that use Python 3.13, `uv`, Dockerized base services, separate API/task-executor processes, and the Vite frontend.
- Configuration review for `.env`, `service_conf.yaml`, document-engine settings, service credentials, ports, storage, queue, embedding-service, and OAuth/default-LLM setup.
- Elasticsearch, Infinity, OpenSearch, OceanBase, SeekDB, MySQL, MinIO, Redis, NATS, HTTPS/nginx, sandbox, and Helm deployment questions.
- Read-only consistency checks using the bundled validator at `scripts/validate_env.py`.

## Start With

1. Identify the deployment mode: Docker Compose, source development, or Helm/Kubernetes.
2. Identify the chosen document engine: `elasticsearch`, `infinity`, `opensearch`, `oceanbase`, or `seekdb` for Docker; `infinity`, `elasticsearch`, or `opensearch` for Helm.
3. Review the relevant guide:
   - `references/deployment-workflows.md` for startup, source launch, engine switching, HTTPS, and Helm flow.
   - `references/configuration.md` for key meanings and cross-file consistency rules.
   - `references/troubleshooting.md` for failure modes and diagnostic checks.
4. If the user provides config files, run a read-only validation such as:

   ```bash
   python scripts/validate_env.py --env docker/.env --service-conf docker/service_conf.yaml.template
   ```

## Key Decisions

- Prefer Docker Compose for self-hosting unless the user is actively developing or debugging source code.
- For source development, start the base services first, then run the backend API and task executors as separate Python processes, then run the frontend dev server.
- Treat `DOC_ENGINE` as a deployment-wide choice: it must match the Compose profile and the corresponding `service_conf.yaml` section.
- Treat `SVR_WEB_HTTP_PORT` as the browser-facing UI port and `SVR_HTTP_PORT` as the backend API port.
- Remember that v0.22+ RAGFlow images do not bundle embedding models; configure an external model provider, user default LLM, or a TEI service profile when needed.

## Boundaries

- For API route behavior or backend endpoint implementation, use `../backend-api-services/SKILL.md`.
- For Python SDK usage and HTTP client calls, use `../sdk-http-integration/SKILL.md`.
- For document parser internals and ingestion chunking, use `../document-parsing/SKILL.md`.
- For React/Vite frontend component work, use `../frontend-integration/SKILL.md`.
- This sub-skill explains and validates deployment configuration; it does not implement API features, SDK wrappers, parsers, or UI components.
