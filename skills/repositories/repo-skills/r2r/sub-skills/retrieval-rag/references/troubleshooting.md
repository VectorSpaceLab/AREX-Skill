# Retrieval Troubleshooting

## Common issues

- **No results**: verify the search mode and search settings before changing the prompt.
- **Citations missing**: confirm the corpus was ingested and that the search request is actually using RAG or agent flow.
- **Stream parsing errors**: handle typed events one by one instead of assuming a single JSON object or newline-delimited text blob.
- **Model/provider errors**: check the configured model and the server-side provider settings.
- **Too much or too little retrieval context**: tighten or loosen `search_settings` and `task_prompt`.
- **Web search not available**: only enable it when the server and provider setup support it.

## Recovery steps

1. Validate the request with `scripts/retrieval_request_builder.py`.
2. Confirm the document ingestion workflow succeeded.
3. If the issue is server/provider setup, switch to `server-configuration`.
