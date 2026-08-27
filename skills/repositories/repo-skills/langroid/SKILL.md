---
name: langroid
description: "Use Langroid to build Python LLM agents, tools, tasks,
  RAG/document chat, provider configs, structured data agents, MCP integrations,
  Chainlit callbacks, and no-network smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Langroid Repo Skill

Use this repo skill when a task names Langroid or asks for Python LLM agent
workflows involving `ChatAgent`, `Task`, `ToolMessage`, providers, RAG,
structured data agents, MCP, Chainlit, or Langroid optional extras.

Langroid is a Python framework for building LLM-powered agents that use tools,
exchange messages, delegate tasks, retrieve from documents, and integrate with
providers and external tool systems.

## First checks

Read [`references/repo-provenance.md`](references/repo-provenance.md) when you
need to decide whether this skill matches a checkout or installed package
version. For install and extras selection, read
[`references/install-and-extras.md`](references/install-and-extras.md) and
[`references/optional-dependencies.md`](references/optional-dependencies.md).

Minimal package check:

```bash
python - <<'PY'
import langroid as lr
import langroid.language_models as lm
print(lr.ChatAgent, lr.Task, lr.ToolMessage)
print(lm.OpenAIGPTConfig().chat_model)
PY
```

No-network skill helper:

```bash
python scripts/check_langroid_environment.py --json --optional
```

## Route by task

| User task shape | Read |
| --- | --- |
| Create a `ChatAgent`, define/enable `ToolMessage`, wire handlers, use `Task`, delegate subtasks, route recipients, configure `done_sequences`, test with `MockLM`, or debug tool/task loops | [`sub-skills/agents-tasks-tools/SKILL.md`](sub-skills/agents-tasks-tools/SKILL.md) |
| Configure OpenAI-compatible models, Azure, Gemini, LiteLLM proxy, Ollama/local endpoints, Portkey, LangDB, HTTP clients, rotating keys, cached clients, embeddings, or model-name selection | [`sub-skills/llm-provider-config/SKILL.md`](sub-skills/llm-provider-config/SKILL.md) |
| Build document QA/RAG with `DocChatAgent`, parse PDFs/DOCX/URLs/Markdown/DataFrames, tune chunking/retrieval/reranking, choose vector stores or embeddings, or debug empty retrieval | [`sub-skills/retrieval-doc-chat/SKILL.md`](sub-skills/retrieval-doc-chat/SKILL.md) |
| Use `TableChatAgent`, `SQLChatAgent`, `Neo4jChatAgent`, `ArangoChatAgent`, CSV-to-KG, schema metadata, database URIs, query validators, or dangerous-operation safety controls | [`sub-skills/data-sql-graph-agents/SKILL.md`](sub-skills/data-sql-graph-agents/SKILL.md) |
| Convert MCP servers to Langroid tools, choose async/decorator MCP patterns, enable search/file tools, wire Chainlit callbacks, HTML logging, quiet/status output, or external integration smoke checks | [`sub-skills/integrations-mcp-chainlit/SKILL.md`](sub-skills/integrations-mcp-chainlit/SKILL.md) |

## Operating defaults

- Prefer deterministic `MockLM` or config-construction checks before making live
  LLM/provider calls.
- Use the smallest optional extra needed for the workflow; do not install
  `all` unless broad demo coverage is explicitly required.
- Treat API keys, local LLM servers, MCP subprocess transports, Chainlit apps,
  vector DB services, SQL/graph databases, model downloads, OCR, and GPU
  execution as optional live-backend work that needs explicit prerequisites.
- Keep security defaults unless the environment is trusted:
  `VectorStoreConfig.full_eval=False`, `TableChatAgentConfig.full_eval=False`,
  and SQL/graph `allow_dangerous_operations=False`.
- Do not depend on original repo examples or tests at runtime. Use this skill's
  bundled references and scripts.

## Bundled smoke scripts

Run these from this skill directory or pass their full path from another current
working directory:

```bash
python scripts/check_langroid_environment.py --json --optional
python sub-skills/agents-tasks-tools/scripts/core_agent_smoke.py
python sub-skills/llm-provider-config/scripts/provider_config_smoke.py --compact
python sub-skills/retrieval-doc-chat/scripts/rag_config_smoke.py --json
python sub-skills/data-sql-graph-agents/scripts/data_agent_safety_smoke.py
python sub-skills/integrations-mcp-chainlit/scripts/mcp_tool_smoke.py
```

These helpers avoid provider calls, live database queries, long-running servers,
network downloads, training, and destructive writes by default.

## Cross-cutting troubleshooting

Start with [`references/troubleshooting.md`](references/troubleshooting.md) for
install/import/extras, provider credential boundaries, security defaults, and
which sub-skill owns each failure surface. Use sub-skill troubleshooting files
for workflow-specific symptoms and recovery.
