# Question Answering Workflows

## Purpose

Read this when you need to run or debug KAG query-time reasoning over an existing project.

## Typical flow

1. Confirm the project was built and the schema/index state matches the query workload.
2. Inspect the solver config with `scripts/inspect_solver_config.py`.
3. Choose the right pipeline.
4. Run a query with `knext reasoner execute` or the Python solver API.
5. Check the trace and references before you change the pipeline.

## Query surfaces

### Python API

Use the solver API when you want to call KAG from Python code.

The source `SolverMain` class is the main entry point for a full query run. It accepts project identity, a task id, the query text, the host address, and optional parameters.

### `knext reasoner execute`

Use `knext reasoner execute` when you want to submit a GQL/DSL query directly to the OpenSPG-backed reasoner.

- `--dsl` accepts a one-line or quoted DSL string.
- `--file` accepts a file path.
- Use exactly one of them.
- `--output` writes the result to a file when supported.

### `knext thinker execute`

Use `knext thinker execute` when the task is a thinker-style reasoning call with subject/predicate/object fields.

## Pipeline selection

### `index_pipeline`

Use when the result should be dominated by references and direct evidence.

### `kag_static_pipeline`

Use for a more deterministic planner/executor flow.

### `kag_iterative_pipeline`

Use when the question needs iterative sub-question refinement.

### `naive_rag_pipeline`

Use as a baseline when graph reasoning is not needed.

### `naive_generation_pipeline`

Use when retrieval is not needed and the query only needs generation.

### `self_cognition_pipeline`

Use when the config asks the system to answer from its own cognition path before falling back to a retrieval pipeline.

### `mcp_pipeline`

Use when the query should be delegated to configured MCP tools.

## What to check when answers look wrong

- the built project id and host address
- whether the selected pipeline matches the task
- whether the retrievers assembled from `chat.index_list` or KB config are the ones you wanted
- whether the schema and indexes were actually committed before the query run
- whether the config has the `llm` or `vectorize_model` values the pipeline expects
