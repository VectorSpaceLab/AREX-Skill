# Search and Recall API Reference

Verified against the installed Cognee package and source inspection.

## `search`

```python
search(
    query_text: str,
    query_type: SearchType = SearchType.GRAPH_COMPLETION,
    user: Optional[User] = None,
    datasets: list[str] | str | None = None,
    dataset_ids: list[UUID] | UUID | None = None,
    system_prompt_path: str = "answer_simple_question.txt",
    system_prompt: str | None = None,
    top_k: int = 15,
    node_type: type | None = NodeSet,
    node_name: list[str] | None = None,
    node_name_filter_operator: str = "OR",
    only_context: bool = False,
    session_id: str | None = None,
    wide_search_top_k: int | None = 100,
    triplet_distance_penalty: float | None = 6.5,
    feedback_influence: float = 0.0,
    verbose: bool = False,
    retriever_specific_config: dict | None = None,
    neighborhood_depth: int | None = None,
    neighborhood_seed_top_k: int | None = None,
    skills: list[str | Skill] | None = None,
    tools: list[str] | None = None,
    max_iter: int | None = None,
    include_references: bool = False,
    llm_config: LLMConfig | None = None,
    embedding_config: EmbeddingConfig | None = None,
    code_query: dict[str, Any] | None = None,
)
```

## `recall`

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

## Key validation rules

- `neighborhood_depth` must be a positive integer when set.
- `neighborhood_seed_top_k` must be a positive integer when set.
- `max_iter` must be a positive integer when set.
- `code_query` requires `query_type=SearchType.CODE`.
- `skills` and `tools` require `query_type=SearchType.AGENTIC_COMPLETION`.
- `node_name_filter_operator` must be `AND` or `OR`.

## Return expectations

- Both functions return lists of structured result objects.
- `recall` may return session results, trace results, context results, or graph results depending on scope.
- `search` can also return code-graph or agentic outputs depending on `query_type`.

## Practical guidance

- Use `recall` when the user’s intent is memory-like or session-aware.
- Use `search` when the user wants explicit low-level search control.
- Use `include_references=True` when evidence links matter.
- Route provider/backend failures to [configuration-backends](../../configuration-backends/SKILL.md).
