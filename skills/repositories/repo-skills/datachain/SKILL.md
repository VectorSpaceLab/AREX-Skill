---
name: datachain
description: "Routes DataChain operating guidance for Python SDK pipelines,
  query expressions, CLI and Studio commands, agent-harness knowledge workflows,
  and repository maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DataChain

Use this repo skill when a task involves DataChain: wrangling unstructured AI
data, turning files or tables into typed versioned datasets, composing
warehouse-backed query operations, running DataChain CLI/Studio commands,
installing DataChain's bundled coding-agent skills, or maintaining the
DataChain source repository.

DataChain's core model is a lazy `DataChain` over typed signals. Signals may be
scalars, file objects, or nested Pydantic/DataChain models; saved datasets carry
schema, lineage, and version metadata so later sessions can reuse them.

## Fast Route

- **Python SDK pipeline authoring**: reading storage/CSV/JSON/Parquet/database,
  writing `map`/`gen`/`agg` UDFs, saving datasets, exporting results,
  checkpoints, delta/retry, File/DataModel types, LLM operations, optional ML
  extras → read [`sdk-pipelines`](sub-skills/sdk-pipelines/SKILL.md).
- **Native query expressions**: `filter`, `select`, `mutate`, `group_by`,
  `merge`, `union`, `diff`, `datachain.func`, window functions, vector
  distances, nested field resolution, backend parity, or schema mapping bugs →
  read [`query-engine`](sub-skills/query-engine/SKILL.md).
- **CLI and Studio operations**: `datachain --help`, storage/dataset commands,
  `show`, `gc`, auth, jobs, pipelines, command parser behavior, local vs Studio
  flavor flags, environment variables → read
  [`cli-and-studio`](sub-skills/cli-and-studio/SKILL.md).
- **Agent harness and knowledge base**: `datachain skill install|list|uninstall`,
  Claude/Cursor/Codex/Pi/Copilot target layouts, `dc-knowledge/`, bundled
  `core`/`knowledge`/`jobs` skills, CAST-style dataset layering, agent data
  workflows → read [`agent-harness`](sub-skills/agent-harness/SKILL.md).
- **Repository maintenance**: editing DataChain source, nox/pytest, package
  extras, contribution workflow, backend-sensitive source changes, signal→column
  matrix, stale skill checks → read
  [`repo-development`](sub-skills/repo-development/SKILL.md).

## Minimal Checks

For an installed package:

```bash
python -c "import datachain as dc; print(dc.__version__)"
datachain --help
```

For a local DataChain SDK smoke that does not need cloud credentials:

```bash
python sub-skills/sdk-pipelines/scripts/local_io_smoke.py
python sub-skills/query-engine/scripts/query_smoke.py
```

For read-only CLI help checks:

```bash
python sub-skills/cli-and-studio/scripts/cli_help_smoke.py job run
```

For agent skill install layout previews without mutating target directories:

```bash
python sub-skills/agent-harness/scripts/skill_layout_check.py --all-targets --local
```

For source-checkout staleness or maintainer test selection:

```bash
python sub-skills/repo-development/scripts/snapshot_repo_state.py
python sub-skills/repo-development/scripts/select_tests.py src/datachain/func/string.py
```

## Cross-Cutting Safety

- Treat DataChain chains as immutable: every operation returns a new chain.
- Prefer saved datasets for reusable or expensive UDF/model/LLM results; avoid
  bypassing `.save()` by pulling rows into Python and dumping files manually.
- Use native Query Engine operations instead of pandas/Python loops for filters,
  joins, grouping, sorting, and SQL-style derivations.
- Do not run cloud, Studio, LLM-provider, model-download, GPU, destructive, or
  credentialed workflows unless the user explicitly supplies access and approves
  side effects/costs.
- Do not print or store Studio tokens, cloud credentials, model API keys, or
  user secret environment variables.
- A local CPU/SQLite smoke is not proof of ClickHouse, BigQuery, Snowflake,
  Postgres, cloud-provider, Studio, or accelerator behavior.
- When maintaining the repository, backend-sensitive schema or query changes
  require a literal test matrix and value read-back assertions.

## Shared References and Helpers

- Read [`references/repo-provenance.md`](references/repo-provenance.md) before
  deciding whether this generated skill matches a current checkout.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  cross-cutting package, optional dependency, credential, and stale-skill
  failures before diving into a sub-skill-specific troubleshooting page.
- Read [`references/roadmap-and-coverage.md`](references/roadmap-and-coverage.md)
  for selected scope, optional unverified surfaces, and verification baseline.
- Run [`scripts/check_env.py`](scripts/check_env.py) to validate the active
  Python environment and optional extras without touching user data.
- Run [`scripts/inspect_cli.py`](scripts/inspect_cli.py) to inspect the CLI help
  tree safely.

## Import and Refresh Notes

This generated repo skill is self-contained operating knowledge for DataChain's
public package and repository. It does not require the source checkout for
runtime use. If a later checkout changes public APIs, CLI flags, optional extras,
backend behavior, or bundled agent skills, refresh this repo skill before using
it as authoritative guidance.
