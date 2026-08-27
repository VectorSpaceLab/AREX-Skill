# Question Answering API Reference

## Purpose

Read this when you need the concrete call shapes behind KAG's query-time solver workflow.

## Verified query entry points

### `SolverMain.invoke`

```python
SolverMain.invoke(
    project_id: int,
    task_id,
    query: str,
    session_id: str = "0",
    is_report: bool = True,
    host_addr: str = "http://127.0.0.1:8887",
    params=None,
    app_id: str = "",
)
```

- synchronous wrapper around the solver flow
- returns the answer text when the run succeeds
- uses the current project config and host address

### `SolverMain.ainvoke`

```python
SolverMain.ainvoke(
    project_id: int,
    task_id: int,
    query: str,
    session_id: str = "0",
    is_report: bool = True,
    host_addr: str = "http://127.0.0.1:8887",
    params=None,
    app_id: str = "",
)
```

- async version of the solver flow
- useful when the surrounding application is already asynchronous

### `qa`

```python
async qa(task_id, query, project_id, host_addr, app_id, params={})
```

- low-level async orchestration function used by `SolverMain`
- handles config setup, reporter selection, pipeline choice, and final answer emission

## CLI query surfaces

### `knext reasoner execute`

- `--dsl` for an inline DSL string
- `--file` for a DSL file path
- `--output` for optional file output
- exactly one of `--dsl` or `--file` must be supplied

### `knext thinker execute`

- `--subject`
- `--predicate`
- `--object`
- `--mode`
- `--params`

## Pipeline names seen in the source

- `index_pipeline`
- `kag_static_pipeline`
- `kag_iterative_pipeline`
- `naive_generation_pipeline`
- `naive_rag_pipeline`
- `self_cognition_pipeline`
- `mcp_pipeline`

## Query-time config keys

Useful keys in the solver config include:

- `chat.ename` to select the active query pipeline in some configs
- `kb` for knowledge-base-specific settings
- `index_list` for retriever selection
- `llm` and `vectorize_model` for the generated reasoning path

## Retrieval assembly note

The solver side builds retrievers from the project's index configuration before the pipeline runs. If a query path is failing, check the build/index side first and then confirm the solver config.
