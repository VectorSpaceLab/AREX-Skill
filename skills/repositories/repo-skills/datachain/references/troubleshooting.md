# Cross-Cutting DataChain Troubleshooting

Start here when the failure spans multiple DataChain surfaces. Then route to the
nearest sub-skill troubleshooting page for details.

## Choose the Right Troubleshooting Owner

| Problem shape | Read next |
| --- | --- |
| Python SDK code, readers, UDFs, `.save()`, exports, LLM calls, optional ML extras | `sub-skills/sdk-pipelines/references/troubleshooting.md` |
| Query operators, `datachain.func`, nested field resolution, schema mapping, backend differences | `sub-skills/query-engine/references/troubleshooting.md` |
| CLI commands, Studio auth/jobs/pipelines, dataset/storage commands, environment variables | `sub-skills/cli-and-studio/references/troubleshooting.md` |
| Agent skill install, target layouts, `dc-knowledge/`, CAST/data-harness behavior | `sub-skills/agent-harness/references/troubleshooting.md` |
| Source checkout maintenance, nox/pytest, optional extras, backend-sensitive code changes | `sub-skills/repo-development/references/troubleshooting.md` |

## Package and Environment

- Minimal import check: `python -c "import datachain as dc; print(dc.__version__)"`.
- CLI check: `datachain --help`.
- Use `scripts/check_env.py` for a read-only environment report and optional
  extra probes.
- A missing optional import such as `datachain.torch` is not a base package
  failure when DataChain says to install the matching extra.
- Keep local virtualenv/conda paths and package install locations out of user
  documentation and final answers unless the user explicitly asks for local
  debugging details.

## Data Access and Credentials

- Public buckets often require `anon=True`; private buckets require normal cloud
  credentials or `client_config`.
- Never print or commit Studio tokens, cloud access keys, or LLM provider keys.
- `datachain auth token` prints a secret; use it only when the user intentionally
  asks to view/copy it.
- Cloud storage, Studio, LLM, and model-download workflows are not verified by a
  local `read_values` smoke.

## Dataset and Pipeline Semantics

- Chains are lazy and immutable. Reassign or continue using the returned chain
  from each operation.
- UDF/model/LLM stages should normally be saved with `.save("name")` before
  problem-specific filters.
- Use `persist()` only for anonymous, script-local materialization.
- Use Query Engine operations instead of pandas/materialized Python loops for
  filtering, sorting, grouping, joins, and expression columns.
- Checkpoints depend on script path and chain hash. `DATACHAIN_IGNORE_CHECKPOINTS=1`
  forces a fresh run.

## Backend Parity

- Local SQLite is the default development backend; Studio uses ClickHouse for
  many workflows; future backends may include BigQuery, Snowflake, and Postgres.
- Nullability, NaN, array/map `None` handling, hash functions, regex dialects,
  random values, and some join/expression semantics are backend-sensitive.
- Verify read-back values on the target backend. Schema display alone does not
  prove stored data matches the intended logical type.

## Stale Skill Signals

Refresh this repo skill when:

- the current DataChain checkout commit differs from `repo-provenance.md`;
- source, docs, tests, package metadata, CLI entry points, environment variables,
  or bundled agent skills changed since generation;
- a sub-skill route is missing a new public workflow or optional extra;
- verification failures show runtime guidance depends on older behavior.
