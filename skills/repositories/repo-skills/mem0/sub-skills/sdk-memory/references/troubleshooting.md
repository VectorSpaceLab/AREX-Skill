# SDK Memory Troubleshooting

Start with read-only checks. The bundled scripts do not require credentials unless you explicitly request live behavior.

```bash
python scripts/inspect_mem0_sdk.py --json
python scripts/mem0_sdk_smoke.py --mode plan --language both
```

## Install and Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mem0'` | Python package not installed in the active environment | Install `mem0ai` in the environment that runs the app; verify with `python scripts/inspect_mem0_sdk.py` |
| `import mem0` works but exports are missing | Wrong package version or shadowing by a local `mem0.py`/folder | Print `mem0.__file__` privately, rename local shadowing files, reinstall `mem0ai` |
| TypeScript cannot import `mem0ai` | Package missing or wrong project/package manager | Install `mem0ai`; use project package manager conventions; verify `node_modules/mem0ai` exists |
| TypeScript cannot import `mem0ai/oss` | Old package version or bundler export resolution issue | Upgrade `mem0ai`; check ESM/TS config; use a direct import test before app integration |
| Hosted client throws during construction/init | Missing/invalid API key or host/network issue | Set `MEM0_API_KEY`, pass `apiKey`, or check custom `host`; do not log the key |

## API Key and Environment Issues

Hosted clients need Mem0 Platform credentials:

- Python: `MemoryClient(api_key="...")` or `MEM0_API_KEY`.
- TypeScript: `new MemoryClient({ apiKey: process.env.MEM0_API_KEY! })`.
- A custom `host` is optional; default is `https://api.mem0.ai`.

OSS memory often needs provider credentials and local backends:

- Python `Memory()` defaults include OpenAI for LLM/embedding and local Qdrant path plus SQLite history.
- TypeScript OSS defaults are local-friendly but can still initialize LLM/embedder/vector-store providers.
- Provider, vector-store, embedder, reranker, and graph setup belongs in `provider-configuration`.

Do not paste or print API keys in troubleshooting output. Redact environment displays to variable presence only.

## Entity Filter Validation Errors

Common error text:

- `Top-level entity parameters ... are not supported in search(). Use filters={'user_id': '...'} instead.`
- `filters must contain at least one of: user_id, agent_id, run_id.`
- `One of the filters: userId, agentId or runId is required!`

Fix by matching the operation-specific scope shape:

| Operation | Correct scope shape |
| --- | --- |
| Python Platform `search` / `get_all` | `filters={"user_id": "alice"}` |
| TypeScript Platform `search` / `getAll` | `{ filters: { user_id: "alice" } }` |
| Python OSS `search` / `get_all` | `filters={"user_id": "alice"}` |
| TypeScript OSS `search` / `getAll` | `{ filters: { user_id: "alice" } }` |
| Python OSS `add` / `delete_all` | `user_id="alice"` |
| TypeScript OSS `add` / `deleteAll` | `{ userId: "alice" }` |
| TypeScript Platform `add` / `deleteAll` | `{ userId: "alice" }` |

When in doubt, use `filters` for search/list and TypeScript camelCase top-level options only where the method type explicitly defines them.

## Empty Search After Add

Use this checklist before changing providers or rewriting code:

1. Confirm add completed. Hosted Platform add may return a pending event; workflows that need read-after-write should wait/poll before searching.
2. Confirm the same project/API key, host, and collection/backend are used for add and search.
3. Confirm scope mapping: TypeScript `add(..., { userId: "alice" })` should search with `{ filters: { user_id: "alice" } }`.
4. Confirm no top-level entity params are used in search/get-all.
5. Query close to the stored fact, lower `threshold`, and increase `top_k` / `topK`.
6. Remove category/date/metadata filters temporarily; add them back one by one.
7. Check `infer=False`/`infer: false`; raw messages may not match the expected extracted fact.
8. For OSS, verify the vector store collection/path, embedding dimensions, provider credentials, and async initialization.
9. For async code, ensure `await add` completes before `search`.
10. Inspect response shape: hosted add may return status/event data, while OSS add returns `results` with memory IDs/events.

## Data and Config Validation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `messages must be str, dict, or list[dict]` | Python add received an unsupported input | Pass a string, a single `{role, content}` dict, or a list of message dicts |
| `Cannot process an empty messages payload` | TypeScript hosted add received an empty array | Pass at least one message |
| `messages array cannot contain only blank content` | TypeScript OSS add received blank content | Trim or validate user input before add |
| `Invalid query: cannot be empty` | Python hosted search got whitespace | Validate/trim query before search |
| `At least one of text, metadata, or timestamp must be provided` | Platform update body is empty | Include `text`, `metadata`, and/or `timestamp` |
| `Missing filters or schema` | TypeScript export creation lacks required fields | Pass both `schema` and `filters` |
| `Missing memoryExportId or filters` | Export retrieval lacks selector | Pass `memoryExportId` or `filters` |
| Temporal feature error in OSS | `timestamp` or `referenceDate` used with local OSS SDK | Remove temporal parameter or use hosted Platform feature |

## Optional Dependency and Backend Failures

SDK call-site errors can be symptoms of provider/backend setup:

- Qdrant, pgvector, Redis, Neo4j, graph, reranker, or model import errors should be handled by `provider-configuration`.
- Embedding dimension mismatch usually means vector-store collection config and embedder model changed independently.
- Local history errors often point to SQLite/history-store path permissions or a missing serverless history provider.
- TypeScript OSS initialization may auto-detect embedding dimension; failures can occur before the first public method finishes.

Do not solve provider failures by installing every optional dependency. Pick the narrow backend/provider required by the user's workflow.

## API Misuse and Migration Traps

- Hosted Platform `search` and `get_all` moved toward v3 request bodies and reject top-level entity parameters.
- TypeScript option casing is mixed by design: method options are camelCase, but `filters` keys remain API/storage keys.
- Python OSS `delete_all(user_id=...)` differs from search/list `filters={"user_id": ...}`.
- Platform `delete_linked` / `deleteLinked` is opt-in; use it only when old linked memories should be removed too.
- `reset()` is local OSS destructive cleanup, not the normal way to delete a Platform user's memories.
- Feedback/export are Platform client capabilities, not local OSS `Memory` operations.
- Project categories/instructions are project-level Platform settings; per-call metadata is not the same thing.

## Workflow-Specific Failures

### Retrieve-generate-store stores irrelevant facts

- Search before generation and add after generation only for durable facts.
- Include source metadata such as `source`, `conversation_id`, or `tenant`.
- Use `infer=True` for fact extraction unless raw transcript storage is intentional.
- Consider user confirmation for sensitive memories.

### Dual Python/TS integration returns inconsistent fields

- Normalize response fields at the app boundary: Python payloads often use snake_case; TypeScript hosted types expose camelCase for responses but preserve `filters` blobs.
- Standardize on `user_id`/`agent_id`/`run_id` in filter payloads across languages.
- Add integration tests that add in one language/client and search with the other using the same Platform project.

### Async code appears flaky

- Await `AsyncMemoryClient`/`AsyncMemory` operations.
- Avoid immediate search after hosted Platform add unless the workflow accounts for pending processing.
- Log failed fire-and-forget add calls; otherwise storage failures become silent personalization gaps.

## When to Escalate to Sibling Sub-skills

- Provider import, model, vector-store, graph, reranker, collection, dimension, or optional dependency errors: `provider-configuration`.
- Shell commands, JSON CLI output, stdin/file add, CLI import/export, or `mem0 init`: `cli-memory`.
- Docker, REST server, OpenMemory dashboard/API/MCP, auth, migrations, and backups: `self-hosted-openmemory`.
- Agent/editor plugins, Vercel AI SDK provider, MCP plugin hooks, and framework integration code: `integrations-plugins`.
