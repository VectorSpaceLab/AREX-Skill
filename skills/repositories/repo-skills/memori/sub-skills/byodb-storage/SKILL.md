---
name: byodb-storage
description: "Routes Memori BYODB storage, schema build, database recipes, and
  provisioning workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# BYODB Storage

Use this sub-skill for Memori database-backed memory setup: connection
factories, schema build, driver selection, database recipes, and provisioning.

## Use when

- The request mentions SQLite, PostgreSQL, MySQL, TiDB, MongoDB, Oracle,
  CockroachDB, OceanBase, SQLAlchemy, DB-API connections, or `Memori.provision`.
- The user needs to understand how `Memori(conn=...)` switches the package from
  cloud mode into BYODB mode.
- The user is debugging unsupported-database, missing-driver, or schema-build
  failures.

## Read first

- `references/storage-api-reference.md` for connection and build behavior.
- `references/database-recipes.md` for supported database families and extras.
- `references/provisioning.md` for TiDB Zero provisioning and cache behavior.
- `references/troubleshooting.md` for driver and service failures.
- `scripts/sqlite_byodb_smoke.py` for a safe local smoke.

## What this sub-skill owns

- `Memori(conn=...)` and the storage manager.
- SQLite and other BYODB driver recipes.
- Schema creation through `mem.config.storage.build()`.
- `Memori.provision(...)` and the TiDB Zero provisioning route.

## What it does not own

- Cloud API key and MCP workflows: use `cli-and-cloud`.
- `llm.register(...)` provider selection: use `llm-integration`.
- Recall/search, attribution, embeddings, or native runtime details: use
  `memory-and-search`.
- TypeScript storage specifics: use `typescript-sdk`.

## Safe first check

Run the bundled SQLite smoke before recommending a live database change:

```bash
python scripts/sqlite_byodb_smoke.py
```

That helper creates a temporary SQLite database, builds the Memori schema, and
checks the expected tables without network or credentials.
