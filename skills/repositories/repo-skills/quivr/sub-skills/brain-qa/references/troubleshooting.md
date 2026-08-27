# Brain QA Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Brain.ask(...)` fails inside async code or complains about the event loop | `Brain.ask` is a synchronous wrapper | Use `Brain.aask(...)` or `Brain.ask_streaming(...)` instead |
| `Brain.aask(...)` or `Brain.ask_streaming(...)` says `run_id` is missing | The current API requires a trace identifier | Pass `run_id=uuid4()` |
| Answers appear, but sources or citations are empty | The retrieved chunks do not carry readable source labels or the store is empty | Check the vector store, confirm `original_file_name`, and inspect `Brain.asearch(...)` first |
| The model behaves like plain text instead of using tools | The model-name heuristic does not think the model supports function calling | Use a tool-calling model, or intentionally keep the model name in the non-tool-calling branch for fake-model smoke tests |
| Web search is not available | `TAVILY_API_KEY` is missing or the workflow does not list the tool | Set the key and add `web search` to `WorkflowConfig.available_tools` |
| Chat history looks reversed or malformed | Messages were not appended as human/AI pairs | Rebuild the history with alternating message types |
| Retrieval returns irrelevant chunks | The vector store or embeddings do not match the query well | Re-check the embedder, chunking, and `Brain.asearch(...)` query |
| Provider warnings mention a missing API key | The selected provider key is absent | Set the provider-specific key or switch to a fake/local model for smoke tests |
| The docs or an old example omit `run_id` | Example drift | Treat the old snippet as stale and update it to the current signature |

## Fast diagnosis sequence

1. Confirm whether the task is retrieval-only, normal QA, or streaming.
2. Check `run_id` first.
3. Check the model-name heuristic next.
4. Then check the vector store, source metadata, and optional web-search key.
