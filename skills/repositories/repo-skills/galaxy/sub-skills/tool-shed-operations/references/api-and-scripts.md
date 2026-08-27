# API And Scripts

Use this reference when a task involves Tool Shed API requests, legacy Tool Shed helper scripts, or deciding whether a Tool Shed operation can be executed safely.

## Bundled Planner

Run the bundled planner first:

```bash
python scripts/tool_shed_api_plan.py --help
python scripts/tool_shed_api_plan.py categories --from-tool-shed https://source.example.org --to-tool-shed http://localhost:9009
python scripts/tool_shed_api_plan.py users --from-tool-shed https://source.example.org --to-tool-shed http://localhost:9009
python scripts/tool_shed_api_plan.py reset-repository-metadata --tool-shed http://localhost:9009 --repository-id ENCODED_ID --dry-run --verbose
python scripts/tool_shed_api_plan.py reset-installed-metadata --galaxy-url http://localhost:8080
python scripts/tool_shed_api_plan.py build-whoosh-index --config config/tool_shed.yml
```

By default it prints a dry-run checklist and never contacts a server. `--execute` is available only for selected small HTTP operations and still requires explicit URL/API-key arguments. Prefer dry-run output for production or public sheds.

## Tool Shed Server API Surface

Tool Shed API routes are rooted at the Tool Shed URL, not the Galaxy URL.

Common operations:

| Operation | Route shape | Auth | Notes |
| --- | --- | --- | --- |
| List categories | `GET /api/categories` | no key normally needed | Returns category records with names/descriptions. |
| Create category | `POST /api/categories` | admin key | Body includes `name` and optional `description`. |
| List users | `GET /api/users` | may require permissions by deployment | Returns users; avoid mirroring real users into production. |
| Create user | `POST /api/users` | admin key | Body includes `username`, `email`, `password`; sensitive/rate-limited. |
| List/search repositories | `GET /api/repositories` | optional | Query by `q`, `owner`, `name`, `category_id`, paging, or sort fields. |
| Repository install info | `GET /api/repositories/install_info` | optional | Requires `name`, `owner`, and `changeset_revision`. |
| Legacy install info | `GET /api/repositories/get_repository_revision_install_info` | optional | Older list-shaped response kept for compatibility. |
| Repository metadata | `GET /api/repositories/{id}/metadata` | optional | Use to inspect metadata and dependencies for a repository revision. |
| Reset one repository metadata | `POST /api/repositories/reset_metadata_on_repository` or `POST /api/repositories/{id}/reset_metadata` | repository manager/admin | Prefer `dry_run=true&verbose=true` first. |
| Reset many repositories metadata | `POST /api/repositories/reset_metadata_on_repositories` | admin or restricted writable set | Risky bulk operation; can skip encoded ids. |
| Repository permissions/admins | `/api/repositories/{id}/allow_push`, `/admins` | manager/admin | Manage push/admin users, not generic Galaxy roles. |

Use `x-api-key` for Tool Shed API key authentication when scripting. Redact keys from output.

## Galaxy Server API Surface For Installed Repositories

Installed Tool Shed repository operations are on the Galaxy server, not the Tool Shed server. The legacy installed-repository metadata reset script targets:

```text
POST /api/tool_shed_repositories/reset_metadata_on_installed_repositories
```

This requires a Galaxy admin API key and resets metadata for repositories installed into that Galaxy instance. Use it only after confirming:

- Target Galaxy base URL and environment class: local, staging, or production.
- Admin key belongs to the intended Galaxy instance.
- User wants an installed-repository reset, not Tool Shed-side repository metadata regeneration.
- Backups/rollback and maintenance window expectations for production.

For generic Galaxy auth, key handling, OpenAPI checks, and non-Tool-Shed API workflows, use `../api-automation/SKILL.md`.

## Legacy Tool Shed API Scripts

Galaxy includes simple helper scripts for copying categories/users between sheds. Their behavior is useful evidence, but the bundled planner should be preferred for safety-first work.

### Category Copy Pattern

Legacy behavior:

1. Read categories from `FROM_TOOL_SHED/api/categories`.
2. For each category with `name` and `description`, POST to `TO_TOOL_SHED/api/categories`.
3. Authenticate to the target Tool Shed with `x-api-key`.
4. Existing categories are left to target behavior; failures are printed per category.

Safe adaptation:

- Restrict target to a local/development/test Tool Shed unless the user explicitly approves production writes.
- Compare source and target category lists first.
- Plan idempotency and duplicate-name handling before executing.
- Never hard-code the API key in a command or file.

### User Copy Pattern

Legacy behavior:

1. Read users from `FROM_TOOL_SHED/api/users`.
2. For each username, synthesize `username@test.org` and password `testuser`.
3. POST to `TO_TOOL_SHED/api/users` with the target admin key.

Safe adaptation:

- Use only for disposable test sheds; never mirror real public users into production with synthetic passwords.
- Confirm email/password policy and user activation behavior for the target Tool Shed.
- Prefer a reviewed CSV or explicit user list when a deployment requires account creation.

## Test Shed Bootstrap Pattern

The development bootstrap flow is service-required and mutating. It can:

- Create categories and users.
- Create repositories as different users.
- Mirror selected categories/users/repositories from a public Tool Shed.
- Clone Mercurial repositories and push content into a target shed.
- Reset metadata for created repositories.

Use it as a reference for development/test-shed setup only. Before adapting it, confirm the shed URL, admin key, user key behavior, network access to the source shed, Mercurial availability, and that the target is disposable.

## Whoosh Index Script Pattern

The Tool Shed index builder reads Tool Shed configuration and writes repository/tool search indexes. The checklist is:

1. Confirm Tool Shed config path.
2. Confirm search is enabled in Tool Shed configuration.
3. Confirm the Whoosh index directory is configured and writable by the Tool Shed runtime user.
4. Confirm database connection and Mercurial repository directories are reachable.
5. Stop or coordinate with live service if the index directory may be replaced.
6. Run the index build in the Tool Shed runtime environment.
7. Verify repository and tool searches after rebuild.

The bundled planner prints this checklist; it does not rebuild indexes.

## Request Payload Notes

Useful request shapes distilled from Tool Shed schema models:

```json
{"name": "Category Name", "description": "Optional description"}
```

```json
{"username": "alice", "email": "alice@example.org", "password": "temporary-password"}
```

```json
{"repository_id": "ENCODED_ID", "dry_run": true, "verbose": true}
```

```json
{"my_writable": true, "encoded_ids_to_skip": ["ENCODED_ID_TO_SKIP"]}
```

Repository create requests include `name`, `synopsis`, optional long `description`, optional `remote_repository_url`, optional `homepage_url`, `type` such as `unrestricted`, and category ids. Publishing repository content and Mercurial push behavior are deployment-sensitive; prefer Tool Shed test helpers or deployment docs for execution.

## Choosing Execute vs Plan

Execute only when all are true:

- The user explicitly asks to execute.
- The target URL and API key are supplied by the user or environment variable.
- The operation is narrowly scoped and understood.
- The target is local/disposable or the user confirms production risk.
- The script output redacts credentials.

Otherwise, return a dry-run plan, expected routes, request bodies, and validation steps.
