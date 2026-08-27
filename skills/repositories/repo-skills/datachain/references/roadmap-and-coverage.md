# Scope, Coverage, and Verification Baseline

This generated DataChain repo skill covers the public operating surface of the
DataChain Python package and repository at the provenance snapshot.

## Included Runtime Coverage

| Area | Owner | Coverage depth |
| --- | --- | --- |
| Python SDK pipelines | `sub-skills/sdk-pipelines` | Readers, UDFs, saves, exports, File/DataModel types, checkpoints, delta/retry, LLM operations, optional ML extras as documented optional surfaces. |
| Query Engine | `sub-skills/query-engine` | Native operations, `datachain.func`, expressions, vector distances, nested schema resolution, backend caveats. |
| CLI and Studio | `sub-skills/cli-and-studio` | Command families, local vs Studio routing, auth/jobs/pipelines, environment variables, read-only help validation. |
| Agent harness | `sub-skills/agent-harness` | Bundled DataChain skills, target layouts, knowledge-base structure, CAST-at-a-glance, data-harness workflow. |
| Repository development | `sub-skills/repo-development` | Contribution setup, nox sessions, focused tests, package extras, signal→column and backend-sensitive change matrix. |

## Explicitly Optional or Unverified Surfaces

The baseline verification environment selected CPU/local SQLite and base package
imports. These surfaces remain documented but not required for baseline import
readiness:

- cloud storage behavior that needs real S3, GCS, Azure, or Hugging Face network
  access and credentials;
- DataChain Studio auth, remote jobs, clusters, scheduled runs, and pipeline
  mutations that need a Studio account/token;
- LLM provider calls that need API keys, network access, and model-call budget;
- optional ML/data extras such as `torch`, `hf`, `video`, `audio`, `vector`,
  `postgres`, `zarr`, `examples`, and benchmark dependencies;
- strict non-SQLite backend runtime parity, especially ClickHouse nullability and
  collection behavior, unless verified in a target backend session.

## Baseline Verification Expectations

Safe final verification should include:

1. Static checks for valid frontmatter, no public local-path leaks, no runtime
   links to original repository docs/examples/tests, valid JSON metadata, and
   import-role fields on every `SKILL.md`.
2. Help checks for all bundled scripts.
3. Default smoke checks for root `scripts/check_env.py`, `scripts/inspect_cli.py`,
   `sdk-pipelines/scripts/local_io_smoke.py`, `query-engine/scripts/query_smoke.py`,
   `query-engine/scripts/schema_probe.py`, and read-only CLI/agent layout helpers.
4. Selected safe native candidates from the repository test suite using the
   prepared environment: CLI parsing, optional torch dependency gate, one native
   expression/mutate assertion, and one local structured read/export fixture if
   dependencies are sufficient.

## When to Refresh or Extend

Refresh this skill after public API, CLI, docs, package metadata, backend
converter, optional-extra, or bundled-agent-skill changes. Extend it when a new
workflow exists but the source snapshot is otherwise current, such as a new
storage backend, new optional integration, or a new agent target layout.
