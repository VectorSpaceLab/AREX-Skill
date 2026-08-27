# Builder API Reference

## Verified Runtime Context

The inspection environment imported the builder modules with Streamlit dummy
secrets and no external API calls. RAGs is an app-style repository: the source
modules are `core` and `st_utils`; a package named `rags` is not importable from
the current pyproject.

## `RAGParams`

`RAGParams` is the Pydantic model used by both the builder and generated agent.

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `include_summarization` | `bool` | `False` | When true, `construct_agent` also builds a summary query tool. |
| `top_k` | `int` | `2` | Passed as `similarity_top_k` to the vector query engine. |
| `chunk_size` | `int` | `1024` | Used when creating the LlamaIndex `ServiceContext`. |
| `embed_model` | `str` | `default` | Resolved through LlamaIndex `resolve_embed_model`. |
| `llm` | `str` | `gpt-4-1106-preview` | Resolved by RAGs `_resolve_llm`. |

## `RAGAgentBuilder`

Important verified signatures:

```python
RAGAgentBuilder(cache=None, agent_registry=None)
RAGAgentBuilder.create_system_prompt(self, task: str) -> str
RAGAgentBuilder.load_data(self, file_names=None, directory=None, urls=None) -> str
RAGAgentBuilder.add_web_tool(self) -> str
RAGAgentBuilder.get_rag_params(self) -> dict
RAGAgentBuilder.set_rag_params(self, **rag_params: dict) -> str
RAGAgentBuilder.create_agent(self, agent_id=None) -> str
RAGAgentBuilder.update_agent(self, agent_id: str, system_prompt=None,
    include_summarization=None, top_k=None, chunk_size=None, embed_model=None,
    llm=None, additional_tools=None) -> None
```

Behavior to preserve in guidance:

- `create_system_prompt` calls the builder LLM and stores the generated system
  prompt in the cache.
- `load_data` delegates to `core.utils.load_data` and records `docs`,
  `file_names`, `urls`, and `directory` in the cache.
- `add_web_tool` appends `web_search` only once.
- `set_rag_params` merges provided fields into the existing parameter dict,
  then reconstructs `RAGParams` for validation.
- `create_agent` requires `cache.system_prompt` to be set, constructs tools and
  a vector index, assigns or preserves an agent ID, stores the agent and vector
  index in cache, and saves through `AgentCacheRegistry`.

## Data Loading

Verified signature:

```python
load_data(file_names=None, directory=None, urls=None) -> list[Document]
```

Rules:

- Empty input raises `ValueError("Must specify either file_names or urls or directory.")`.
- More than one source kind raises `ValueError("Must specify only one of file_names or urls or directory.")`.
- `file_names` uses `SimpleDirectoryReader(input_files=...)`.
- `directory` uses `SimpleDirectoryReader(input_dir=...)`.
- `urls` uses `llama_hub.web.simple_web.base.SimpleWebPageReader` and therefore
  needs network access.

## Model Resolution

`_resolve_llm` handles these model string patterns:

- No prefix: treat the value as an OpenAI model name and read `openai_key`.
- `openai:<model>`: use OpenAI with the text after the prefix.
- `anthropic:<model>`: read `anthropic_key` and create an Anthropic LLM.
- `replicate:<model>`: read `replicate_key` and create a Replicate LLM.
- `local:<model>`: delegate to LlamaIndex `resolve_llm`.

Unsupported prefixes raise `ValueError("LLM <value> not recognized.")`.

## Agent Construction

`construct_agent(system_prompt, rag_params, docs, vector_index=None,
additional_tools=None)` resolves the embedding model and LLM, builds a
`VectorStoreIndex` when needed, creates a `vector_tool`, optionally creates a
`summary_tool`, appends additional tools, and calls `load_agent`.

`load_agent` uses an OpenAI function-calling agent when the LLM is an OpenAI
function-calling model. Otherwise it falls back to `CondensePlusContextChatEngine`
and requires the vector index in `extra_kwargs`.

## Multimodal Builder

`MultimodalRAGAgentBuilder` mirrors the default builder but its `load_data`
accepts files or a directory only. Its `create_agent` calls `construct_mm_agent`
and sets `cache.builder_type = "multimodal"` before saving. The class imported
in the minimum inspection environment, but actual multimodal construction was
not executed because optional dependencies and external model calls are outside
the safe default verification scope.
