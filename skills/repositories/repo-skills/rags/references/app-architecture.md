# RAGs App Architecture

## Purpose

Read this when a task spans multiple RAGs pages or when you need to understand
how builder state, generated agents, data sources, tools, and cache files relate.

## High-Level Components

- **Streamlit shell:** three page flows: Home/build, RAG Config, and Generated
  RAG Agent chat.
- **Shared state helpers:** session state keeps the selected agent ID, cache,
  builder agent, builder object, registry, and multimodal toggle.
- **Builder agent:** a tool-using LLM agent that calls builder methods in a
  rough order: create system prompt, load data, add optional tools, set RAG
  parameters, create the generated agent.
- **Generated RAG agent:** a LlamaIndex chat engine or agent with a vector query
  tool and optional summary tool.
- **Cache registry:** persisted agent IDs, per-agent cache metadata, and
  persisted vector-index storage.

## Data and Control Flow

1. User chooses a new or existing agent in the sidebar.
2. The Home page initializes a builder for new agents or selected cache state.
3. The builder receives natural-language task instructions and uses tools to
   construct a RAG agent.
4. Source data is loaded from exactly one of local files, one directory, or URLs.
5. RAG parameters determine chunking, retrieval count, embedding model, LLM, and
   whether a summary tool is added.
6. Generated agent and vector index are stored in cache.
7. The config page can update or delete the selected cache.
8. The chat page calls the selected generated agent and renders text/image
   sources when source nodes exist.

## Secrets and Providers

`openai_key` is required early because the builder LLM is configured from
Streamlit secrets. Other provider keys are used only by selected routes:

- `anthropic_key` for `anthropic:<model>` LLM strings.
- `replicate_key` for `replicate:<model>` LLM strings.
- `metaphor_key` for the optional `web_search` tool.

Local model strings are delegated to LlamaIndex resolution and may need separate
local model dependencies or downloads.

## Model and Tool Resolution

- Unprefixed LLM strings are OpenAI model names.
- `openai:<model>`, `anthropic:<model>`, `replicate:<model>`, and
  `local:<model>` are recognized model formats.
- The only named additional tool supported by current source is `web_search`.
- `include_summarization=True` adds a `summary_tool`; otherwise the agent uses
  vector retrieval only.

## Cache Shape

The cache registry stores an ID list and one directory per generated agent. Each
cache contains JSON metadata plus vector-index storage. The saved JSON records
source paths/URLs, tools, RAG parameters, builder type, system prompt, and agent
ID. On load, RAGs reloads source documents, restores vector-index storage, and
reconstructs the generated agent.

## Optional Multimodal Branch

The beta multimodal toggle constructs a multimodal builder and sets
`builder_type="multimodal"`. It supports files or directories, not URL loading.
Actual multimodal operation depends on optional model/image dependencies and
OpenAI multimodal credentials. Treat it as opt-in and validate with a tiny
fixture before using it on important data.

## App-Style Packaging Note

The repository metadata names a distribution `rags`, but the current snapshot
does not contain an import package with that name. A root package install fails;
use dependency installation and run or inspect from a checkout. The root
troubleshooting reference records this as an operating constraint.
