---
name: sdk-memory
description: "Use Mem0 SDKs for hosted Platform clients and local OSS memory in
  Python and TypeScript, including CRUD, search, async clients, entity filters,
  metadata, categories, export, feedback, and migration-sensitive API
  differences."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mem0 SDK Memory

Use this sub-skill when the task asks for Mem0, `mem0ai`, a memory layer, memory CRUD/search, Platform SDK calls, OSS `Memory()` usage, TypeScript `MemoryClient`, `mem0ai/oss`, async memory calls, retrieve-generate-store flows, filters, metadata, categories, exports, feedback, or SDK migration debugging.

## Route First

- Use this sub-skill for Python `MemoryClient`, `AsyncMemoryClient`, `Memory`, `AsyncMemory`, TypeScript hosted `MemoryClient`, and TypeScript OSS `Memory` from `mem0ai/oss`.
- Use [Python SDK](references/python-sdk.md) for imports, live signatures, sync/async Python examples, and Platform-vs-OSS differences.
- Use [TypeScript SDK](references/typescript-sdk.md) for hosted `MemoryClient`, OSS `Memory`, camelCase/snake_case option differences, exports, and feedback.
- Use [Memory Operations](references/memory-operations.md) for add/search/update/delete patterns, retrieve-generate-store workflows, filters, metadata, categories, export, feedback, and migration notes.
- Use [Troubleshooting](references/troubleshooting.md) for empty search results, import/install failures, API keys, optional backends, validation errors, and SDK misuse.

## Sibling Boundaries

- Route provider, vector store, embedder, LLM, reranker, graph-memory, and optional dependency selection to `provider-configuration`.
- Route terminal commands, CLI config, JSON output, stdin/file workflows, import/export through commands, and `mem0 init/add/search` behavior to `cli-memory`.
- Route REST server deployment, Docker Compose, OpenMemory, MCP server hosting, API keys for self-hosted services, migrations, and operational backups to `self-hosted-openmemory`.
- Route editor/agent plugins, framework cookbooks, Vercel AI SDK provider wrapping, MCP plugin config, hooks, OpenClaw, and Pi Agent plugin tasks to `integrations-plugins`.

## Fast Decision Tree

1. Hosted Platform SDK? Use `MemoryClient` / `AsyncMemoryClient` in Python or `MemoryClient` in TypeScript; it needs a Mem0 API key and talks to `https://api.mem0.ai` by default.
2. Local OSS memory? Use Python `Memory` / `AsyncMemory` or TypeScript `Memory` from `mem0ai/oss`; it needs provider/backend configuration, often OpenAI credentials by default.
3. Search or list memories? Put entity scope in `filters`, for example `filters={"user_id": "alice"}` in Python and `{ filters: { user_id: "alice" } }` in TypeScript.
4. Add or bulk delete by entity? Follow the SDK-specific options in [Memory Operations](references/memory-operations.md); current SDKs keep top-level entity options for add/delete-all, while search/get-all require `filters`.
5. Debug before changing code? Run `python scripts/inspect_mem0_sdk.py --json` to inspect installed Python exports/signatures without credentials, then `python scripts/mem0_sdk_smoke.py --mode plan --language both` to generate safe smoke snippets.

## Minimal Patterns

Python hosted Platform:

```python
from mem0 import MemoryClient

client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
client.add("User prefers vegetarian meals", user_id="alice", metadata={"source": "chat"})
results = client.search("dietary preferences", filters={"user_id": "alice"}, top_k=5)
```

Python OSS:

```python
from mem0 import Memory

memory = Memory()
memory.add("User prefers vegetarian meals", user_id="alice", metadata={"source": "chat"})
results = memory.search("dietary preferences", filters={"user_id": "alice"}, top_k=5)
```

TypeScript hosted Platform:

```ts
import { MemoryClient } from "mem0ai";

const client = new MemoryClient({ apiKey: process.env.MEM0_API_KEY! });
await client.add([{ role: "user", content: "User prefers vegetarian meals" }], { userId: "alice" });
const results = await client.search("dietary preferences", { filters: { user_id: "alice" }, topK: 5 });
```

TypeScript OSS:

```ts
import { Memory } from "mem0ai/oss";

const memory = new Memory();
await memory.add("User prefers vegetarian meals", { userId: "alice", metadata: { source: "chat" } });
const results = await memory.search("dietary preferences", { filters: { user_id: "alice" }, topK: 5 });
```

## Safety Notes

- Do not print API keys, provider keys, memory contents from production users, or full environment dumps.
- Prefer read-only inspection before live API calls. The bundled scripts default to help/plan/inspection modes and do not require credentials unless explicitly requested.
- Never instruct future agents to run source-repository tests or examples; use the bundled references and scripts here.
- Treat `reset`, wildcard deletes, and scoped `delete_all` / `deleteAll` as destructive. Confirm scope and tenant before running them.
