# Native Tools, Common Tools, and Embeddings

Pydantic AI has two different tool families that are easy to confuse:

- **Native tools** are executed by the model provider and are passed through `capabilities=[NativeTool(...)]` using classes from `pydantic_ai.native_tools`.
- **Common tools** are Python function tools executed by Pydantic AI, imported from `pydantic_ai.common_tools`, and passed through `tools=[...]` or toolsets.

Use native tools when the provider has first-class support and you want provider-managed behavior. Use common tools or provider-adaptive capabilities when model portability and local fallback matter more.

## Native Tool Inventory

| Native tool | Supported providers in current source/docs | Key notes |
| --- | --- | --- |
| `WebSearchTool` | Anthropic, OpenAI Responses, Google, xAI, Groq compound models, OpenRouter | OpenAI Chat Completions is not enough; use `openai-responses:` for OpenAI native web search. Parameters vary by provider. |
| `XSearchTool` | xAI | Can be used through higher-level `XSearch` capability with a fallback model for non-xAI agents. Validates mutually exclusive handle allow/block lists. |
| `CodeExecutionTool` | Anthropic, OpenAI Responses, Google, Bedrock Nova 2.0, xAI | Provider executes code in its own sandbox; do not assume local Python packages/files are available. |
| `WebFetchTool` | Anthropic, Google | `UrlContextTool` is a deprecated alias for backward-compatible serialized payloads. |
| `ImageGenerationTool` | OpenAI Responses, Google | Controls an image-generation tool inside the model request; it does not change the conversational model. |
| `MemoryTool` | Anthropic | Requires a compatible Anthropic memory tool implementation exposed as a function tool named `memory`; route function-tool implementation details to `tools-and-toolsets`. |
| `MCPServerTool` | OpenAI Responses, Anthropic, xAI | Provider-native remote MCP server access. Route local MCP client/server lifecycle details to `mcp-and-integrations`. |
| `FileSearchTool` | OpenAI Responses, Google, xAI collections search | Requires provider-side uploaded/processed file stores or collections; file upload scripts were excluded from this runtime skill because they need live credentials and mutate provider resources. |

### Minimal Native Tool Pattern

```python
from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[NativeTool(WebSearchTool(search_context_size='high'))],
)
```

For dynamic configuration, wrap a callable in `NativeTool`; it may return an `AbstractNativeTool` instance or `None` based on `RunContext`. Keep provider-specific parameter support in mind. A configuration accepted by one provider may be ignored or rejected by another.

### Provider-Adaptive Capabilities

For model-agnostic apps, prefer higher-level capabilities such as `WebSearch`, `WebFetch`, `ImageGeneration`, or `MCP` where appropriate. These can use native tools when supported and local/common-tool fallbacks otherwise. Integration and lifecycle details belong in `mcp-and-integrations`; function-tool fallback details belong in `tools-and-toolsets`.

## Common Tool Workflows

Common tools require optional extras and execute in the application process:

```python
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

agent = Agent(
    'openai:gpt-5.2',
    tools=[duckduckgo_search_tool()],
    instructions='Search DuckDuckGo and summarize the result.',
)
```

Use these when a provider lacks a native tool, when you need deterministic Python-side validation, or when the tool should be portable across providers. Install and runtime prerequisites:

- `duckduckgo_search_tool()` requires `pydantic-ai-slim[duckduckgo]` and network access at runtime.
- `web_fetch_tool()` requires `pydantic-ai-slim[web-fetch]` and network access at runtime; it includes SSRF protection.
- `tavily_search_tool(...)` requires `pydantic-ai-slim[tavily]` plus `TAVILY_API_KEY` or an explicit client/key.
- Exa tools and `ExaToolset` require `pydantic-ai-slim[exa]` plus `EXA_API_KEY` or an explicit client/key.

## Embeddings

Use `Embedder` for high-level embedding workflows:

```python
from pydantic_ai import Embedder

embedder = Embedder('openai:text-embedding-3-small')

async def embed_docs() -> int:
    result = await embedder.embed_documents(['alpha', 'beta'])
    return len(result.embeddings)
```

Embedding model strings also require a provider prefix. `infer_embedding_model()` raises `ValueError` if the prefix is missing and `UserError` for an unknown embedding provider.

| Prefix | Model class | Typical use |
| --- | --- | --- |
| `openai:` and OpenAI-compatible providers | `OpenAIEmbeddingModel` | Managed embeddings, dimension control for OpenAI `text-embedding-3-*`, OpenAI-compatible endpoints. |
| `google:` / `google-cloud:` | `GoogleEmbeddingModel` | Gemini API or Google Cloud embeddings. |
| `cohere:` | `CohereEmbeddingModel` | Cohere multilingual/domain embeddings. |
| `voyageai:` | `VoyageAIEmbeddingModel` | Voyage domain/code/legal/finance embeddings. |
| `bedrock:` | `BedrockEmbeddingModel` | AWS-hosted Titan/Cohere/Nova embedding models. |
| `sentence-transformers:` | `SentenceTransformerEmbeddingModel` | Local/private embeddings without API keys; dependencies/models can be large. |

`Embedder` methods:

- `embed_query(text_or_texts, settings=...)` for search queries;
- `embed_documents(text_or_texts, settings=...)` for indexed documents;
- `embed(inputs, input_type='query' | 'document', settings=...)` for explicit control;
- `override(model=...)` for temporary testing or migration;
- `instrument_all(...)` or `instrument=` for OpenTelemetry/Logfire integration when configured.

Changing embedding models changes dimensions and similarity distributions. Re-embed and re-index stored documents after changing model family, provider, or dimensions.

## Native Output Cross-Link

Provider-native structured output compatibility is tightly coupled to model profiles and output modes. Use `outputs-and-messages` for `NativeOutput`, `ToolOutput`, `PromptedOutput`, message parts, and structured-output retry behavior; use this sub-skill only to select/configure the provider and profile that make native output possible.
