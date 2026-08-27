# Integrations And Migration Troubleshooting

## Framework Integrations

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Framework import fails | Optional framework package is not installed | Install the framework integration dependency separately from MemMachine. |
| Tool executes but finds no memories | Missing/wrong project or user/session context | Pass explicit org/project and memory metadata through graph/tool state. |
| Agent stores too much transient data | Add-memory hook runs on every token/message without policy | Store only stable facts, decisions, preferences, or approved conversation turns. |
| Provider-backed example fails | Missing LLM provider key, model ID, quota, or network access | Verify provider setup separately; keep MemMachine memory checks independent. |
| MCP client cannot call tools | Wrong stdio/HTTP mode, context config, command PATH, or auth | Validate entry point help/imports and configure context/secret values in the MCP client. |

## Platform Plugins

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Plugin action 401/403 | API key not stored in platform secret manager or wrong header | Use bearer auth and mask the key. |
| 404 on platform REST calls | Wrong base URL path prefix | Confirm whether the target endpoint expects `/api/v2` or `/v2`. |
| Action schema mismatch | Platform action fields differ from MemMachine REST payload | Map project context, query/content, metadata, and memory type explicitly. |
| Cannot test locally | Platform runtime required | Use a direct SDK/REST health and add/search smoke against a test project first. |

## Migration Files

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Probe says JSON root is unknown | Export format differs from ChatGPT/OpenAI/LoCoMo assumptions | Inspect redacted keys/counts and write a small adapter before upload. |
| Messages missing content | Some export entries are system/tool/attachment-only or malformed | Skip empty entries and record counts; do not invent content. |
| Duplicate memories after retry | No source ID/import batch metadata | Add deterministic metadata and check existing entries before re-upload. |
| Upload rate-limited or slow | Large export or provider-backed semantic processing | Batch uploads, back off, and consider episodic-only import first. |
| Search after import is empty | Wrong metadata context or semantic ingestion delay | List by import batch, then search with matching `set_metadata`; allow ingestion time. |

## Privacy Rules

- Summarize export schema and counts, not raw conversation text.
- Show at most short redacted snippets when the user explicitly asks for a parse
  diagnosis.
- Never include API keys, account tokens, database passwords, or full private
  chat exports in generated commands or reports.
- Ask before uploading, deleting, or reprocessing memories.
