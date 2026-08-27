# Search, RAG, and Agent Reference

## Search

- `client.retrieval.search(query=..., search_mode=..., search_settings=...)`
- Default search mode is custom; the repository docs and tests also cover basic and advanced search shapes.

```python
client.retrieval.search(
    query="Explain the architecture",
    search_mode="custom",
    search_settings={"limit": 5},
)
```

## RAG

- `client.retrieval.rag(query=..., rag_generation_config=..., search_mode=..., search_settings=..., task_prompt=..., include_title_if_available=..., include_web_search=...)`
- Use `rag_generation_config` to control the model, temperature, and streaming behavior.

```python
client.retrieval.rag(
    query="Summarize the corpus",
    search_mode="advanced",
    rag_generation_config={"stream": False, "temperature": 0.0},
)
```

## Agent and completion

- `client.retrieval.agent(message=..., rag_generation_config=..., research_generation_config=..., search_mode=..., search_settings=..., task_prompt=..., tools=..., rag_tools=..., research_tools=..., mode=...)`
- `client.retrieval.completion(messages=..., generation_config=...)`
- `client.retrieval.embedding(text=...)`

## Practical notes

- `include_title_if_available` can improve answer framing when document titles matter.
- `include_web_search` is a separate retrieval option and should only be used when web lookup is desired.
- Keep retrieval settings in the payload, not in the prompt text.
