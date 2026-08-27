---
name: chat
description: "Use this RAGs sub-skill to query generated RAG agents, inspect
  text and image sources, and troubleshoot Generated RAG Agent chat behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RAGs Chat

Use this sub-skill after a RAGs bot has been created and the task is to ask
questions, debug generated-agent responses, inspect cited sources, or reason
about text and image source display.

## Read This When

- The user mentions the Generated RAG Agent page, chat UI, `agent.chat`, source
  nodes, image sources, or missing citations.
- The app says the agent is not created even though the user expected one.
- The generated answer is wrong, has no sources, has broken image paths, or
  appears to ignore summarization/retrieval settings.
- The task involves `get_image_and_text_nodes`, `MultimodalChatEngine`, or the
  response `source_nodes` contract.

For setup, data loading, or model selection before an agent exists, read
[`../builder/SKILL.md`](../builder/SKILL.md). For changing an existing agent's
configuration or cache, read [`../configuration/SKILL.md`](../configuration/SKILL.md).

## Core Workflow

1. Confirm `current_state.cache.agent` exists. If not, route the user back to
   the builder flow.
2. Ask the question through the generated agent chat route. The app appends the
   user message, calls `agent.chat(str(prompt))`, displays the response, and
   stores the response object in message metadata.
3. Inspect sources using the response's `source_nodes` when available. Text
   sources are displayed as IDs and full metadata content; image sources are
   displayed from `metadata["file_path"]`.
4. If source evidence is absent or weak, debug retrieval/data/index settings
   before treating it as a UI problem.
5. For model/provider errors, route back to builder/configuration because the
   chat page uses the agent created from those settings.

Read [`references/chat-workflow.md`](references/chat-workflow.md) for detailed
query and source-display flow. Read
[`references/api-reference.md`](references/api-reference.md) for response and
helper behavior. Read [`references/troubleshooting.md`](references/troubleshooting.md)
for known failure symptoms.

## Important Operating Facts

- The chat page initializes `agent_messages` with `"Ask me a question!"`.
- It only enables chat when the selected cache has a live generated agent.
- `display_sources` splits `response.source_nodes` into image and text nodes.
- Image nodes need a local `file_path` metadata value; text nodes use
  `MetadataMode.ALL` to include metadata in displayed content.
- Default agent construction creates a vector search tool and may add a
  summarization tool when `include_summarization=True`.
- External model calls and URL/web-search behavior require credentials and
  network access; the safe skill verification did not execute them.

## Boundaries

Do not promise that a source list exists for every response. Some chat engines
or error paths may not provide `source_nodes`, and poor retrieval settings can
produce empty or irrelevant sources. Debug the data/index/config route before
rewriting chat UI behavior.
