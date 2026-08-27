# Brain QA Workflows

## Basic answer path

Use `Brain.aask(...)` when you want a normal answer and are already in an async
context.

```python
from uuid import uuid4

response = await brain.aask(run_id=uuid4(), question="What does the brain know?")
print(response.answer)
print(response.metadata.sources if response.metadata else [])
```

Why this path works:

- `run_id` satisfies the current API and carries trace metadata.
- `Brain.aask(...)` uses the brain's retrieval configuration unless you provide a
  custom one.
- The returned object is a `ParsedRAGResponse`, so you get the answer and the
  metadata together.

## Streaming path

Use `Brain.ask_streaming(...)` when the user wants incremental output or source
metadata at the end of the stream.

```python
from uuid import uuid4

async for chunk in brain.ask_streaming(run_id=uuid4(), question="What is in the document?"):
    if not chunk.last_chunk:
        print(chunk.answer, end="")
    else:
        print("sources:", chunk.metadata.sources)
        print("citations:", chunk.metadata.citations)
```

Remember:

- the final chunk carries metadata,
- `chat_history` is updated after the stream completes,
- and the model-name heuristic determines whether the answer path behaves as a
  tool-calling or plain-text workflow.

## Retrieval inspection

Use `Brain.asearch(...)` when you only want to debug chunk retrieval instead of
running the full answer pipeline.

Typical uses:

- check whether the right documents are in the vector store,
- verify that the query embedding can find the expected chunk,
- and confirm that the chunk metadata still contains readable source labels.

## Config-driven QA

Use `RetrievalConfig.from_yaml(...)` when the user wants to control the workflow
through a YAML file.

Important pieces:

- `llm_config` selects the model and token budget.
- `reranker_config` activates reranking when the supplier key is present.
- `workflow_config` can enable `web search` and bind `cited_answer` on the
  generation node.
- `Brain.aask(..., retrieval_config=...)` and `Brain.ask_streaming(..., retrieval_config=...)`
  both accept that config.

## Web search path

If the workflow enables the web-search tool, confirm all of the following before
promising success:

1. `TAVILY_API_KEY` is set.
2. `available_tools` includes `web search`.
3. The generate node binds `cited_answer` when the workflow expects cited output.

## Chat history path

`ChatHistory.iter_pairs()` expects alternating human and AI messages. If you are
manually constructing history, append messages in that order so the retrieval
history stays valid.
