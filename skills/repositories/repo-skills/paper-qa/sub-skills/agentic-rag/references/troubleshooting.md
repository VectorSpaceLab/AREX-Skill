# Agentic RAG Troubleshooting

Use this guide for Python API RAG failures around `Docs`, `Doc`, `Text`, `ask`, `agent_query`, evidence sessions, callbacks, and async boundaries.

## Empty docs or no evidence

Symptoms:

- `await docs.aget_evidence(...)` returns a `PQASession` with `contexts == []`.
- `await docs.aquery(...)` answers that it cannot answer because there are no papers or insufficient information.
- The agent's `gather_evidence` tool reports no useful evidence or raises an empty-docs error internally.

Checks:

```python
print(len(docs.docs), len(docs.texts), len(docs.texts_index))
print(session.question, len(session.contexts))
```

Likely causes and fixes:

- No documents were added: call `aadd`, `aadd_file`, or `aadd_texts` first and check the return value.
- `aadd_texts(texts=[], ...)` raises `ValueError("No texts to add.")`; pass at least one `Text`.
- `Docs.aget_evidence` short-circuits when both `docs.docs` is empty and the vector store is empty. If you intentionally use an external prebuilt `texts_index`, construct `Docs(texts_index=that_index)` and query after confirming the index is not empty.
- Evidence exists but is filtered as irrelevant: inspect `Context.score`, lower or review `answer.evidence_relevance_score_cutoff`, and check whether the summary prompt returns parseable relevance scores.
- Retrieval is the bottleneck: temporarily set `settings.answer.evidence_retrieval = False` to process all `docs.texts`; if that works, diagnose embeddings/vector search.

## Duplicate docnames or duplicate dockeys

Symptoms:

- `Docs.aadd(...)` returns `None` or `Docs.aadd_texts(...)` returns `False`.
- Expected source name changed from `paper` to `papera` or similar.
- Fewer documents appear than expected.

Behavior:

- `dockey` is the true duplicate key. If `doc.dockey` already exists, `aadd_texts` returns `False`; `aadd` returns `None` after duplicate detection.
- `docname` collisions are renamed automatically by suffixing letters (`a`, `b`, ...), and the incoming `Text.name` values are rewritten when they contain the old docname.

Fixes:

```python
# Give each logical document a stable unique dockey.
doc = Doc(docname="trial2024", dockey="trial2024-arm-a", citation="Trial A, 2024")
added = await docs.aadd_texts(texts, doc, settings=settings)
assert added, "Document key already exists"
```

If replacing a document, delete the old doc first:

```python
docs.delete(docname="trial2024")
# then add replacement with a new dockey or the now-removed dockey
```

## Missing citations trigger LLM or metadata calls

Symptoms:

- Adding a local file unexpectedly calls an LLM.
- Missing API key error occurs during `docs.aadd(...)`, before any query.
- Metadata provider/network errors occur while adding a file.

Causes:

- If `citation` is omitted, `Docs.aadd` peeks at the first chunk and asks `settings.get_llm()` to create a citation.
- If `parsing.use_doc_details=True` and `title` or `doi` is present, PaperQA may use metadata clients to upgrade `Doc` into `DocDetails`.

No-surprise ingest pattern:

```python
settings = Settings(parsing={"defer_embedding": True, "use_doc_details": False})
await docs.aadd(
    "paper.pdf",
    citation="Known Author, Known Title, 2024",
    docname="known2024",
    dockey="known2024-v1",
    settings=settings,
)
```

For richer metadata intentionally, use [metadata-and-sources](../../metadata-and-sources/SKILL.md).

## API keys and LLM provider errors

Symptoms:

- OpenAI/Anthropic/Gemini/LiteLLM authentication errors.
- `aget_evidence` fails during context summaries.
- `aquery` fails during answer generation.
- `agent_query` fails during agent tool selection.

Which model role is involved:

| Operation | Model setting usually used |
| --- | --- |
| Citation inference in `aadd` | `settings.llm` |
| Evidence summaries in `aget_evidence` / `gather_evidence` | `settings.summary_llm` |
| Final answer in `aquery` / `gen_answer` | `settings.llm` |
| Agent tool selection in default `ToolSelector` | `settings.agent.agent_llm` |
| Embedding retrieval | `settings.embedding` |

Fixes:

- Confirm credentials for every role actually in use, not just `llm`.
- For agent workflows, set `llm`, `summary_llm`, and `agent.agent_llm` consistently when switching providers.
- If using local providers or non-default embeddings, follow [settings-and-configuration](../../settings-and-configuration/SKILL.md).
- For a structural no-provider test, run `scripts/smoke_docs_objects.py smoke`; do not use it as evidence that live providers work.

## Embedding failures

Symptoms:

- Errors from `settings.get_embedding_model()` or embedding provider.
- `aget_evidence` fails even though adding pre-chunked texts worked.
- Vector store remains empty until retrieval, then fails.

Causes and fixes:

- `aadd_texts` with `Settings(parsing={"defer_embedding": True})` stores texts without embeddings; retrieval later embeds them.
- If `defer_embedding=False`, PaperQA embeds during `aadd_texts` unless you pass an explicit `embedding_model` or pre-populated embeddings.
- If only testing object plumbing, set `answer.evidence_retrieval=False` and `answer.evidence_skip_summary=True`; this avoids retrieval embeddings and summary LLM calls.
- If real retrieval is needed, configure a valid embedding provider or local embedding model in [settings-and-configuration](../../settings-and-configuration/SKILL.md).

Minimal diagnostic:

```python
print(settings.embedding, settings.embedding_config)
print(any(t.embedding is None for t in docs.texts))
```

## Async and nested event loops

Symptoms:

- `RuntimeError: asyncio.run() cannot be called from a running event loop`.
- `ask(...)` returns a `Task` instead of an `AnswerResponse`.
- Calls appear to do nothing in a notebook because the returned task was not awaited.

Fixes:

- In scripts, wrap async code once with `asyncio.run(main())`.
- In notebooks, IPython, FastAPI, or any running event loop, use `await docs.aquery(...)` directly.
- If using `ask(...)` inside an async context, do:

```python
response = await ask("question", settings=settings)  # ask returned a Task
```

- Do not create multiple nested loops to drive PaperQA methods. Prefer native async APIs over sync convenience wrappers.

## Callback confusion

Symptoms:

- Direct callback receives string chunks, but agent callback expected `EnvironmentState`.
- Async lifecycle callbacks are never called.
- Callback key spelling has no effect.

Use the correct surface:

- `Docs.aquery(..., callbacks=[fn])` and `Docs.aget_evidence(..., callbacks=[fn])` pass LLM streaming chunks to `fn`.
- `Settings.agent.callbacks["gather_evidence_initialized"]` and similar lifecycle callbacks receive `EnvironmentState` and are awaited by tools.
- `Settings.agent.callbacks["gather_evidence_aget_evidence"]` and `"gen_answer_aget_query"` are LLM streaming callbacks forwarded inside the tools.
- `agent_query(..., on_agent_action_callback=...)` receives agent action objects and runner state/ledger, depending on the agent route.

Known callback keys are listed in [api-reference.md](api-reference.md#agent-tools-and-callback-names).

## Impossible parsing or corrupt document inputs

Symptoms:

- `ValueError` about empty documents or not looking like text.
- PDF/image/Office parser import errors.
- Media extraction or multimodal enrichment fails.
- `aadd_file` cannot infer usable file type from a binary stream.

This sub-skill only covers the RAG API surface. For parser selection, optional parser packages, chunking options, corrupt PDFs, media extraction, image/table enrichment, and Office/code/html parsing details, switch to [docs-and-parsing](../../docs-and-parsing/SKILL.md).

Short API-side mitigations:

- Provide `citation`, `docname`, and `dockey` so metadata/citation inference is not mixed with parser diagnosis.
- Try a known-good `.txt` file or pre-chunked `Text` via `aadd_texts` to distinguish parser failure from RAG failure.
- Avoid `aadd_url` while diagnosing parser behavior because it adds network/download failure modes.

## Answer status uncertainty

Symptoms:

- `AnswerResponse.status` is `unsure` or `truncated`, but `response.session.answer` is non-empty.
- The final answer says it cannot answer, even with some contexts.
- `PQASession.has_successful_answer` is `None` after direct `Docs.aquery`.

Interpretation:

- Direct `Docs.aquery` does not run the agent `complete` tool, so `has_successful_answer` may remain unset.
- `agent_query` returns `AnswerResponse.status`; status may be `success`, `unsure`, `truncated`, or `fail`.
- On timeout or max-step truncation, PaperQA tries a failover answer, so non-empty text does not guarantee confidence.
- The `complete` tool can mark `has_successful_answer=False`, yielding an uncertain answer.

Robust check:

```python
response = await agent_query("question", settings=settings)
print(response.status, response.session.has_successful_answer)
print(response.session.answer)
print(response.session.references)
```

If status is not `success`, review `session.contexts`, `tool_history`, and whether the agent had enough papers/evidence before `gen_answer` or `complete`.

## Missing references or malformed citations in answers

Symptoms:

- `session.answer` mentions claims but `session.references` is empty.
- Raw answer includes unknown `pqac-...` ids or hallucinated citations.
- Citations use source names incorrectly.

Causes and fixes:

- `populate_formatted_answers_and_bib_from_raw_answer()` only keeps references for context ids that appear in `raw_answer` and match `session.contexts`.
- Prompt or custom context serializer may not expose valid keys clearly.
- Evidence contexts may have been stripped, deduplicated, or filtered.

Debug:

```python
print(session.raw_answer)
print(session.used_contexts)
for c in session.contexts:
    print(c.id, c.text.name, c.text.doc.formatted_citation)
```

If using a custom serializer, ensure valid `Context.id` values remain visible to the answer prompt, or return to the default serializer.

## Agent index/search surprises

Symptoms:

- `agent_query` with `paper_search` reports no papers.
- `ask` searches a different directory than expected.
- An answer is saved into an `answers` index unexpectedly.

This sub-skill covers the Python call surface, not index management. Operational index details, `PQA_HOME`, `pqa index`, manifests, index names, and stale/corrupt index handling belong to [cli-and-indexing](../../cli-and-indexing/SKILL.md).

API-side checks:

```python
print(settings.agent.index.paper_directory)
print(settings.agent.index.name, settings.agent.index.index_directory)
print(settings.agent.rebuild_index, settings.agent.tool_names)
```

If you do not want `paper_search`, pass existing `docs` and use `agent_type="fake"` only with tool names that make sense, or use direct `Docs.aquery`.
