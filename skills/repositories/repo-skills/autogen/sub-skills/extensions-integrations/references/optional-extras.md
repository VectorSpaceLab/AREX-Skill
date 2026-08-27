# Optional Extras and Dependency Selection

`autogen-ext==0.7.5` imports with only `autogen-core==0.7.5`. Most integrations are optional and fail at import or construction time until their exact extra and external service are available. Prefer narrow extras so maintenance environments remain debuggable.

## Install Pattern

```bash
pip install "autogen-ext[openai]"
pip install "autogen-ext[mcp]"
pip install "autogen-ext[docker]"
```

Use multiple narrow extras when one workflow needs multiple surfaces:

```bash
pip install "autogen-ext[openai,mcp,docker]"
```

Avoid installing Studio or Magentic-One CLI packages into the same 0.7.x environment without checking version constraints; those tool surfaces are handled by `tools-studio-bench`.

## Extras Matrix

| Extra | Adds | Main public surface | External requirement |
| --- | --- | --- | --- |
| `openai` | `openai`, `tiktoken`, `aiofiles` | `OpenAIChatCompletionClient`, `AzureOpenAIChatCompletionClient`, OpenAI assistant/agent surfaces | API key or Azure endpoint/token; no provider calls during import checks |
| `anthropic` | `anthropic` | `AnthropicChatCompletionClient`, `AnthropicBedrockChatCompletionClient` | Anthropic key or AWS Bedrock credentials |
| `azure` | Azure AI, identity, search packages | `AzureAIChatCompletionClient`, `AzureAIAgent`, `AzureAISearchTool`, `ACADynamicSessionsCodeExecutor` | Azure endpoint, deployment/model, credential, roles, service availability |
| `ollama` | `ollama`, `tiktoken` | `OllamaChatCompletionClient` | Running Ollama service and pulled model |
| `llama-cpp` | `llama-cpp-python` | `LlamaCppChatCompletionClient` | Local model file and compatible native build |
| `gemini` | `google-genai` | Gemini support through OpenAI-compatible handling and related clients | Google credentials/API key depending on chosen path |
| `semantic-kernel-core` | `semantic-kernel` | `SKChatCompletionAdapter`, `KernelFunctionFromTool` | A configured Semantic Kernel connector |
| `semantic-kernel-google` / `hugging-face` / `mistralai` / `ollama` / `onnx` / `anthropic` / `pandas` / `aws` / `dapr` | Provider-specific Semantic Kernel extras | `SKChatCompletionAdapter` with provider connector | Provider-specific credentials and packages |
| `semantic-kernel-all` | Many Semantic Kernel connectors | Same | Heavy; use only when multiple SK connectors are intentionally required |
| `mcp` | `mcp` | `StdioServerParams`, `SseServerParams`, `StreamableHttpServerParams`, `McpWorkbench`, MCP adapters/host | Trusted MCP server command or URL; may start a process if used |
| `http-tool` | `httpx`, `json-schema-to-pydantic` | `HttpTool` | Network endpoint only when invoked |
| `langchain` | `langchain_core` | `LangChainToolAdapter` | Compatible LangChain tool object |
| `graphrag` | `graphrag` | `GlobalSearchTool`, `LocalSearchTool` | Prepared GraphRAG artifacts/config |
| `docker` | `docker`, `asyncio_atexit` | `DockerCommandLineCodeExecutor` | Installed and running Docker daemon |
| `jupyter-executor` | `ipykernel`, `nbclient` | `JupyterCodeExecutor` | Local kernel availability; starts kernels when executed |
| `docker-jupyter-executor` | Docker plus `websockets`, `requests`, `aiohttp` | `DockerJupyterServer`, `DockerJupyterCodeExecutor` | Docker daemon, image/build, exposed gateway port |
| `diskcache` | `diskcache` | `DiskCacheStore`, `ChatCompletionCache` | Writable cache directory |
| `redis` | `redis` | `RedisStore` | Redis service and connection parameters |
| `redisvl` | `redisvl` | Redis vector-related integration support | Redis/RedisVL service compatibility |
| `chromadb` | `chromadb` | `ChromaDBVectorMemory` | Local persistent path or Chroma HTTP server; optional embedding provider |
| `task-centric-memory` | `chromadb` | `MemoryController` experimental surface | ChromaDB plus model client |
| `mem0` | `mem0ai` | `Mem0Memory` cloud mode | Mem0 API key or environment |
| `mem0-local` | `mem0ai`, `neo4j`, `chromadb` | `Mem0Memory` local mode | Local config plus Neo4j/ChromaDB as configured |
| `canvas` | `unidiff` | `TextCanvas`, `TextCanvasMemory` | None beyond file/content access |
| `grpc` | `grpcio` | `GrpcWorkerAgentRuntime`, `GrpcWorkerAgentRuntimeHost` | gRPC/protobuf-compatible worker/host topology |
| `web-surfer` | AgentChat, Playwright, Pillow, Magika, MarkItDown | `MultimodalWebSurfer` | Browser binaries and trusted browsing policy |
| `file-surfer` | AgentChat, Magika, MarkItDown | `FileSurfer` | Local file access policy |
| `video-surfer` | AgentChat, OpenCV, ffmpeg, Whisper | `VideoSurfer` | Media codecs/models and local file policy |
| `magentic-one` | AgentChat, Playwright, Pillow, Magika, MarkItDown | `MagenticOneCoderAgent`, `MagenticOneGroupChat` helper surfaces | Browser/code execution dependencies; route CLI package questions to `tools-studio-bench` |
| `rich` | `rich` | `RichConsole` UI helper | Terminal output only |

## Selection Rules

- Match the import path first, then install the extra that owns that path.
- Do not install `semantic-kernel-all` just to use one connector; install the provider-specific Semantic Kernel extra.
- Do not install both CLI/tooling packages and 0.7.x libraries into one environment unless their dependency ranges are proven compatible.
- For model-client failures, separate package importability from provider authentication. A successful import does not prove API access.
- For service-backed extras (`docker`, `redis`, `chromadb`, `mem0-local`, `jupyter-executor`, `docker-jupyter-executor`, `mcp`), perform import/spec checks first and start services only under an explicit verification plan.

## Safe Inspection

Run the bundled script for import/spec status only:

```bash
python scripts/inspect_extensions.py --json
```

The script intentionally does not instantiate provider clients with real credentials, ping Docker, open Jupyter kernels, start MCP servers, connect to Redis/ChromaDB/mem0, launch Playwright, or call network APIs.
