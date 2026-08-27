# Galaxy Cross-Cutting Troubleshooting

## Purpose

Read this for failures that span multiple Galaxy surfaces or when the right sub-skill is not obvious.

## Install or Import Failure

Symptoms:

- Root editable install fails with package discovery, generated package, or flat-layout errors.
- `import galaxy` succeeds but a submodule fails on an optional dependency.
- Split package metadata exists but full server imports are incomplete.

Likely causes and recovery:

1. Check [Package Layout](package-layout.md) before installing broad dependencies.
2. Prefer split-package installs for config/schema/tool-util inspection when full server runtime is not required.
3. Install only dependencies for the selected workflow; avoid all dev/test/client extras unless the task requires them.
4. If the task requires a full server, expect database, web, job, storage, and optional service dependencies; plan that as a service setup task.

## Server Startup vs Client Build

Symptoms:

- `run.sh` or startup logs mention missing static assets, client build, Node/pnpm, or Vite.
- Backend config changes appear mixed with frontend artifact errors.

Recovery:

- Use [Configuration and Admin](../sub-skills/configuration-and-admin/SKILL.md) for backend config/startup.
- Use [Web Client Development](../sub-skills/web-client-development/SKILL.md) for pnpm, Vite, static bundle, generated API-client, or frontend test failures.
- Do not rebuild the client automatically unless the user asked for frontend/build validation.

## Service-Required Operations

Many Galaxy workflows need a running Galaxy or Tool Shed service:

- API history/dataset/workflow writes.
- Framework tool and workflow tests.
- Integration/Selenium/Playwright tests.
- Tool Shed metadata reset, category/user creation, repository install, or Whoosh index rebuild.
- Database migrations, cleanup scripts, object-store migration, and cloud backend checks.

Before running, identify the target service, credentials, disposable data scope, and rollback expectations. For planning-only work, use the bundled dry-run helpers in the relevant sub-skill.

## Credential, Network, and Destructive Boundaries

Do not run these without explicit user authorization and disposable targets:

- Cloud object-store/file-source tests requiring AWS, Azure, GCP, iRODS, Rucio, Onedata, WebDAV, OAuth, or private tokens.
- Scripts that purge/delete datasets, histories, libraries, users, storage files, repositories, search indexes, or database rows.
- Commands that download large data, build containers, call package registries, or start external services.
- API calls against production Galaxy or Tool Shed URLs.

Record skipped native candidates with a reason and create a synthetic/tiny-fixture case where possible.

## Version or Staleness Confusion

If current repo facts differ from [Repository Provenance](repo-provenance.md), run `refresh-repo-skill` before trusting detailed claims. Important signals include:

- Current Git commit or dirty paths differ from provenance.
- `galaxy.version.VERSION` changed.
- Split package versions or entry points changed.
- Client `package.json` scripts or pnpm workspace layout changed.
- Public API routes, tool-util CLIs, config schemas, Tool Shed metadata flows, or test conventions changed.

## Route Recovery

- Config/startup/admin issue: [Configuration and Admin](../sub-skills/configuration-and-admin/SKILL.md).
- HTTP API issue: [API Automation](../sub-skills/api-automation/SKILL.md).
- Tool/workflow artifact issue: [Workflows and Tools](../sub-skills/workflows-and-tools/SKILL.md).
- Datatype/storage/data-manager issue: [Data and Storage](../sub-skills/data-and-storage/SKILL.md).
- Tool Shed repository issue: [Tool Shed Operations](../sub-skills/tool-shed-operations/SKILL.md).
- Vue/TypeScript/client issue: [Web Client Development](../sub-skills/web-client-development/SKILL.md).
