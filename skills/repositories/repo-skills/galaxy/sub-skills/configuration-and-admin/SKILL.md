---
name: configuration-and-admin
description: "Configure, start, validate, and troubleshoot Galaxy server/admin
  deployments, including galaxy.yml, jobs, object stores, dependency resolvers,
  and startup routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy Configuration And Admin

Use this sub-skill when a user needs help configuring or starting a Galaxy server, validating `galaxy.yml`, resolving config schema/startup errors, or planning admin changes around jobs, object stores, dependency resolvers, authentication, or Gravity process startup.

## Start Here

1. Identify the active `galaxy.yml`; if missing, help the user copy or derive it from the bundled sample guidance rather than editing sample files in place.
2. Read [configuration.md](references/configuration.md) for the core file roles, top-level YAML shape, safe validation workflow, and bundled helper usage.
3. Read [admin-operations.md](references/admin-operations.md) for startup decisions, `run.sh`/Gravity concepts, job routing, object-store pointers, dependency resolvers, and authentication/config file routing.
4. Read [troubleshooting.md](references/troubleshooting.md) when the symptom is a failed startup, YAML/schema error, missing config, path mistake, dependency resolver failure, or client/server confusion.

## Bundled Helper

Run `python scripts/validate_galaxy_config.py --config PATH` to perform a safe read-only smoke check of a Galaxy YAML config. Add `--sample PATH` when comparing a copied sample or checking that a sample file is parseable. The helper does not start Galaxy, contact services, write files, install dependencies, or validate every Galaxy schema rule.

## Routing Boundaries

- Use this sub-skill for `galaxy.yml`, startup, admin config files, job config pointers, dependency resolver configuration, authentication pointers, and high-level object-store references.
- Route object-store implementation details, data tables, dataset storage behavior, and storage migration planning to [data-and-storage](../data-and-storage/SKILL.md).
- Route API automation, admin API calls, scripted user/tool management, and client request examples to [api-automation](../api-automation/SKILL.md).
- Route tool XML, workflow authoring, Tool Shed behavior, and execution semantics to `workflows-and-tools` when present.
- Route JavaScript client build, npm/yarn, webpack/Vite, static asset, and UI development issues to [web-client-development](../web-client-development/SKILL.md).

## Safety Rules

- Treat database connections, object-store paths, job runner commands, dependency resolver paths, authentication providers, and proxy/socket settings as deployment-sensitive.
- Prefer dry-run/read-only checks first; do not create, migrate, delete, or move production database/storage content unless the user explicitly asks and provides a backup/rollback plan.
- Do not collect or print secrets from database URLs, OIDC/SAML settings, Vault config, cloud object-store credentials, or proxy authentication headers.
- Keep local development plans separate from production deployment plans; production usually needs an external database, proxy, process manager, logging, backups, and service monitoring beyond this sub-skill.
