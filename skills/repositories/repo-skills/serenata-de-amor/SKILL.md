---
name: serenata-de-amor
description: "Use Operação Serenata de Amor's Rosie suspicious-expense pipeline
  and Jarbas Django data API, setup, and data-loading workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Serenata de Amor

Use this repo skill when a task involves Operação Serenata de Amor, especially Rosie suspicious-reimbursement analysis, Jarbas Django/DRF reimbursement APIs, or the service/data setup that connects them.

## First checks

- Read [references/repo-provenance.md](references/repo-provenance.md) before assuming this skill is current for a checkout. Refresh if the commit, dirty state, source roots, dependencies, or public workflow files changed.
- Use [scripts/check_serenata_imports.py](scripts/check_serenata_imports.py) for a safe import/Django setup preflight. It does not run migrations, start services, download datasets, or call external APIs.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting legacy dependency, non-packaged checkout, service, and safety boundaries.

## Route by task

- **Generate or inspect suspicious-expense output with Rosie** -> `sub-skills/rosie-suspicion-pipeline/`. Use it for `rosie.py run`, `rosie.py test`, classifier required columns, `Core(settings, adapter)`, `suspicions.xz`, model caches, and no-download classifier smoke checks.
- **Use, build, or debug Jarbas API queries** -> `sub-skills/jarbas-data-api/`. Use it for reimbursement/company/applicant/subquota/receipt endpoints, query parameters, pagination, serializers, CNPJ/CPF cleaning, same-day logic, and PostgreSQL search-vector caveats.
- **Set up services, load data, or operate maintenance commands** -> `sub-skills/deployment-and-data-ops/`. Use it for Docker/local setup, `.env` variables, migrations, sample data load order, management commands, Celery/cache/PostgreSQL/Node/Elm boundaries, and reference-only research/deploy scripts.

## Typical workflow map

1. If starting from raw civic spending data, use `rosie-suspicion-pipeline` to understand or run Rosie and produce `suspicions.xz`.
2. Use `deployment-and-data-ops` to prepare Jarbas configuration, migrate the database, load reimbursements/companies/suspicions, and rebuild search vectors when PostgreSQL is available.
3. Use `jarbas-data-api` to query or explain API results after data exists.
4. When a failure crosses boundaries, start with the owning sub-skill and follow its sibling links rather than duplicating setup or API details.

## Runtime and service expectations

Serenata de Amor is a legacy multi-service project, not a single modern pip package. Public evidence shows Python 3.6-era CI and pinned 2019 dependencies. For practical inspection or maintenance, use a compatible legacy Python environment and avoid unpinned upgrades unless the task is explicitly to modernize the repo.

Full Jarbas behavior uses PostgreSQL-specific fields and search vectors. SQLite can be enough for import/system-check preflights, but it is not evidence that search or all model-field behavior works in production. RabbitMQ/Celery, memcached, Docker, Node/Elm, Twitter credentials, DigitalOcean credentials, and network-backed dataset downloads are optional or service-bound surfaces; do not start or mutate them without task-specific authorization.

## Safe validation commands

From a target checkout with suitable dependencies installed:

```console
$ python scripts/check_serenata_imports.py --repo-root <serenata-checkout>
$ python sub-skills/rosie-suspicion-pipeline/scripts/rosie_smoke.py --repo-root <serenata-checkout>
$ python sub-skills/jarbas-data-api/scripts/jarbas_api_probe.py smoke
$ python sub-skills/deployment-and-data-ops/scripts/jarbas_manage_check.py --repo-root <serenata-checkout>
```

These helpers are bundled with the skill and are safe by default. They do not replace native unit tests, migrations, sample data loads, or service-backed API verification.

## Do not use this skill for

- Generic Django, Celery, scikit-learn, or civic-tech questions that do not involve Serenata de Amor concepts, commands, data columns, APIs, or errors.
- Executing production deploy/update/cron/research fetch scripts without explicit credentials, target environment, rollback plan, and user authorization.
- Claiming current compatibility with modern Python/NumPy/Django stacks unless you have refreshed and verified the repository.
