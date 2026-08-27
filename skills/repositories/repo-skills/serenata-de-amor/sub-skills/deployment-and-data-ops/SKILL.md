---
name: deployment-and-data-ops
description: "Operate Jarbas and Rosie service setup, data loading, validation,
  assets, and maintenance workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment and Data Operations

Use this sub-skill when the task is to install, start, seed, validate, or troubleshoot the service/data lifecycle around Serenata de Amor's Jarbas Django service and Rosie outputs.

Route elsewhere:

- Jarbas REST endpoint semantics, serializers, filters, and response shapes are owned by `jarbas-data-api`.
- Rosie classifier behavior, model/cache details, and `suspicions.xz` generation are owned by `rosie-suspicion-pipeline`.
- Production deployment automation, DigitalOcean updates, cron jobs, and external API publishing are reference-only here; do not execute credential-bound automation unless a human explicitly authorizes the exact target environment.

## Fast operating map

1. Identify the environment path: Docker Compose local, local Python service stack, or reference-only production maintenance.
2. Prepare configuration using [configuration.md](references/configuration.md). Never invent or print real credentials.
3. Bring up prerequisites from [docker-and-services.md](references/docker-and-services.md): legacy Python dependencies, PostgreSQL for full Jarbas semantics, optional RabbitMQ/Celery, cache, and optional Node/Elm asset tooling.
4. Run the safe preflight helper before service-changing operations:

   ```console
   $ python sub-skills/deployment-and-data-ops/scripts/jarbas_manage_check.py --repo-root <serenata-checkout>
   ```

   Use `--no-run` to inspect the command and default environment keys without invoking Django.
5. Seed data using [data-loading.md](references/data-loading.md) and [management-commands.md](references/management-commands.md). The safe sample order is migrations first, then reimbursements, companies, suspicions, search vector, and optional tweets/social-media/receipt commands.
6. Build or collect frontend/static assets only when the legacy Node/Elm stack is available; see [frontend-assets.md](references/frontend-assets.md).
7. For maintenance scripts and one-off research data acquisition, classify the script before running anything using [research-and-maintenance-scripts.md](references/research-and-maintenance-scripts.md).
8. Diagnose known failures with [troubleshooting.md](references/troubleshooting.md).

## Safe defaults and validation boundaries

- `manage.py check` is a configuration/import preflight; it does not replace migrations, sample data loads, API tests, or PostgreSQL-backed search validation.
- SQLite can be useful for `manage.py check`, but full Jarbas behavior uses PostgreSQL-specific fields and search vectors.
- `tweets`, `tweet`, `receipts`, `receipts_text`, `socialmedia`, and `update` have side effects or external dependencies; read their command notes before use.
- Do not run DigitalOcean, cron, deploy, or research fetch scripts as generic setup. Treat them as historical/maintainer workflows unless the user provides credentials, target environment, rollback plan, and authorization.

## Bundled files

- [configuration.md](references/configuration.md) — environment variables, secret handling, and check-time defaults.
- [docker-and-services.md](references/docker-and-services.md) — Docker Compose topology, local install prerequisites, startup/validation sequences.
- [data-loading.md](references/data-loading.md) — sample dataset formats, load order, validation counts, receipt text and social-media CSV assumptions.
- [management-commands.md](references/management-commands.md) — command table, flags, prerequisites, outputs, and safety classification.
- [frontend-assets.md](references/frontend-assets.md) — Node 8 / Elm 0.18 asset workflow and pitfalls.
- [research-and-maintenance-scripts.md](references/research-and-maintenance-scripts.md) — research, cron, update, and deploy script classifications.
- [troubleshooting.md](references/troubleshooting.md) — common failures and recovery steps.
- [jarbas_manage_check.py](scripts/jarbas_manage_check.py) — safe wrapper around `python manage.py check`.
