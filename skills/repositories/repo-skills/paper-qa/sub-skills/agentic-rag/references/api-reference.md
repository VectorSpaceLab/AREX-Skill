# Agentic RAG API Reference

Verified against installed `paper-qa==2026.8.12` and `paper-qa-pypdf==2026.8.12` package facts. These are runtime-facing facts only; for model/provider configuration details see [settings-and-configuration](../../settings-and-configuration/SKILL.md).

## Public imports

```python
from paperqa import Docs, Doc, Text, Context, PQASession, Settings, ask, agent_query
from paperqa.agents.models import AnswerResponse, AgentStatus
```

`paperqa.__all__` exports `Docs`, `Doc`, `DocDetails`, `Text`, `Context`, `PQASession`, `Settings`, vector stores, LMI model types, `ask`, `agent_query`, and `get_settings`.

## Core object shapes

### `Doc`

Construct manually when you already know the citation and want to avoid metadata inference:

```python
Doc(docname="smith2024", dockey="smith-2024", citation="Smith et al., 2024")
```

Required fields:

| Field | Purpose |
| --- | --- |
| `docname: str` | Human/citation key used in `Text.name` and answer references. |
| `dockey: Any` | Stable unique key in `Docs.docs`; duplicates with the same key are skipped. |
| `citation: str` | Formatted citation string used for evidence and bibliography. |

Optional fields include `content_hash` and metadata overwrite controls. `Doc.formatted_citation` returns `citation`.

### `Text`

`Text` represents a pre-chunked retrievable unit:

```python
Text(text="The intervention improved survival.", name="smith2024 chunk 1", doc=doc)
```

Required fields:

| Field | Purpose |
| --- | --- |
| `text: str` | Chunk text. |
| `name: str` | Chunk/source name. Keep it unique and cite-like. |
| `doc: Doc | DocDetails` | Source document object. |

Optional fields include `embedding`, `media`, and extra metadata. `Text.get_embeddable_text(with_enrichment=False)` returns text for embedding.

### `Docs`

Installed constructor:

```text
Docs(*, id=<uuid>, docs={}, texts=[], docnames=set(), texts_index=NumpyVectorStore(), name='default', deleted_dockeys=set())
```

Important fields:

| Field | Shape | Purpose |
| --- | --- | --- |
| `docs` | `dict[dockey, Doc | DocDetails]` | Documents known to this collection. |
| `texts` | `list[Text]` | Chunked texts available for retrieval. |
| `docnames` | `set[str]` | Used to rename duplicate docnames by suffixing `a`, `b`, ... |
| `texts_index` | `VectorStore` | Built lazily for retrieval when embeddings are available. |

Verified public methods are async in this installation: `aadd`, `aadd_file`, `aadd_url`, `aadd_texts`, `aget_evidence`, `aquery`, `retrieve_texts`, and `delete`. The README names sync aliases (`add`, `query`, etc.) historically, but the verified installed `Docs` class exposes the async methods above; prefer `await`.

### `PQASession`

`PQASession` is both an input carrier and output record:

| Field | Shape | Meaning |
| --- | --- | --- |
| `id` | UUID | Session id used in LLM call tracking. |
| `question` | `str` | Original user question. |
| `contexts` | `list[Context]` | Evidence summaries with scores and linked texts. |
| `context` | `str` | Serialized final context string sent to answer generation. |
| `raw_answer` | `str` | Raw answer containing context ids before citation formatting. |
| `answer` | `str` | Answer text after replacing citation ids with readable source names. |
| `formatted_answer` | `str` | User-facing question + answer + references. |
| `references` | `str` | Bibliography text populated from used contexts. |
| `has_successful_answer` | `bool | None` | Agent certainty marker: `True`, `False`, or not completed. |
| `token_counts`, `cost` | dict/float | Usage accounting from LLM calls. |
| `tool_history` | `list[list[str]]` | Agent tool names called at each step. |

`session.populate_formatted_answers_and_bib_from_raw_answer()` maps raw context ids like `pqac-...` to chunk names and references.

### `Context`

`Context(context=..., question=..., text=..., score=...)` stores one evidence summary. Scores usually use a 0-10 relevance scale; evidence with score `<= 0` is filtered during retrieval.

## Verified method signatures and return shapes

### `Docs.aadd`

```text
Docs.aadd(self, path: str | os.PathLike, citation: str | None = None, docname: str | None = None, dockey: DocKey | None = None, title: str | None = None, doi: str | None = None, authors: list[str] | None = None, settings: MaybeSettings = None, llm_model: LLMModel | None = None, embedding_model: EmbeddingModel | None = None, **kwargs) -> str | None
```

Adds a local file path after parsing/chunking. Returns the final `doc.docname` when added, or `None` if the document is already present. If `citation` is omitted, PaperQA peeks at the first chunk and asks the configured `llm` to infer a citation. If parsing uses document details and `title` or `doi` is present, metadata providers may be queried unless configured otherwise.

### `Docs.aadd_file`

```text
Docs.aadd_file(self, file: BinaryIO, citation: str | None = None, docname: str | None = None, dockey: DocKey | None = None, title: str | None = None, doi: str | None = None, authors: list[str] | None = None, settings: MaybeSettings = None, llm_model: LLMModel | None = None, embedding_model: EmbeddingModel | None = None, **kwargs) -> str | None
```

Accepts a binary file-like object, writes it to a temporary file with an inferred suffix, and delegates to `aadd`. Same return shape and caveats as `aadd`.

### `Docs.aadd_url`

```text
Docs.aadd_url(self, url: str, citation: str | None = None, docname: str | None = None, dockey: DocKey | None = None, settings: MaybeSettings = None, llm_model: LLMModel | None = None, embedding_model: EmbeddingModel | None = None) -> str | None
```

Downloads the URL and delegates to `aadd_file`. This is a network operation; do not use it for no-network or untrusted URL smokes.

### `Docs.aadd_texts`

```text
Docs.aadd_texts(self, texts: list[Text], doc: Doc, settings: MaybeSettings = None, embedding_model: EmbeddingModel | None = None) -> bool
```

Adds pre-chunked `Text` instances and the matching `Doc`. Returns `True` when added, `False` when `doc.dockey` is already in `docs.docs`. Raises `ValueError("No texts to add.")` for an empty list.

Embedding behavior:

- If `settings.parsing.defer_embedding` is `False` and `embedding_model` is not provided, PaperQA calls `settings.get_embedding_model()` immediately.
- If `defer_embedding=True`, texts can be stored with `embedding=None`; embeddings are created later by retrieval if an embedding model is available.
- If `doc.docname` collides with an existing docname, PaperQA renames the incoming docname by suffixing `a`, `b`, ... and updates `Text.name` occurrences.

### `Docs.aget_evidence`

```text
Docs.aget_evidence(self, query: PQASession | str, settings: MaybeSettings = None, callbacks: Sequence[Callable] | None = None, embedding_model: EmbeddingModel | None = None, summary_llm_model: LLMModel | None = None, partitioning_fn: Callable[[Embeddable], int] | None = None) -> PQASession
```

Retrieves and summarizes evidence. Input may be a string or an existing `PQASession`; the returned session contains appended `contexts`, usage data, and the original or supplied `question`. If there are no `docs` and the `texts_index` is empty, it returns the session without contexts.

Important settings:

- `answer.evidence_k`: number of retrieved matches.
- `answer.evidence_retrieval`: if `False`, process all stored texts instead of vector retrieval.
- `answer.evidence_skip_summary`: if `True`, evidence contexts use raw chunk text and can avoid summary LLM calls.
- `answer.max_concurrent_requests`: max concurrent context-summary LLM calls.
- `prompts.use_json`: selects JSON summary parsing vs raw score extraction.

### `Docs.aquery`

```text
Docs.aquery(self, query: PQASession | str, settings: MaybeSettings = None, callbacks: Sequence[Callable] | None = None, llm_model: LLMModel | None = None, summary_llm_model: LLMModel | None = None, embedding_model: EmbeddingModel | None = None, partitioning_fn: Callable[[Embeddable], int] | None = None) -> PQASession
```

Generates a final answer. If `answer.get_evidence_if_no_contexts` is true and the input session has no contexts, it first calls `aget_evidence`. Output fields to inspect:

```python
session.answer            # answer text alone
session.formatted_answer  # question + answer + references
session.context           # serialized evidence context sent to the answer LLM
session.contexts          # Context objects used/available
session.references        # bibliography assembled from used contexts
session.has_successful_answer  # only set by agent completion, not plain aquery
```

If no usable contexts are present, `aquery` sets an answer that includes the unable-to-answer phrase and distinguishes no papers vs insufficient information.

### `ask`

```text
ask(query: str | MultipleChoiceQuestion, settings: Settings) -> AnswerResponse | asyncio.Task[AnswerResponse]
```

Convenience wrapper around `agent_query(query, settings, agent_type=settings.agent.agent_type)`. It configures logging and uses PaperQA's `run_or_ensure`: outside an event loop it blocks and returns `AnswerResponse`; inside a running loop it returns an `asyncio.Task` that must be awaited.

### `agent_query`

```text
agent_query(query: str | MultipleChoiceQuestion, settings: Settings, docs: Docs | None = None, agent_type: str | type = 'ToolSelector', **runner_kwargs) -> AnswerResponse
```

Runs the agent over supplied `docs` or a new `Docs()`. Returns `AnswerResponse(session=PQASession, status=AgentStatus, ...)` and also saves the answer response into an `answers` search index under the configured agent index directory.

`agent_type` options verified in tests include:

| Value | Meaning |
| --- | --- |
| `'fake'` | Deterministic lower-token path: search queries, gather evidence, generate answer, complete. |
| `'ToolSelector'` or `aviary.core.ToolSelector` | Default LLM tool-selection agent. |
| LDP agent type path/class | Advanced agent route when optional LDP dependencies are installed. |

`runner_kwargs` can include callbacks accepted by lower runners, such as `on_env_reset_callback`, `on_agent_action_callback`, and `on_env_step_callback`.

## Agent response objects

`AnswerResponse` constructor shape:

```text
AnswerResponse(*, answer: PQASession, bibtex: dict[str, str] | None = None, status: AgentStatus, timing_info: dict[str, dict[str, float]] | None = None, duration: float = 0.0, stats: dict[str, str] | None = None)
```

The Pydantic alias for `session` is `answer`, so serialized responses may use either naming depending on dump options. `AnswerResponse.session` is filtered for user display: context text and embeddings are dropped from nested contexts, but doc metadata remains.

`AgentStatus` values:

- `success`: answer generated and marked successful.
- `unsure`: answer exists but the agent completed as unsure or generated an unsuccessful answer.
- `truncated`: timeout or max steps triggered; PaperQA falls back to generating an answer.
- `fail`: unhandled trajectory failure.

## Agent tools and callback names

Default installed tool names are:

```text
paper_search, gather_evidence, gen_answer, reset, complete
```

Available tool classes also include `clinical_trials_search`, which belongs mainly with metadata/source workflows.

`Settings.agent.callbacks` is a mapping of callback-name to callables. Accepted names in the installed settings docs include:

| Callback key | Called by |
| --- | --- |
| `gather_evidence_initialized` | Before `GatherEvidence.gather_evidence`. Callable receives `EnvironmentState`. |
| `gather_evidence_aget_evidence` | Passed as LLM streaming callbacks inside `Docs.aget_evidence`. Callable receives LLM chunks. |
| `gather_evidence_completed` | After evidence gathering. Callable receives `EnvironmentState`. |
| `gen_answer_initialized` | Before `GenerateAnswer.gen_answer`. Callable receives `EnvironmentState`. |
| `gen_answer_aget_query` | Passed as LLM streaming callbacks inside `Docs.aquery`. Callable receives LLM chunks. |
| `gen_answer_completed` | After answer generation. Callable receives `EnvironmentState`. |

For direct `Docs.aquery(..., callbacks=[...])`, callbacks are passed to LLM calls for streaming chunks.
