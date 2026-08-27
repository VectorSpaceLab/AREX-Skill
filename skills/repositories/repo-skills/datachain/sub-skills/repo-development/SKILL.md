---
name: repo-development
description: "Guides DataChain repository maintenance, packaging, focused tests,
  contributor workflows, and backend-sensitive source changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Repo Development

Use this sub-skill when the user is working inside a DataChain checkout and asks
how to edit, test, package, document, or review the repository itself. It is for
maintainer workflows, not ordinary DataChain SDK usage.

## Trigger Phrases

Load this sub-skill for prompts containing or implying:

- contributor setup, `nox`, pytest, lint, docs build, package build, optional
  extras, Python version support, or repository test layout;
- changes to signal schemas, `DataModel`, flatten/unflatten, Python↔SQL type
  conversion, physical storage, warehouse SQL, or nested field exports;
- backend divergence between local SQLite, Studio ClickHouse, and future
  BigQuery/Snowflake/Postgres support;
- source edits under `src/datachain/lib`, `src/datachain/func`,
  `src/datachain/sql`, `src/datachain/query`, `src/datachain/cli`, or
  `src/datachain/skill`;
- dirty/stale checkout checks, generated repo skill refresh decisions, or
  repository provenance.

## First Decision

1. **Need setup, tests, nox sessions, optional extras, or focused test choice**
   → read [development-and-testing](references/development-and-testing.md) and
   use [select_tests.py](scripts/select_tests.py) for suggestions.
2. **Changing schema, nested signal mapping, SQL types, export/read-back, or
   backend-sensitive behavior** → read
   [schema-backend-change-matrix](references/schema-backend-change-matrix.md)
   before proposing completion criteria.
3. **Need stale-skill or checkout provenance evidence** → run
   [snapshot_repo_state.py](scripts/snapshot_repo_state.py) in the current
   checkout and compare with the root skill provenance.
4. **Debugging maintainer failures** → read
   [troubleshooting](references/troubleshooting.md), then pick the narrowest
   reproducible test before running broad sessions.

## Durable Maintainer Rules

- A signal is a typed column. A nested `DataModel` flattens into DB columns; the
  logical `SignalSchema` travels with every dataset version.
- Chain operations return new chains and must not mutate the receiver in place.
- Logical schema and physical columns are mapped in many paths: ingestion,
  export, query operations, object hydration, flat tabular export, and each
  backend. There is no single chokepoint.
- Local SQLite is the convenient default, not proof of backend parity. ClickHouse
  has stricter nullability and array/map behavior; future backends add more
  divergence. Verify target behavior on the actual backend when the change
  depends on backend semantics.
- For signal→column work, done means a literal matrix of affected paths ×
  backend(s) × composition axes with permanent tests and read-back assertions.
  A green smoke test is not enough.
- Keep comments sparse and timeless. Public APIs need docstrings; internal
  helpers usually need clear names instead of explanatory comments.

## Boundaries and Reroutes

- This sub-skill owns DataChain source maintenance, packaging, nox/pytest, test
  selection, backend-sensitive review, and stale-skill provenance.
- For user-facing SDK code patterns, UDFs, saves, exports, File/DataModel usage,
  and LLM operations, read [`sdk-pipelines`](../sdk-pipelines/SKILL.md).
- For native query operations, function expressions, and schema/backend behavior
  as an SDK user, read [`query-engine`](../query-engine/SKILL.md).
- For `datachain` CLI command usage or Studio job/pipeline operation, read
  [`cli-and-studio`](../cli-and-studio/SKILL.md).
- For DataChain bundled coding-agent skills or `dc-knowledge`, read
  [`agent-harness`](../agent-harness/SKILL.md).

## Safety Rules

- Do not run full `nox` or broad example/cloud/Studio tests when a focused test
  can isolate the issue first.
- Treat tests that need cloud credentials, Studio tokens, model downloads,
  optional GPU/torch/HF/video extras, or shared remote services as optional or
  credential-gated unless the user explicitly supplies access.
- Do not claim backend parity from a local CPU/SQLite run.
- Do not overwrite generated repo skill directories or live managed skills from
  maintainer scripts; refresh/import workflows are owned by DisCo meta skills.
- Do not include local environment paths, secrets, or machine-specific checkout
  paths in public docs or skill content.

## Native Verification Candidates Owned Here

- Optional-dependency import gate: base `import datachain` must not require torch,
  while `datachain.torch` should explain the missing `torch` extra.
- CLI/skill/knowledge tests for changes under `src/datachain/cli` or
  `src/datachain/skill`.
- Signal/schema/type conversion tests for changes under `lib/convert`,
  `lib/signal_schema`, `data_storage`, `sql`, and query operations.
- `nox -s tests -- <focused pytest path>` for a selected subset after narrow
  pytest commands pass.
