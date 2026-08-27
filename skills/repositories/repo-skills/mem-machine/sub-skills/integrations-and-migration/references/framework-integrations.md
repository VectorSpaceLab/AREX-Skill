# Framework Integrations

MemMachine integrations all share the same core requirements: a MemMachine
server or cloud endpoint, project context (`org_id`, `project_id`), memory
context (`user_id`, `agent_id`, optional `group_id`/`session_id`), and auth when
needed.

## Integration Matrix

| Surface | Best path | Notes |
| --- | --- | --- |
| Plain Python agent | Python SDK | Use `MemMachineClient`, project memory context, and add/search calls. |
| LangGraph | `memmachine_client.langgraph.MemMachineTools` or helper factories | Good when graph nodes/tools should add or search memory. |
| LangChain | LangChain memory wrapper or custom tool around Python SDK | Requires LangChain dependency; validate memory key/context mapping. |
| LlamaIndex | LlamaIndex memory adapter or SDK-backed retriever/tool | Requires LlamaIndex dependency and explicit project/user context. |
| CrewAI | Tool wrapper around MemMachine add/search | Requires CrewAI runtime and tool registration. |
| AWS Strands | Strands tool integration | Requires Strands SDK and AWS/runtime setup separate from MemMachine. |
| MCP clients | MemMachine MCP stdio/HTTP | Good for Claude Desktop/Cursor/tool clients; configure context and auth. |
| Dify/n8n/FastGPT/OpenClaw | Platform plugin or REST integration | Usually manifest/platform-specific; use REST endpoint and API key carefully. |
| Node/TypeScript apps | `@memmachine/client` | Use the TypeScript sub-skill for class/method details. |

## LangGraph Pattern

```python
from memmachine_client.langgraph import MemMachineTools, create_add_memory_tool, create_search_memory_tool

tools = MemMachineTools(base_url="http://localhost:8080", api_key=None)
add_memory = create_add_memory_tool(tools)
search_memory = create_search_memory_tool(tools)
```

Before wiring into a graph, verify:

- framework dependency is installed;
- base URL and API key are loaded securely;
- graph state carries stable user/project/session context;
- tool outputs are converted into the graph's expected message/state format.

## MCP Pattern

Use MCP when the host client expects tools rather than an SDK import:

```bash
memmachine-mcp-stdio
memmachine-mcp-http --host localhost --port 8080
```

Configure the MCP client with project/user context and auth outside command
logs. Use stdio for local launcher workflows and HTTP for shared/networked
clients.

## Example-agent Adaptation

When adapting a chatbot or provider-backed example:

1. Replace hard-coded demo IDs with user/project/session variables.
2. Add a health check before memory operations.
3. Add memory only for stable facts or conversation turns that the user wants
   persisted.
4. Search memories with a narrow query before calling the LLM.
5. Keep provider API keys and MemMachine API keys separate.
6. Add a dry-run mode for tests that prints intended memory operations.

## Platform Integrations

No-code or plugin platforms typically need:

- endpoint/base URL;
- API key or bearer token;
- org/project context;
- tool/action definitions for add/search/list/delete;
- privacy policy and secret storage settings;
- test request with non-sensitive content.

Do not assume platform plugins are installed with `memmachine-client`; they are
separate integration assets or packages.

## Validation Checklist

- Can the host app import its framework integration dependency?
- Can it reach MemMachine health endpoint?
- Does a non-sensitive add/search round trip work in a test project?
- Does metadata isolate users/sessions correctly?
- Are writes/deletes explicitly approved?
- Are provider and MemMachine secrets masked in logs?
