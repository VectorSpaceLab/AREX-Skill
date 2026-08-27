---
name: legacy-migration
description: "Migrate Argilla v1/Rubrix users, workspaces, and legacy task
  datasets into Argilla 2.x safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Legacy migration

Use this sub-skill when you need to move legacy Argilla v1/Rubrix users, workspaces, and task-specific datasets into Argilla 2.x, or when you need to explain why a legacy dataset should not be migrated as-is.

Read these bundled references:

- `references/migration-workflow.md` when you are planning the migration order, choosing a v1-to-v2 mapping, or deciding whether the source is already a `FeedbackDataset`.
- `references/legacy-api-reference.md` when you need the exact legacy compatibility calls, the current v2 counterparts, or the dependency traps to avoid.
- `references/troubleshooting.md` when imports, credentials, IDs/passwords, record shapes, or search-index refresh questions fail.

Run this bundled script:

- `scripts/legacy_migration_skeleton.py` when you want a safe argparse starting point or a TODO-based migration plan template. It only prints a plan/template and does not talk to a server unless you later edit the placeholder hooks.

Use this sub-skill for:

- `import argilla.v1 as rg_v1` compatibility workflows.
- Retrieving legacy users and workspaces from a v1/Rubrix server.
- Recreating users and workspaces on a current Argilla 2.x server.
- Rebuilding `DatasetForTextClassification`, `DatasetForTokenClassification`, and `DatasetForText2Text` as v2 `rg.Settings` + `rg.Dataset` objects.
- Mapping legacy records into `dataset.records.log(...)` with fields, metadata, vectors, suggestions, and responses.

Do not use this sub-skill for:

- Fresh current-only dataset workflows -> use `python-sdk`.
- Deployment, proxying, or search-index reindex mechanics -> use `server-ops`.
- Deep legacy training, monitoring, or listener frameworks -> out of scope here.

Before you start, confirm:

- Legacy server URL and API key.
- Current Argilla 2.x server URL and API key.
- Backups and export-first handling.
- Passwords cannot be recovered from the legacy server.
- If IDs and passwords must stay stable, a same-server upgrade or temporary v2 copy path is safer than a fresh re-creation.
- If you need the old package for deeper inspection, keep it in a separate legacy inspection environment; do not add broad legacy extras to the current Argilla 2.x server env.

Migration in one line:

1. Extract from `rg_v1`.
2. Recreate `rg.User` and `rg.Workspace`.
3. Define v2 `rg.Settings` and `rg.Dataset`.
4. Convert legacy records to `rg.Record`.
5. Upload with `dataset.records.log(...)`.
6. Hand off search-index refresh questions to `server-ops` when the problem is operational rather than schema-level.

Note: `FeedbackDataset` already uses the v2 format. Do not run the legacy schema migration for it; only search-index refresh/reindex may be needed after a 2.x server change.

Provenance: distilled from the current Argilla 2.8.0dev0 SDK/server inspection, the legacy-dataset migration guide, the Rubrix migration note, the `argilla.v1` shim, and `argilla-v1` package metadata/source names.
