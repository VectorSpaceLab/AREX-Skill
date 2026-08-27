---
name: sdk-pipelines
description: "Guides DataChain ingestion, UDF pipelines, datasets, exports, LLM
  operations, and optional ML integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SDK Pipelines

Use this sub-skill when the user asks for Python DataChain SDK code: reading
files or structured data, building lazy chains, writing UDFs, saving versioned
datasets, exporting outputs, using `datachain.llm`, or debugging checkpoint,
delta, retry, File, and DataModel behavior.

## Trigger Phrases

Load this sub-skill for prompts containing or implying:

- `read_storage`, `read_csv`, `read_json`, `read_parquet`, `read_database`,
  `read_pandas`, `read_records`, `read_values`, `read_hf`, or `read_zarr`;
- `map`, `gen`, `agg`, `setup`, `Mapper`, `Generator`, `Aggregator`, return
  type, `params=`, `output=`, multiprocessing, cache, prefetch, or checkpoints;
- `.save()`, `.persist()`, `read_dataset`, dataset versioning, namespace,
  project, metrics, parameters, delta, retry, or multi-stage pipelines;
- `to_pandas`, `to_csv`, `to_json`, `to_jsonl`, `to_parquet`, `to_database`,
  `to_storage`, `to_pytorch`, `to_values`, or `to_list`;
- `File`, `ImageFile`, `TextFile`, `AudioFile`, `VideoFile`, nested Pydantic
  models, `DataModel`, schema flattening from user return types;
- `datachain.llm.complete`, `classify`, `score`, `embed`, model selection,
  usage columns, retries/fallbacks, provider credentials, or LLM caching;
- optional extras such as `datachain[torch]`, `datachain[hf]`, `datachain[video]`,
  `datachain[vector]`, and failure messages from those optional imports.

## First Decision

1. **Need API signatures or parameter rules** → read
   [api-reference](references/api-reference.md).
2. **Need an end-to-end SDK recipe** → read
   [workflows](references/workflows.md). Start from saved datasets when reusable;
   use raw storage only when no existing dataset covers the input.
3. **Need typed files, nested outputs, or UDF parameter binding** → read
   [data-models-and-files](references/data-models-and-files.md).
4. **Need LLM or embedding operations** → read
   [llm-operations](references/llm-operations.md). LLM calls are UDF-like,
   expensive, cached, and should normally be saved before task-specific filters.
5. **Need failure diagnosis** → read [troubleshooting](references/troubleshooting.md),
   then run [local_io_smoke.py](scripts/local_io_smoke.py) or
   [delta_retry_smoke.py](scripts/delta_retry_smoke.py) only as tiny local checks.

## Core Operating Rules

- Prefer `import datachain as dc`. Import `model` or Pydantic types only when
  needed for annotations or schemas.
- A chain is lazy. Terminal operations such as `.save()`, `.show()`,
  `.to_values()`, `.to_pandas()`, and file/database exports trigger execution.
- Chain operations return a new chain. Assign or continue chaining the return
  value; do not assume `filter`, `map`, `mutate`, or `select` mutates the
  receiver.
- Any pipeline stage that runs a Python UDF, model, LLM, or expensive I/O should
  end with `.save("descriptive_name")`. Reuse it later with `dc.read_dataset`.
- Save full expensive results before applying problem-specific filters; filters
  after the saved stage preserve compute for later tasks.
- Every UDF must have a known output type. Prefer a named function with a return
  annotation; use `output=` for non-`str` lambdas or callables you cannot
  annotate.
- Use `params=["file.path"]` or other nested column paths for metadata-only UDFs
  so DataChain does not download file contents just to inspect metadata.
- Use `setup()` for heavy resources such as models or clients. Avoid module-level
  lazy globals in parallel workers.
- Use Query Engine operations for column math, grouping, filtering, and ranking;
  reroute to sibling [`query-engine`](../query-engine/SKILL.md) for details.

## Boundaries and Reroutes

- This sub-skill owns Python SDK pipeline authoring, UDFs, saves, exports,
  File/DataModel types, checkpoints/delta/retry, and LLM operation usage.
- For native SQL-like operations, function families, schema/backend divergence,
  or vector ranking once embeddings already exist, read
  [`query-engine`](../query-engine/SKILL.md).
- For `datachain` command-line usage, Studio auth/jobs/pipelines, or environment
  variables as CLI behavior, read [`cli-and-studio`](../cli-and-studio/SKILL.md).
- For bundled DataChain coding-agent skills, target install layouts, or
  `dc-knowledge/`, read [`agent-harness`](../agent-harness/SKILL.md).
- For source edits, nox, focused tests, or backend-sensitive contributor
  invariants, read [`repo-development`](../repo-development/SKILL.md).

## Native Verification Candidates Owned Here

- Base import without optional torch dependencies: optional dependency guidance
  should match the `Missing dependencies for torch` import error.
- Local read/write fixtures: CSV boolean inference, nested model CSV flattening,
  `read_values` + `map/setup` smoke, and tiny save/read_dataset flows.
- Delta/retry examples should be verified with synthetic tiny fixtures rather
  than cloud buckets or long-running examples.
- LLM examples require provider credentials and should be tested as guidance or
  parser contracts unless explicit credentials and budget are supplied.

## Safety Rules

- Do not use original repository examples or tests as runtime dependencies. This
  subtree contains distilled recipes and tiny bundled helpers.
- Do not print cloud credentials, Studio tokens, LLM API keys, or local
  environment paths in generated code or answers.
- Do not run cloud, Studio, model-download, GPU, or credentialed examples unless
  the user explicitly provides access and approves the cost/side effects.
- Do not treat a local CPU smoke as proof that optional cloud, Studio, GPU, or
  provider-backed workflows are verified.
