# Tools, Memory, MCP, and Sandbox

## Tool Categories

RAGFlow agent workflows can use several tool styles:

- In-canvas tools under an `Agent` component, represented as component configs in `Agent.params.tools`.
- Sub-agent components, exposed to a supervisor Agent through a callable schema with `user_prompt`, `reasoning`, and `context`.
- Built-in Python tool components such as Retrieval, CodeExec, ExeSQL, HTTP/search/finance/weather/email/source tools, and crawler-style tools.
- Plugin-style LLM tools loaded from embedded plugin packages; plugins provide metadata and an `invoke(...) -> str` contract.
- MCP tools bound through configured MCP server records and exposed to the Agent as OpenAI-style function tools.

Tool calls are traced through the canvas callback with the path, tool name, arguments, result, and elapsed time. Do not include secrets in tool arguments if traces may be returned to users.

## Built-In Tools to Recognize

Common tool component classes include:

- `Retrieval`: dataset and memory retrieval, returns `formalized_content`, JSON chunks, and citation references.
- `CodeExec`: sandboxed Python or JavaScript execution with strict output contracts and collected artifacts.
- `ExeSQL`: SQL execution against configured databases; validate SSRF/network and credential safety before live use.
- `Crawler`, `DuckDuckGo`, `Google`, `GoogleScholar`, `Wikipedia`, `PubMed`, `ArXiv`, `TavilySearch`, `TavilyExtract`: network-backed search/crawl tools; require user approval and credentials where applicable.
- `Email`, `GitHub`, `DeepL`, `QWeather`, `YahooFinance`, `AkShare`, `TuShare`, `WenCai`, `Jin10`, `SearXNG`: integration-specific tools with credential, network, or service availability constraints.

When drafting or debugging a tool-enabled Agent, ensure each tool has a clear function name, concise description, required parameters, and explicit boundaries in the system prompt.

## Retrieval Tool Usage

`Retrieval` can read from datasets and memories.

Important dataset parameters:

- `dataset_ids` or legacy `kb_ids`: selected datasets; variable references can resolve dataset names or IDs.
- `similarity_threshold`, `keywords_similarity_weight`, `top_n`, `top_k`: ranking and result sizing controls.
- `rerank_id`: optional reranker model.
- `empty_response`: output when no chunks match.
- `use_kg`, `cross_languages`, `toc_enhance`, `meta_data_filter`: advanced retrieval behavior.

Important outputs:

- `formalized_content`: prompt-ready text assembled from retrieved chunks.
- `json`: raw-ish chunk list for downstream data operations.
- Canvas references: chunks/doc aggregations for citations and message references.

Use the `dataset-ingestion-retrieval` sub-skill for retrieval internals, chunk parsing, metadata filters, and dataset state debugging.

## Memory Integration

Memory stores raw and extracted conversation context. It supports raw, semantic, episodic, and procedural memory types depending on configuration.

Behavior-level surfaces:

- Create/list/update/delete memories with fields such as name, memory type, embedding model, LLM, permissions, memory size, forgetting policy, prompts, and avatar/description.
- Add messages with `memory_id`, `agent_id`, `session_id`, `user_input`, and `agent_response`.
- Search messages with `memory_id`, query, thresholds, `top_n`, and optional `agent_id`, `session_id`, or `user_id` filters.
- Fetch recent messages for memory IDs, agent ID, session ID, and limit.
- Toggle or forget individual memory messages.

Agent workflow pattern:

1. Configure a memory with compatible embedding and chat models.
2. Use a Retrieval component with `memory_ids` to bring relevant memory into the prompt.
3. Use a Message component configured to save selected conversation content back to memory.
4. Keep `agent_id`, `session_id`, and `user_id` attribution consistent so searches return the intended history.

API-key callers can supply an external user subject for messages; session/JWT callers are attributed to the authenticated user. Avoid spoofing user IDs unless the integration intentionally maps external identities.

## MCP Retrieval Server

The RAGFlow MCP server exposes a `ragflow_retrieval` tool through MCP `list_tools` and `call_tool`.

Key behavior:

- Backend base URL defaults to a local RAGFlow API base but should be configured per deployment.
- Self-host mode requires a server-side API key. Host mode expects the client to provide an API key or bearer-style header per request.
- Transports include legacy SSE at `/sse` and streamable HTTP at `/mcp`; streamable HTTP JSON responses are enabled by default when that transport is enabled.
- `ragflow_retrieval` accepts `question`, optional `dataset_ids`, optional `document_ids`, and retrieval parameters such as page, page size, thresholds, top K, reranker, keyword mode, and force-refresh.
- If `dataset_ids` is omitted or empty, the server resolves all accessible dataset IDs for the provided key and searches across them.
- Dataset/document metadata is cached with a short TTL and paginated without exceeding REST API page-size limits.

Safe setup checklist:

- Bind local development servers to loopback unless the user explicitly needs network exposure.
- Keep the RAGFlow API key separate from the MCP server URL; never embed a real key in public examples.
- In host mode, verify client headers are supplied and do not accidentally fall back to a shared host key.
- In self-host mode, verify the key has access only to intended datasets.
- Use dataset IDs or document IDs to restrict search when handling sensitive corpora.

## Sandbox and CodeExec

`CodeExec` supports Python and JavaScript/Node-style code through a sandbox provider system or legacy HTTP sandbox manager. It is powerful and must be treated as a potentially dangerous live execution path.

Contract rules:

- Python code must define `main(...)`; JavaScript should export `main`.
- The component has exactly one business output in addition to system outputs. Reserved names include `content`, `actual_type`, `attachments`, `_ERROR`, `_ARTIFACTS`, `_ATTACHMENT_CONTENT`, `raw_result`, `_created_time`, and `_elapsed_time`.
- The returned top-level value must be String, Number, Boolean, Object, Array, or Null.
- Declared output type is validated against the returned value; mismatches set `_ERROR` and still render canonical content when possible.
- Artifacts saved under `artifacts/` can be collected and exposed as image/download markdown plus stable attachment text.

Operational facts:

- The sandbox design uses gVisor isolation, optional seccomp, Docker-based executor manager, static Python AST inspection, and language-specific base images.
- Python base packages include commonly used data packages such as pandas, numpy, matplotlib, and requests; matplotlib should use a non-interactive backend and save files rather than display windows.
- JavaScript base packages include axios by default.
- Code execution can fall back from provider mode to a legacy HTTP sandbox endpoint if provider modules are unavailable.

Safety defaults:

- Do not run CodeExec by default during skill use. Ask before executing user-provided code.
- Reject or isolate code that reads host files, spawns subprocesses, opens sockets unexpectedly, or attempts credential discovery.
- Treat generated artifacts as untrusted output until inspected.
- Keep sandbox hostnames, private bucket details, and storage internals out of public guidance.

## Plugin-Style Tools

Plugin LLM tools expose metadata and an invoke method. Metadata includes name, display name, description, display description, parameters, parameter types, and required flags. The LLM sees the functional description; the UI can show display fields or i18n keys. Keep plugin return values textual and deterministic where possible.
