# Configuration Workflows

## Purpose

Use this reference to map RAG Config page controls to the underlying builder and
cache behavior.

## Config Page Preconditions

The RAG Config page is useful only after an agent has been created or selected.
When no `agent_builder` is available, the page displays a message instructing
the user to create an agent first. When the selected cache has no constructed
agent, the update/delete buttons are hidden.

## Editable Fields

| UI field | Cache/API target | Notes |
| --- | --- | --- |
| Agent ID | `cache.agent_id` and registry key | Renaming through update deletes the old cache entry and saves the new one. |
| System Prompt | `cache.system_prompt` | Required before creating an agent. Keep it task-focused and data-source agnostic. |
| Include Summarization | `RAGParams.include_summarization` | Adds a summary query tool; best with GPT-4-class models. |
| Additional tools | `cache.tools` | Comma-separated; current source recognizes only `web_search`. |
| Top K | `RAGParams.top_k` | Retrieval count for vector search. |
| Chunk Size | `RAGParams.chunk_size` | Chunk size for index construction. |
| Embed Model | `RAGParams.embed_model` | `default` or a LlamaIndex-resolvable identifier such as `local:<model-id>`. |
| LLM | `RAGParams.llm` | Unprefixed OpenAI model, or `openai:`, `anthropic:`, `replicate:`, `local:`. |

Loaded files, directory, and URLs are displayed as non-editable fields. To
change the data source, build a new agent instead of treating it as a simple
configuration edit.

## Update Workflow

`update_agent` performs these steps:

1. Delete the old cache entry using the current `cache.agent_id`.
2. Set `cache.agent_id` to the submitted ID.
3. Replace the system prompt when provided.
4. Build a partial RAG parameter dict from fields that are not `None`.
5. Call `set_rag_params` to merge and validate RAG parameters.
6. Replace `cache.tools` when `additional_tools` is provided.
7. Call `create_agent`, which reconstructs and saves the agent.
8. Update the sidebar selection to the new agent ID.

Because this path deletes the old cache before rebuilding, advise users to
avoid risky config edits when credentials, data paths, or model dependencies are
not ready.

## Delete Workflow

The delete button removes the selected cache directory and updates
`agent_ids.json`, then clears the selected agent. Use it when the user wants to
remove a generated agent or recover from stale state they no longer need.

## Loaded Data Display

The config page shows non-editable summaries of `file_names`, `directory`, and
`urls` from the selected cache. If these are wrong, the correct workflow is to
create a new bot from the builder route because the vector index was built from
the original documents.

## Additional Tools

The additional tools text box stores comma-separated tool names. Current source
only maps `web_search` to a tool object. Empty text becomes an empty list. Any
unknown tool name will fail later when tool objects are resolved.
