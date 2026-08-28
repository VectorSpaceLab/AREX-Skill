---
name: deploy-configure
description: "Guides DocsGPT development, deployment, service topology, model configuration, authentication, storage, observability, and upgrades."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deploy and Configure DocsGPT

Use this sub-skill for environment setup, application topology, provider/model configuration, auth, storage, database, queue, observability, and upgrade work.

## Choose the path

- **Source development**: read [development and deployment](references/development-and-deployment.md). Reuse an existing Python environment, Postgres, and Redis when healthy; use explicit dependency commands rather than setup bootstrap scripts.
- **Container or Kubernetes deployment**: read the same reference for service topology, health gates, worker queues, reverse proxy, and rollout order.
- **Environment/model configuration**: read [configuration](references/configuration.md), then validate custom model YAML before restart.
- **OIDC, SCIM, RBAC, S3, migrations, or observability**: read [auth, storage, and observability](references/auth-storage-observability.md).
- **Failure or upgrade**: read [troubleshooting](references/troubleshooting.md) before mutating data or identity configuration.

## Baseline source-development workflow

1. Confirm Python 3.12, a project-local environment, and existing service health.
2. Configure a root `.env`; do not commit it.
3. Install the bundled 0.18.0 backend dependency snapshot explicitly (run from this sub-skill directory):

   ```bash
   python -m pip install -r ../../references/backend-requirements-0.18.0.txt
   ```

   For another DocsGPT release, compare [repository provenance](../../references/repo-provenance.md) and refresh the skill rather than silently mixing dependency versions.

4. Run the full ASGI target:

   ```bash
   uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091 --reload
   ```

5. Start a worker in another terminal when ingestion, parsing, schedules, titles, or other background jobs are needed:

   ```bash
   celery -A application.app.celery worker -l INFO
   ```

   On macOS, use `python -m celery -A application.app.celery worker -l INFO --pool=solo`.
6. Run the frontend separately with its local npm dependencies.
7. Verify `/api/health`, `/api/config`, one model listing, and one bounded task before broader testing.

Flask-only development is a reduced mode: `/mcp` and native-async message-event reconnect are absent.

## Service preflight

Use the bundled checker before blaming application code:

```bash
python scripts/check_services.py \
  --postgres-uri "$POSTGRES_URI" \
  --redis-url "$CELERY_BROKER_URL" \
  --api-url http://localhost:7091
```

The helper performs connection/readiness probes only. Omit secrets from pasted output.

## Model catalog changes

Use operator YAML through `MODELS_CONFIG_DIR` for OpenAI-compatible endpoints or extensions to registered providers. Preserve model ids after users select them.

```bash
python scripts/validate_model_catalog.py ./models-config
```

Validation checks shape, duplicate ids, supported capability fields, attachment aliases, reasoning effort, and OpenAI-compatible metadata. It does not contact providers.

## Production rules

- Run the ASGI app through an ASGI-capable worker. Forward SSE without proxy buffering and preserve long request timeouts deliberately.
- Use Postgres as the user-data store. Set `AUTO_CREATE_DB=false` and `AUTO_MIGRATE=false` when migrations are controlled by CI/CD.
- Use Redis URLs consistently across web and workers. A worker without `-Q` consumes all configured queues; split `docsgpt` and `parsing` only with matching workers.
- Treat `LOCAL_MODE_ADMIN=true` as local no-auth mode only; never use it on a networked deployment.
- Mount model catalogs read-only, keep secrets in the platform secret store, and separate public base URLs from internal service URLs.
- Back up Postgres and object storage before schema or data migrations.
- Add optional services only for selected features: pgvector/vector database, S3-compatible storage, sandbox runner, OAuth connectors, telemetry collector.

## Cross-skill routes

- Source ingestion and worker behavior: [ingest-sources](../ingest-sources/SKILL.md)
- Vector-store and retrieval compatibility: [retrieval-vectorstores](../retrieval-vectorstores/SKILL.md)
- Client/API verification: [api-client-operations](../api-client-operations/SKILL.md)
- Sandbox and remote-device services: [tools-integrations](../tools-integrations/SKILL.md)
