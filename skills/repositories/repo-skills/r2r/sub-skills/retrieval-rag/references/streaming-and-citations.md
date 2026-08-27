# Streaming and Citations

## Event types

The Python client may yield typed events such as:

- `ThinkingEvent`
- `SearchResultsEvent`
- `MessageEvent`
- `CitationEvent`
- `FinalAnswerEvent`
- `ToolCallEvent`
- `ToolResultEvent`
- `UnknownEvent`

## Consumption pattern

```python
stream = client.retrieval.rag(
    query="What does the corpus say?",
    rag_generation_config={"stream": True},
)

for event in stream:
    print(type(event).__name__)
```

## Citation handling

- Do not assume every stream item is plain text.
- Watch for citation-bearing events and final-answer events separately.
- Preserve the sequence of events if you want to show a trace or debug a response.

## Async pattern

The async client mirrors the same event types and should be consumed with `async for`.
