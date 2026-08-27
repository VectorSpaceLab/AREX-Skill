# Chat Workflow

## Purpose

Use this reference to operate or troubleshoot the Generated RAG Agent page after
a RAGs agent has been built.

## Preconditions

- A generated agent exists in the selected cache.
- The model provider credentials required by the selected `llm` and embedding
  model are available.
- The original data source paths are still valid if a cached agent must be
  reconstructed.
- Network access exists for remote model providers, URL-loaded data, or
  web-search tools.

## Query Flow

1. The page gets current state and renders the shared sidebar.
2. If `agent_messages` is absent, it initializes the conversation with an
   assistant greeting.
3. If `current_state.cache.agent` is present, the page displays prior messages.
4. When the user submits a prompt, the prompt is appended as a user message.
5. If the last message is not from the assistant, the page calls
   `agent.chat(str(prompt))`.
6. The response text is displayed, sources are rendered when possible, and the
   response object is stored in message metadata.

If step 3 fails because there is no agent, the correct recovery path is to build
or reselect an agent, not to patch chat history.

## Source Display

The page calls `display_sources(response)`. That helper expects
`response.source_nodes` and then uses `get_image_and_text_nodes` to split nodes:

- Image nodes are rendered with `st.image(image_node.metadata["file_path"])`.
- Text nodes are collected into a table with `ID` and `Text` fields.
- Text content uses `MetadataMode.ALL`, so metadata can appear alongside text.

For non-multimodal agents, most source nodes should be text. For multimodal
agents, image source nodes must contain a valid local `file_path` metadata value
or rendering will fail even if retrieval found an image.

## Retrieval and Tool Behavior

Default construction creates a vector query engine using `top_k`. If
summarization is enabled, construction also creates a `summary_tool`; the
function-calling agent decides which tool to invoke. A wrong answer can come
from retrieval miss, chunk size, too-small `top_k`, stale cache data, missing
summarization, or model/provider behavior.

## Safe Debugging Order

1. Confirm the selected agent ID and cache load correctly.
2. Review the configured data source, `top_k`, `chunk_size`, embed model, LLM,
   and summarization setting.
3. Ask a narrow question whose answer should appear in a known source chunk.
4. Inspect whether `source_nodes` are empty, irrelevant, or missing metadata.
5. If sources are wrong, adjust retrieval/data/chunk settings through the
   configuration or rebuild route.
6. If sources are right but answer quality is weak, inspect LLM choice,
   summarization, and system prompt.

## Multimodal Notes

`MultimodalChatEngine` wraps a `SimpleMultiModalQueryEngine` and returns an
`AgentChatResponse` with `source_nodes`. The beta branch is useful for image and
text retrieval, but it was not fully exercised in the minimum verification
environment. Treat image-source tasks as requiring optional dependency and
credential checks before live use.
