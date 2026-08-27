---
name: runtime-configuration
description: "Install, run, configure, and deploy ContextForge safely from PyPI
  or a checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Runtime Configuration

Use this sub-skill for ContextForge install, run, configuration, and deployment tasks.
It is the operator-facing route for PyPI installs, checkout installs, `.env` setup,
secret generation, container start-up, and high-level deployment choice.

## Read first

- [`../../references/package-overview.md`](../../references/package-overview.md)
- [`../../references/cli-entrypoints.md`](../../references/cli-entrypoints.md)
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
- [`references/configuration-and-runtime.md`](references/configuration-and-runtime.md)
- [`references/deployment-recipes.md`](references/deployment-recipes.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`scripts/contextforge_env_audit.py`](scripts/contextforge_env_audit.py)

## Use this sub-skill when

- the user wants to install ContextForge from PyPI or from a checkout
- the user asks how to start `mcpgateway`, `mcpgateway-server`, `cforge`, or `init-secrets`
- the user needs to choose between local dev, production serve, containers, Compose, or Helm
- the user needs help with required secrets, `.env` values, or safe environment auditing
- the user needs a startup diagnostic that does not print secret values

## What this sub-skill covers

- package identity and Python support window
- secret creation, patching, and validation
- host/port choices and local run modes
- SQLite, PostgreSQL, and Redis selection
- admin UI / admin API / observability feature flags
- Docker, Compose, and Helm at a route-and-checklist level
- safe startup diagnostics and env-file audit flows

## Reference map

| Need | Use |
| --- | --- |
| package/version/Python requirement | [`../../references/package-overview.md`](../../references/package-overview.md) |
| CLI behavior and special diagnostics | [`../../references/cli-entrypoints.md`](../../references/cli-entrypoints.md) |
| `.env`, secrets, ports, DB/cache, feature flags | [`references/configuration-and-runtime.md`](references/configuration-and-runtime.md) |
| PyPI, checkout, container, Compose, Helm, `cforge` choice | [`references/deployment-recipes.md`](references/deployment-recipes.md) |
| startup failures and common symptoms | [`references/troubleshooting.md`](references/troubleshooting.md) |
| read-only env audit | [`scripts/contextforge_env_audit.py`](scripts/contextforge_env_audit.py) |

## Decision rules

1. Identify the install source first: PyPI, editable checkout, container, or deployment YAML.
2. Check `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET` before anything else.
3. Treat `make dev` as the live-reload lane on port `8000`.
4. Treat `make serve`, `mcpgateway`, `mcpgateway-server`, and `python -m mcpgateway` as production-style startup on port `4444` unless overridden.
5. Prefer SQLite only for local or simple single-node use; prefer PostgreSQL for production.
6. Use Redis when you need shared cache, rate limiting, or multi-instance coordination.
7. Keep management surfaces intentional: `MCPGATEWAY_UI_ENABLED`, `MCPGATEWAY_ADMIN_API_ENABLED`, `API_ALLOW_BASIC_AUTH`, and `DOCS_ALLOW_BASIC_AUTH` should not be assumed from code defaults.
8. For read-only checks, prefer `mcpgateway --validate-config`, `mcpgateway --config-schema`, `mcpgateway --support-bundle`, or `scripts/contextforge_env_audit.py`.
9. Route auth/RBAC questions to [`../auth-rbac-security/SKILL.md`](../auth-rbac-security/SKILL.md).
10. Route registry CRUD/API questions to [`../registry-admin-api/SKILL.md`](../registry-admin-api/SKILL.md).
11. Route live MCP/A2A/gRPC transport questions to [`../mcp-transports-federation/SKILL.md`](../mcp-transports-federation/SKILL.md).
12. Route maintainer test-matrix or validation-workflow questions to [`../development-validation/SKILL.md`](../development-validation/SKILL.md).

## Source script policy

- Bundle only the read-only audit helper: [`scripts/contextforge_env_audit.py`](scripts/contextforge_env_audit.py).
- Treat repository `scripts/contextforge-setup.sh` as reference-only because it installs packages, configures Docker/user state, clones repositories, and can start services.
- Exclude cleanup and maintenance scripts from this runtime subtree because they can remove volumes, databases, containers, or operational state.
- If a user asks to run a host-mutating setup or cleanup script, stop and ask for explicit confirmation and deployment context first.

## Fast operating checklist

- Pick the install lane: PyPI, checkout, or container image.
- Generate real secrets with `init-secrets` before startup.
- Make the `.env` file match the chosen lane instead of mixing dev and prod defaults.
- Choose the database and cache backend before deployment.
- Decide whether the UI/admin API should be exposed.
- Use the bundled audit script to compare `.env` against `.env.example` without revealing secret values.
- Escalate to the troubleshooting reference if startup fails or a flag mismatch is suspected.

## Output style

When answering, give the shortest safe path first, then point to the matching reference or script.
Prefer bundled references over re-deriving package behavior from memory.
