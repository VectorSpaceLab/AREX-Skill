# Cross-Cutting Troubleshooting

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` followed by `LangroidImportError` naming an extra | Optional workflow dependency is not installed | Install the narrow extra named by the error, then re-run `python scripts/check_langroid_environment.py --json --optional`. |
| Installing `langroid[sql]` tries to build `psycopg2` and fails with `pg_config executable not found` | Source `psycopg2` build lacks PostgreSQL headers/tools | Install PostgreSQL client development tools, use a Conda package, or use `psycopg2-binary` for local inspection when acceptable. |
| Provider call fails with authentication error | Missing/incorrect API key or provider-specific environment variable | Use `sub-skills/llm-provider-config/`; validate config without printing secrets before making a live call. |
| Local/Ollama/OpenAI-compatible model fails | Wrong `api_base`, model string, or server is not running | Probe the server health separately, then set `OpenAIGPTConfig(api_base=..., chat_model=...)`. |
| Chainlit import fails | `chainlit` extra not installed | Install the `chainlit` extra only when launching a UI workflow. |
| PDF/OCR parser import fails | Parser extra or native binary is missing | Choose another parser or install the relevant parser extra plus required system binary/model cache. |

## Safety defaults

- `VectorStoreConfig.full_eval` defaults to `False`.
- `TableChatAgentConfig.full_eval` defaults to `False`.
- `SQLChatAgentConfig.allow_dangerous_operations` defaults to `False`.
- `Neo4jChatAgentConfig.allow_dangerous_operations` and
  `ArangoChatAgentConfig.allow_dangerous_operations` default to `False`.

Do not override these defaults unless the data, database, and generated queries
are trusted. Route SQL/table/graph safety questions to
`sub-skills/data-sql-graph-agents/`.

## No-network smoke checks

Run these before live provider/service work:

```bash
python scripts/check_langroid_environment.py --json --optional
python sub-skills/agents-tasks-tools/scripts/core_agent_smoke.py
python sub-skills/llm-provider-config/scripts/provider_config_smoke.py --compact
python sub-skills/retrieval-doc-chat/scripts/rag_config_smoke.py --json
python sub-skills/data-sql-graph-agents/scripts/data_agent_safety_smoke.py
python sub-skills/integrations-mcp-chainlit/scripts/mcp_tool_smoke.py
```

Each helper is deterministic by default and avoids provider calls, live database
queries, long-running servers, downloads, or destructive writes.

## Routing failures

- Tool/task behavior: `sub-skills/agents-tasks-tools/references/troubleshooting.md`.
- Provider/model/key behavior: `sub-skills/llm-provider-config/references/troubleshooting.md`.
- Document parsing or retrieval: `sub-skills/retrieval-doc-chat/references/troubleshooting.md`.
- SQL/table/graph query safety: `sub-skills/data-sql-graph-agents/references/troubleshooting.md`.
- MCP/Chainlit/search/logging integration: `sub-skills/integrations-mcp-chainlit/references/troubleshooting.md`.
