# Memory Engines

MemMachine combines several memory subsystems. Server configuration controls
which are enabled and which resources back them.

## Episodic Memory

Episodic memory stores conversation-like event history and supports search over
long-term memory plus optional short-term session summaries.

Important controls:

- `episodic_memory.enabled`
- `long_term_memory_enabled`
- `short_term_memory_enabled`
- `episode_store.database`
- `episodic_memory.long_term_memory.*`
- `episodic_memory.short_term_memory.*`

### Long-term Memory Backends

| Backend | Data path | Required resources |
| --- | --- | --- |
| Declarative | graph/vector graph store | embedder, reranker, `vector_graph_store` |
| Event | vector store + segment store | embedder, optional reranker, `vector_store`, `segment_store` |

Event backend can use `properties_schema` for filterable event properties.
If the schema declares custom fields, keep add/search metadata consistent with
those fields.

### Segmenters And Derivers

Event memory can use segmenter/deriver settings. Defaults are intended for
ordinary text, while text/sentence segmenters and derivers may be used for more
fine-grained retrieval. Verify optional dependencies before selecting advanced
text processing.

## Short-term Memory

Short-term memory summarizes recent session state. It needs a language model
resource and capacity settings:

```yaml
short_term_memory:
  llm_model: openai_model
  message_capacity: 64000
```

If short-term summarization fails, check the language-model resource, provider
credentials, model ID, and whether the server has enough context to summarize.

## Semantic/Profile Memory

Semantic memory stores durable facts, categories, tags, and features. It
requires an LLM, embedder, and storage/config databases when enabled.

Common workflow:

1. Define or select a semantic set type.
2. Resolve a semantic set ID from metadata tags.
3. Add categories or templates with prompts.
4. Add/update features and tags.
5. Search or retrieve features through SDK/API calls.

If semantic ingestion is asynchronous, allow for delay between adding raw
memories and seeing semantic/profile facts.

## Retrieval Agent

Retrieval-agent mode is enabled at query time by client/API options such as
`agent_mode=True` or `--agent-mode`. It can route, decompose, or rerank queries
using configured LLM and reranker resources.

Important notes:

- A simple direct search is safer for first checks.
- Retrieval-agent mode needs server-side resources; failures may be provider or
  reranker issues rather than client bugs.
- The optional spaCy multi-hop decomposer is not part of the base install in
  the source baseline. Missing spaCy can produce a non-fatal decomposer warning
  and fallback behavior. Install spaCy/model dependencies only if the user asks
  for that local decomposition path.

## Selecting A Backend For A User Task

- Use event backend when the user wants vector-store-backed episodic events,
  segment-level search, or Qdrant/Milvus/SQLite vector store integration.
- Use declarative backend when the user wants graph-style long-term memory and
  the graph store is available.
- Use semantic memory when the user needs stable user facts/profile categories,
  not just conversational episodes.
- Use short-term memory when the current session context needs summarization.
- Use retrieval-agent mode when a query needs decomposition/reranking and the
  server has LLM/reranker resources.

## Validation Signals

- Health endpoint confirms the server process is reachable.
- Config resources endpoint confirms known resource IDs and statuses when the
  config API is enabled.
- A small add/search round-trip confirms the chosen project, memory subsystem,
  and context metadata.
- Backend-specific tests require actual services/credentials and should be
  classified as optional unless the task demands them.
