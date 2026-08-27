---
name: deployment-operations
description: "Operate Nexent Docker, Kubernetes, offline deployment, SQL
  migration, image build, monitoring, and deployment troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment Operations

Use this sub-skill for Nexent deployment and release-engineering tasks: Docker Compose, Kubernetes/Helm, offline packages, image builds, uninstall/upgrade, runtime env files, monitoring, SQL migration/init synchronization, and deployment failure triage.

Do **not** use this sub-skill for backend route/service architecture, frontend UI/API integration, or SDK agent runtime changes except where deployment files must be coordinated with them.

## Start Here

1. Classify the task:
   - Docker or Compose lifecycle -> read [deployment workflows](references/deployment-workflows.md#docker-compose-deployment).
   - Kubernetes or Helm lifecycle -> read [deployment workflows](references/deployment-workflows.md#kuberneteshelm-deployment).
   - Offline package, image build, image registry, or `local-latest` -> read [deployment workflows](references/deployment-workflows.md#image-builds-and-offline-packages).
   - Runtime environment, ports, image sources, secrets, OAuth/CAS, sandbox, or monitoring -> read [configuration](references/configuration.md).
   - SQL schema, migrations, init SQL, release version, or data-sync scripts -> read [migrations and data sync](references/migrations-and-data-sync.md).
   - Failed deployment, unhealthy containers/pods, migration waits, port conflicts, pull failures, or env mismatch -> read [troubleshooting](references/troubleshooting.md).
2. Prefer safe static checks before live operations. For SQL/init/version checks, run:

   ```bash
   python sub-skills/deployment-operations/scripts/check_sql_migration_sync.py --repo-root <nexent-checkout>
   ```

   Use `--json` when a caller needs machine-readable output.
3. If a command can delete data, push images, rotate secrets, touch a live cluster, or restart services, confirm the intended target, component set, data-preservation policy, and backup status before running it.

## Repo-Relative Files This Sub-Skill Owns

| Area | Primary files to inspect or update in a Nexent checkout |
| --- | --- |
| Root wrappers | `deploy.sh`, `uninstall.sh`, `build.sh`, `VERSION` |
| Shared deployment helpers | `deploy/common/common.sh`, `deploy/common/version.sh`, `deploy/common/run-sql-migrations.sh`, `deploy/common/start-backend.sh` |
| Docker | `deploy/docker/deploy.sh`, `deploy/docker/uninstall.sh`, `deploy/docker/compose/*.yml`, `deploy/docker/assets/`, `deploy/docker/deploy.options` |
| Kubernetes | `deploy/k8s/deploy.sh`, `deploy/k8s/uninstall.sh`, `deploy/k8s/helm/nexent/`, `deploy/k8s/deploy.options` |
| Environment | `deploy/env/.env.example`, `deploy/env/.env`, `deploy/env/image-source.*.env`, `deploy/env/monitoring.env.example`, `deploy/env/monitoring.env` |
| Images/offline | `deploy/images/build.sh`, `deploy/images/dockerfiles/*/Dockerfile`, `deploy/offline/*.sh` |
| SQL/data sync | `deploy/sql/init.sql`, `deploy/sql/migrations/*.sql`, `deploy/sql/supabase/*.sql`, `deploy/docker/assets/scripts/*sync*` |
| Native deploy tests | `deploy/tests/test_common.sh`, `deploy/tests/test_sql_migrations.sh`, `deploy/tests/test_build_offline_package.sh`, `deploy/tests/test_images_build.sh`, `deploy/tests/test_super_admin_init.sh` |

## Boundary Routing

- Backend app/service/database implementation, env variable source-of-truth, and pytest selection -> [backend services/API](../backend-services-api/SKILL.md).
- Frontend web behavior, Next.js builds, API client contracts, and UI routes -> [frontend integration](../frontend-integration/SKILL.md).
- SDK agent execution, model/tool configuration, sandbox semantics, and monitoring instrumentation internals -> [SDK agent runtime](../sdk-agent-runtime/SKILL.md).
- Knowledge, MinIO, Elasticsearch, Redis, data-process, and memory workflows at application level -> [knowledge/data/memory](../knowledge-data-memory/SKILL.md). Use this sub-skill only for deploying those services.

## Safety Rules

- Treat `.env`, generated secrets, registry passwords, Supabase keys, OAuth/CAS secrets, and monitoring provider keys as sensitive. Do not paste secret values into reports unless the user explicitly asks.
- Keep data by default. Docker `delete-all` / `--delete-volumes true` and Kubernetes `delete-all` / `--delete-local-data true` are destructive.
- Do not edit generated Helm values by hand; rerun the deployment script so values are regenerated from `deploy/env/.env` and deployment options.
- SQL-only changes require rerunning deployment so mounted/rendered SQL and rollout checksums update; they do not require rebuilding application images.
- Deployment scripts are repo-bound and have live side effects. This generated skill bundles a static SQL checker, not copies of deployment scripts.
