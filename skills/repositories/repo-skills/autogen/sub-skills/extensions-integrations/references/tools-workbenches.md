# Tools and Workbenches

`autogen_ext.tools.*` provides adapters for external tools and tool ecosystems. These surfaces make other systems callable from AutoGen; they do not replace AgentChat team orchestration. Route agent/team composition to `agentchat-workflows`.

## Tool Surface Map

| Surface | Extra | Public imports | Use when |
| --- | --- | --- | --- |
| MCP stdio/SSE/streamable HTTP tools | `mcp` | `StdioServerParams`, `SseServerParams`, `StreamableHttpServerParams`, `McpWorkbench`, `mcp_server_tools`, `StdioMcpToolAdapter`, `SseMcpToolAdapter`, `StreamableHttpMcpToolAdapter` | You need tools, prompts, resources, or host capabilities exposed by an MCP server |
| MCP host support | `mcp` | `McpSessionHost`, `ChatCompletionClientSampler`, `StdioElicitor`, `StaticRootsProvider` | An MCP server requests sampling, elicitation, or roots from the client host |
| HTTP API tool | `http-tool` | `HttpTool` | You need to expose a typed HTTP operation as an AutoGen tool |
| LangChain adapter | `langchain` | `LangChainToolAdapter` | You have an existing LangChain tool object |
| Azure AI Search | `azure` | `AzureAISearchTool`, `SearchQuery`, `VectorizableTextQuery`, `AzureAISearchConfig` | You need Azure AI Search as a tool or grounding source |
| GraphRAG search | `graphrag` | `GlobalSearchTool`, `LocalSearchTool`, GraphRAG config classes | You have prepared GraphRAG data/config and want search tools |
| Semantic Kernel function adapter | `semantic-kernel-core` | `KernelFunctionFromTool`, `KernelFunctionFromToolSchema` | You need an AutoGen tool exposed into Semantic Kernel |
| Code execution as a tool | executor extra depends on backend | `PythonCodeExecutionTool` | You want a code executor wrapped as a tool; inspect executor safety separately |

## MCP Workbench

MCP support has three transport parameter classes:

```python
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

server_params = StdioServerParams(
    command="python",
    args=["server.py"],
)
workbench = McpWorkbench(server_params=server_params)
```

Use this as a shape example only; starting the workbench may start a server process. For diagnosis without execution, check:

- `autogen-ext[mcp]` is installed and `autogen_ext.tools.mcp` imports.
- The chosen server params match the transport: stdio command/args/env, SSE URL, or streamable HTTP URL/headers.
- The stdio `command` is trusted and resolves on PATH, and `args` do not execute unreviewed scripts.
- Filesystem roots and environment variables passed to the server are intentionally scoped.
- `McpWorkbench` starts before `list_tools()`, `call_tool()`, `list_prompts()`, or resource methods; tests show a missing actor after start raises `RuntimeError("Actor is not initialized. Please check the server connection.")`.

### MCP Adapters vs Workbench

- Use `mcp_server_tools(...)` or MCP tool adapters when you only need selected MCP tools as AutoGen tools.
- Use `McpWorkbench` when the agent needs MCP tools plus prompts/resources or a workbench lifecycle.
- Use `McpSessionHost` when the MCP server asks the client host to sample from a model, elicit user input, or list allowed roots.

## HTTP Tool

`HttpTool` needs `autogen-ext[http-tool]`. It converts an HTTP operation and schema into an AutoGen tool. Diagnostics should check schema generation, request method/URL construction, authentication header handling, and whether network access is allowed. Do not invoke the HTTP endpoint during static import checks.

## LangChain Tool Adapter

`LangChainToolAdapter` needs `autogen-ext[langchain]` and a compatible LangChain tool object. If imports fail, distinguish missing `langchain_core` from mismatched LangChain tool APIs. If execution fails, inspect the wrapped tool independently before blaming AutoGen.

## Azure AI Search Tool

Azure AI Search surfaces come from the `azure` extra. Validate:

- Search endpoint, index name, credential type, and role/key permissions.
- Whether vectorizable text queries require embedding/model configuration.
- Network access and private endpoint constraints.

The same `azure` extra also enables other Azure surfaces; do not assume an Azure AI Search install means Azure OpenAI, Azure AI Foundry, or Azure Container Apps Dynamic Sessions are configured.

## GraphRAG Tools

`GlobalSearchTool` and `LocalSearchTool` need prepared GraphRAG artifacts and config. Importability only proves the Python package is present. Diagnose missing data paths, incompatible GraphRAG versions, and model/embedding provider setup separately.

## Semantic Kernel Tool Adapter

`KernelFunctionFromTool` exposes an AutoGen tool as a Semantic Kernel function. Keep Semantic Kernel model-client adapter questions in `references/model-clients.md`. Watch for schema mismatches between AutoGen tool schemas and the SK connector's supported function/tool-calling format.

## Code Execution Tool

`PythonCodeExecutionTool` wraps an AutoGen code executor as a tool. Before using it in an agent, inspect the executor backend in `references/code-executors-and-runtimes.md`:

- Local executor: trusted-code only.
- Docker executor: daemon, image, work directory, cleanup, timeout.
- Jupyter executor: kernel availability and output-file policy.
- Azure executor: endpoint, credential, session pool, upload/workdir behavior.

Do not expose code execution to an LLM agent without a containment and approval policy.
