# Agentic RAG Workflows

These recipes are self-contained and use the installed Python API. Paths in examples are placeholders that the user supplies at runtime; no recipe depends on any project checkout.

## Choose the right entry point

| Goal | Use | Calls LLMs/embeddings? | Notes |
| --- | --- | --- | --- |
| Prove object construction without network | `scripts/smoke_docs_objects.py smoke` | No | Uses `Docs`, `Doc`, `Text`, `Settings`, `aadd_texts`, and evidence generation without model calls. |
| Use already chunked text | `Docs.aadd_texts` | Ingest can avoid embeddings with `defer_embedding=True`; retrieval later needs embeddings unless retrieval is disabled. | Best for synthetic or pre-parsed content. |
| Add local files | `Docs.aadd` / `Docs.aadd_file` | Usually yes unless citation/metadata/embedding are controlled. | Parser details belong to [docs-and-parsing](../../docs-and-parsing/SKILL.md). |
| Retrieve evidence only | `Docs.aget_evidence` | Embeddings + summary LLM by default. | Returns `PQASession.contexts`; does not produce final answer. |
| Generate final answer over known docs | `Docs.aquery` | Summary LLM, embedding, and answer LLM by default. | Returns `PQASession` with answer/context/references. |
| Agentic paper search and answer | `ask` or `agent_query` | Agent LLM + search/index + embeddings + answer LLM. | CLI/index details belong to [cli-and-indexing](../../cli-and-indexing/SKILL.md). |

## Async boundary pattern

PaperQA's installed `Docs` RAG methods are async. Use `await` when already inside an async function:

```python
import asyncio
from paperqa import Docs, Settings

async def main() -> None:
    docs = Docs()
    settings = Settings()
    await docs.aadd("paper.pdf", citation="Example Author, 2024", settings=settings)
    session = await docs.aquery("What did the paper find?", settings=settings)
    print(session.answer)

asyncio.run(main())
```

In notebooks or web servers, do not call `asyncio.run()` from inside an already running event loop; call `await main()` or `await docs.aquery(...)` directly. `ask(...)` is a convenience wrapper: outside an event loop it blocks; inside a running event loop it returns an `asyncio.Task` that must be awaited.

## No-network object smoke

From this sub-skill directory, or by path from the root skill, run:

```bash
python sub-skills/agentic-rag/scripts/smoke_docs_objects.py --help
python sub-skills/agentic-rag/scripts/smoke_docs_objects.py smoke --json
```

The smoke constructs `Settings(parsing={"defer_embedding": True})`, a `Docs`, a `Doc`, and two `Text` chunks, then calls `Docs.aadd_texts`. It also exercises `Docs.aget_evidence` with `answer.evidence_retrieval=False` and `answer.evidence_skip_summary=True`, passing sentinel model objects so no embedding or LLM provider methods are called.

Use this only to validate installed API shape. It does not prove real parsing, embeddings, provider credentials, answer quality, or index behavior.

## Pre-chunked texts with deferred embeddings

Use this when documents have already been chunked by another trusted process or when you want to stage objects before deciding on an embedding provider.

```python
from paperqa import Docs, Doc, Text, Settings

settings = Settings(
    parsing={"defer_embedding": True, "use_doc_details": False},
)

doc = Doc(
    docname="smith2024",
    dockey="smith-2024-v1",
    citation="Smith et al., Example Study, 2024",
)
texts = [
    Text(text="Treatment A improved survival in cohort 1.", name="smith2024 chunk 1", doc=doc),
    Text(text="Adverse events were mild in the follow-up period.", name="smith2024 chunk 2", doc=doc),
]

docs = Docs()
added = await docs.aadd_texts(texts=texts, doc=doc, settings=settings)
assert added is True
```

Later retrieval can embed lazily:

```python
# This will use settings.get_embedding_model() unless you pass embedding_model=...
session = await docs.aget_evidence("What happened in cohort 1?", settings=settings)
for context in session.contexts:
    print(context.score, context.text.name, context.context)
```

If you need a fully no-network evidence smoke, set both `answer.evidence_retrieval=False` and `answer.evidence_skip_summary=True` and pass explicit sentinel objects for `embedding_model` and `summary_llm_model`, as the bundled smoke script does. That is only a structural smoke, not semantic retrieval.

## Add local files manually

Use `Docs.aadd` for local files and `Docs.aadd_file` for binary streams. Provide citation and stable identifiers when you want to avoid citation-inference LLM calls.

```python
from pathlib import Path
from paperqa import Docs, Settings

settings = Settings(
    parsing={
        "defer_embedding": True,
        "use_doc_details": False,  # avoid metadata-provider hydration during ingest
    }
)

docs = Docs()
for path in [Path("paper1.pdf"), Path("notes.md")]:
    docname = await docs.aadd(
        path,
        citation=f"Local source, {path.name}, 2024",
        docname=path.stem.replace("_", "-")[:40],
        dockey=f"local-{path.stem}",
        settings=settings,
    )
    print("added", docname)
```

Operational notes:

- If `citation` is omitted, `Docs.aadd` asks the configured `llm` to infer a citation from the first parsed chunk.
- If `parsing.use_doc_details=True` and `title` or `doi` is supplied, metadata clients may be used to upgrade `Doc` to `DocDetails`.
- Duplicate `dockey` returns `None` from `aadd` or `False` from `aadd_texts`.
- Duplicate `docname` is renamed automatically by suffixing letters (`doc`, `doca`, `docb`, ...).

## Evidence first, answer later

Split retrieval from answer generation when you want to inspect evidence before spending answer-generation tokens:

```python
from paperqa import PQASession, Settings

settings = Settings.from_name("fast")
settings.answer.evidence_k = 5
settings.answer.answer_max_sources = 3

session = PQASession(question="What outcomes improved?")
session = await docs.aget_evidence(session, settings=settings)

for i, context in enumerate(session.contexts, start=1):
    print(i, context.score, context.text.name)
    print(context.context[:500])

# Reuse inspected contexts for final answer.
session = await docs.aquery(session, settings=settings)
print(session.answer)
print(session.references)
```

`Docs.aquery` will call `aget_evidence` itself if `session.contexts` is empty and `settings.answer.get_evidence_if_no_contexts` is true. Passing an existing `PQASession` lets you preserve prior contexts, question, token/cost accounting, and iterative-answer state.

## Inspect answer/session/source outputs

After `Docs.aquery`, use these fields:

```python
print(session.answer)            # answer alone
print(session.formatted_answer)  # question, answer, references
print(session.references)        # bibliography entries actually cited
print(session.context)           # serialized evidence prompt content
print(session.used_contexts)     # context ids cited in raw_answer

for context in session.contexts:
    source_doc = context.text.doc
    print(context.id, context.score, context.text.name, source_doc.formatted_citation)
```

A final answer only includes references for contexts whose ids appear in `raw_answer`. If references are empty despite evidence existing, inspect `raw_answer`, `session.used_contexts`, and whether the model cited valid `pqac-...` ids.

## Direct callbacks for streaming chunks

Pass `callbacks=[callable]` to `Docs.aget_evidence` or `Docs.aquery` to receive streamed chunks from LLM calls:

```python
chunks: list[str] = []

def capture(chunk: str) -> None:
    chunks.append(chunk)

session = await docs.aquery("What did the study conclude?", settings=settings, callbacks=[capture])
print("".join(chunks))
```

Callbacks here are LLM streaming callbacks. They are not the same as agent lifecycle callbacks below.

## Agentic query with `ask`

`ask` is a convenience wrapper for agentic search + evidence + answer:

```python
from paperqa import Settings, ask

settings = Settings(
    temperature=0.0,
    agent={"index": {"paper_directory": "my_papers"}},
)
response_or_task = ask("What is the evidence for intervention A?", settings=settings)
# In a sync script, response_or_task is AnswerResponse.
# In a running event loop, it is an asyncio.Task and must be awaited.
```

`ask` uses `settings.agent.agent_type`, which defaults to `"ToolSelector"`. It uses the local PaperQA search index configured under `settings.agent.index`; see [cli-and-indexing](../../cli-and-indexing/SKILL.md) for index reuse and manifest behavior.

## Agentic query with explicit `agent_query`

Use `agent_query` when you want to pass an existing `Docs` object or choose an agent type explicitly:

```python
from paperqa import Docs, Settings, agent_query

settings = Settings.from_name("fast")
settings.agent.index.paper_directory = "my_papers"
settings.agent.max_timesteps = 6

# deterministic lower-token tool path: search -> gather_evidence -> gen_answer -> complete
fake_response = await agent_query(
    "How can XAI help chemical property prediction?",
    settings=settings,
    docs=Docs(),
    agent_type="fake",
)
print(fake_response.status, fake_response.session.answer)

# default LLM tool selector
selector_response = await agent_query(
    "Which papers support the claim?",
    settings=settings,
    agent_type="ToolSelector",
)
print(selector_response.status, selector_response.session.tool_history)
```

Interpret status carefully:

- `success`: agent completed and marked answer successful.
- `unsure`: the completion tool or answer checks indicated uncertainty.
- `truncated`: timeout or max steps stopped the agent; PaperQA generated a best-effort answer.
- `fail`: trajectory failed.

Always inspect both `response.status` and `response.session.answer`; a non-empty answer can still be uncertain or truncated.

## Agent lifecycle callbacks

Use `Settings.agent.callbacks` for tool lifecycle hooks and tool-internal LLM streaming callbacks:

```python
from paperqa import Settings, agent_query

async def on_gather_started(state):
    print("papers", len(state.docs.docs), "contexts", len(state.session.contexts))

streamed: list[str] = []
def on_llm_chunk(chunk: str) -> None:
    streamed.append(chunk)

settings = Settings.from_name("fast")
settings.agent.callbacks = {
    "gather_evidence_initialized": [on_gather_started],
    "gather_evidence_aget_evidence": [on_llm_chunk],
    "gen_answer_aget_query": [on_llm_chunk],
}

response = await agent_query("What does the evidence say?", settings=settings, agent_type="fake")
```

Agent runner callbacks can also be passed as `runner_kwargs` to `agent_query`:

```python
async def on_action(action, state_or_ledger):
    print("agent action", action)

response = await agent_query(
    "What should I cite?",
    settings=settings,
    on_agent_action_callback=on_action,
)
```

Use lifecycle callbacks for progress, telemetry, or custom status. Do not rely on them to mutate documents unless you understand agent state ordering.

## Custom context serialization

When the default context prompt is too verbose or you need a special layout, use `Settings.custom_context_serializer`:

```python
from paperqa import Settings

async def custom_context_serializer(settings, contexts, question, pre_str=None):
    rows = [f"- {c.text.name} score={c.score}: {c.context}" for c in contexts]
    return "\n".join(rows)

settings = Settings(custom_context_serializer=custom_context_serializer)
session = await docs.aquery("What is robustly supported?", settings=settings)
print(session.context)
```

Keep serializer output compatible with the answer prompt's citation instructions. If answer citations disappear, compare `session.contexts`, `session.raw_answer`, and `session.references`.

## Deleting or replacing docs

`Docs.delete(docname=...)` removes a document from `docs.docs`, marks its key deleted, and filters associated `texts`. Vector-store cleanup may be lazy depending on store behavior; if you need a clean slate, create a new `Docs()` or call `docs.clear_docs()`.

```python
docs.delete(docname="smith2024")
# or reset everything
docs.clear_docs()
```

## Boundary reminders

- Parser failures, file-format support, multimodal media extraction, and chunking quality are owned by [docs-and-parsing](../../docs-and-parsing/SKILL.md).
- Provider selection, API keys, local model servers, embedding models, prompts, and vector stores are owned by [settings-and-configuration](../../settings-and-configuration/SKILL.md).
- Metadata provider behavior and paper acquisition helpers are owned by [metadata-and-sources](../../metadata-and-sources/SKILL.md).
