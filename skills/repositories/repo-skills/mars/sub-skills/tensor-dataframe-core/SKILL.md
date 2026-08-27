---
name: tensor-dataframe-core
description: "Routes Mars tensor, DataFrame, session, eager-mode, and local CPU
  execution requests to the verified array-and-table workflow guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensor and DataFrame Core

Use this sub-skill for the everyday Mars workflows that look like NumPy,
pandas, and a local session: `new_session`, `execute`, `fetch`, `stop_server`,
tensor creation and arithmetic, DataFrame and Series creation, selection,
groupby, and small file-backed IO.

## Trigger phrases

- "How do I start a local Mars session?"
- "How do I run a small tensor or DataFrame computation?"
- "Why does `execute()` return a Mars object?"
- "How do I switch eager mode on or off?"
- "How do I read or write a small CSV, HDF5, or Parquet file?"
- "How do I convert between Mars tensors, DataFrames, NumPy, and pandas?"

## What belongs here

- Local CPU usage and session lifecycle.
- Core tensor and DataFrame constructors, math, reductions, indexing, and
  reshaping.
- `mars.config.options` and `option_context` for eager mode and related
  settings.
- Tiny safe IO examples that do not need external services or credentials.

## What stays elsewhere

- Remote DAGs, logs, or script execution -> `remote-and-scripts`.
- Learn estimators and integrations -> `learn-and-integrations`.
- Ray, GPU, Kubernetes, YARN, or CLI help -> `deployment-and-backends`.

## Read these bundled files

- `references/api-reference.md` for the verified API surface and representative
  signatures.
- `references/workflows.md` for the step-by-step local compute path.
- `references/troubleshooting.md` for install/import, session, IO, and
  path-shadowing failures.
- `scripts/check_tensor_dataframe.py` for a tiny CPU smoke that future agents
  can run without reopening the source repo.

## Minimal route

1. Import `mars`, `mars.tensor as mt`, and `mars.dataframe as md`.
2. Create a local session with `mars.new_session()` when you want repeatable
   execution.
3. Build a tiny tensor or DataFrame.
4. Call `.execute()` and then `.fetch()` only when you want the concrete value.
5. Use `mars.stop_server()` after smoke runs that create a session.

## Common decisions

- Use `.execute()` rather than `.to_numpy()` or `.to_pandas()` for large values.
- Use `option_context({'eager_mode': True})` only when you want immediate
  execution for a short debugging session.
- Treat `groupby`, indexing, and IO as part of the same local workflow, not as
  separate skills.
- If `mars.dataframe` import fails because a shadowed `ray` module is visible,
  fix the environment first instead of rewriting the workflow.

## Quality bar

A future agent should be able to answer the usual local Mars questions from
this sub-skill alone: start a session, run a small tensor or DataFrame example,
understand the execution model, choose between `execute` and `fetch`, and
recover from the most common environment and IO issues.
