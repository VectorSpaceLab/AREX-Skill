# RAG Workflows

## Local knowledge-base chat

Use this when documents have been indexed into a named KB under `KB_ROOT_PATH`.

1. Initialize and configure Chatchat.
2. Upload/copy docs into a KB and run vectorization (`upload_docs` with `to_vector_store=True` or `chatchat kb -r`).
3. Call `/knowledge_base/local_kb/{kb_name}/chat/completions` or `/chat/chat/completions` with `tool_choice="search_local_knowledgebase"`.
4. Tune `top_k`, `score_threshold`, and `prompt_name` based on retrieval quality.

Use `return_direct=True` to inspect retrieved context before debugging LLM generation.

## Temporary file chat

Use this when a user uploads files for a transient conversation rather than a named persistent KB.

1. POST files to `/knowledge_base/upload_temp_docs`.
2. Capture `knowledge_id` from the response.
3. Call `/knowledge_base/temp_kb/{knowledge_id}/chat/completions` or SDK file/temp methods.
4. Clean up temp data according to the user's data policy.

Temp KB workflows still require an embedding model for indexing uploaded docs.

## Search-engine chat

Use `/knowledge_base/search_engine/{engine_name}/chat/completions` for search-backed RAG. Configured engine names include options such as `bing`, `duckduckgo`, `metaphor`, and `searx` in settings evidence. Search engines may require network access, credentials, or a local Searx service.

## Unified chat and tools

`/chat/chat/completions` routes by payload shape:

- No `tools` or `tool_choice`: pure LLM chat through the configured provider.
- `tools`: agent-style tool selection; streaming should be enabled for step events.
- `tool_choice` without `extra_body.tool_input`: model parses tool arguments for the selected tool.
- `tool_choice` with `extra_body.tool_input`: manual tool invocation and response composition.

Fetch `/tools` before constructing tool requests. The tool list returns names, titles, descriptions, argument schemas, and config.

## Retrieval-first debugging pattern

When RAG answers are bad:

1. Check that documents are present: `list_knowledge_bases`, `list_files`.
2. Search docs directly: `/knowledge_base/search_docs` with the same query/top_k/threshold.
3. Use `return_direct=True` on the RAG chat route to see retrieved docs without LLM synthesis.
4. Adjust chunk size, overlap, text splitter, embedding model, or score threshold.
5. Only then debug prompt/model generation.

## Streaming expectations

- Agent/tool workflows stream multiple steps; chunks can include status-like progress, tool call info, and final text.
- OpenAI-compatible chat streams `ChatCompletionChunk`-like objects.
- Some SDK methods return generators that parse SSE/JSON chunks.
- If a consumer expects one JSON object, set `stream=False` where supported or collect stream chunks explicitly.

## Safety and data mutation

- Upload, delete, update, prune, and vector rebuild routes mutate KB state.
- `return_direct=True` and `search_docs` are safer for diagnosis because they avoid LLM generation but still read indexed data.
- Do not call external search engines or model providers when the user asked for offline/static inspection only.
