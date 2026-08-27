# Core Memory API Reference

Verified against the installed Cognee package and source inspection.

## Public signatures

### `remember`

```python
remember(
    data,
    dataset_name: str = "main_dataset",
    *,
    dataset_id: UUID | None = None,
    session_id: str | None = None,
    chunk_size: int | None = None,
    chunker: Any | None = None,
    custom_prompt: str | None = None,
    run_in_background: bool = False,
    self_improvement: bool = True,
    session_ids: list[str] | None = None,
    dry_run: bool = False,
    **kwargs,
)
```

Notable points:
- Accepts text, file paths, file-like objects, `DataItem`, memory entries, and
  memory sources.
- `session_id` switches to session-backed memory.
- `dry_run=True` avoids the expensive LLM path for supported permanent-memory flows.
- `RememberResult` is promise-like and can be awaited if the call is backgrounded.

### `recall`

```python
recall(
    query_text: str,
    query_type: SearchType | None = None,
    *,
    datasets: list[str] | None = None,
    dataset_ids: list[UUID] | None = None,
    top_k: int = 15,
    auto_route: bool = True,
    scope: str | list[str] | None = None,
    system_prompt: str | None = None,
    system_prompt_path: str = "answer_simple_question.txt",
    node_name: list[str] | None = None,
    node_name_filter_operator: str = "OR",
    only_context: bool = False,
    session_id: str | None = None,
    context_profile: str = "qa",
    wide_search_top_k: int | None = 100,
    triplet_distance_penalty: float | None = 6.5,
    feedback_influence: float = 0.0,
    verbose: bool = False,
    retriever_specific_config: dict | None = None,
    neighborhood_depth: int | None = None,
    neighborhood_seed_top_k: int | None = None,
    include_references: bool = False,
    user: object | None = None,
    llm_config: LLMConfig | None = None,
    embedding_config: EmbeddingConfig | None = None,
)
```

Notable points:
- Session-aware when `session_id` is provided.
- `scope` defaults to auto routing across session/graph sources.
- `auto_route=True` may choose a better search type when `query_type` is omitted.

### `add`, `cognify`, `search`, `improve`, `forget`

See the root API signatures in the installed package for the exact parameter list.
The key behavior for this sub-skill is the workflow relationship:

- `add` ingests raw data into a dataset.
- `cognify` transforms ingested content into graph structure.
- `search` queries the processed graph.
- `improve` enriches an existing dataset or session bridge.
- `forget` removes content or datasets.

## Important result types

- `RememberResult`: promise-like wrapper with `status`, `dataset_name`, `dataset_id`,
  `session_ids`, `pipeline_run_id`, `items_processed`, `elapsed_seconds`, and `error`.
- `SearchType`: enum used by `recall`/`search` to select retrieval mode.

## Practical notes

- `recall(scope="graph_context")` is deprecated in favor of `scope="graph"`.
- `code_query` is only valid when `query_type=SearchType.CODE`.
- `skills` and `tools` require `SearchType.AGENTIC_COMPLETION`.
- Validation is strict about positive integer arguments for some retrieval knobs.
