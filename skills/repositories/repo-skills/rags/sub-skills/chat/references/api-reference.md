# Chat API Reference

## Page-Level Helpers

### `display_sources(response)`

Expected behavior:

1. Reads `response.source_nodes`.
2. Splits nodes with `get_image_and_text_nodes`.
3. Opens a "Sources" expander when either image or text sources exist.
4. Renders image sources from each image node's `metadata["file_path"]`.
5. Renders text sources as a table with node ID and content including metadata.

Assumptions to validate during debugging:

- The response object has a `source_nodes` attribute.
- Image node metadata contains a readable `file_path`.
- Text nodes have a `node` object with `get_content(metadata_mode=...)`.

### `add_to_message_history(role, content, extra=None)`

Stores chat messages in Streamlit session state as dictionaries with `role`,
`content`, and optional `extra`. The response object is stored under
`extra["response"]` so sources can be displayed again when history is rerendered.

### `display_messages()`

Renders prior chat messages. It supports `msg_type="text"` and `msg_type="info"`.
Unknown message types raise `ValueError`.

## Source Split Helper

`get_image_and_text_nodes(nodes)` returns `(image_nodes, text_nodes)`. It treats
nodes whose `.node` is an `ImageNode` as image sources and all others as text.
This means a node with image-like metadata but not an `ImageNode` class will be
shown in the text table rather than with `st.image`.

## Generated Agent Construction

The chat page uses the agent produced by builder/configuration. Default
construction:

- Resolves embedding and LLM settings from `RAGParams`.
- Builds or reuses a `VectorStoreIndex`.
- Creates a vector query-engine tool named `vector_tool`.
- Optionally creates a `summary_tool` when `include_summarization=True`.
- Uses an OpenAI function-calling agent when the LLM is an OpenAI
  function-calling model, otherwise uses `CondensePlusContextChatEngine`.

## Multimodal Chat Engine

`MultimodalChatEngine` wraps a `SimpleMultiModalQueryEngine` and implements
`chat`, `stream_chat`, `achat`, and `astream_chat`. The synchronous `chat`
method queries the underlying multimodal engine and returns an
`AgentChatResponse` containing text and source nodes. The class does not retain
chat history internally; it reports an empty `chat_history` property.

## Response Debugging Checklist

- Does `current_state.cache.agent` exist?
- Does `agent.chat` return a response or raise a provider/credential error?
- Does the response have `source_nodes`?
- Are source nodes text or image nodes as expected?
- Do image nodes contain valid file paths?
- Are retrieved text chunks related to the user's question?
- Do retrieval settings match the expected context size and recall needs?
