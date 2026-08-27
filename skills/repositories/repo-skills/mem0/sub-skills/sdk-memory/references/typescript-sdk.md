# TypeScript SDK Reference

The TypeScript package is `mem0ai`. It exposes a hosted Platform `MemoryClient` from `mem0ai` and local OSS `Memory` from `mem0ai/oss`. Hosted SDK options use camelCase in TypeScript and are converted to API snake_case where appropriate; `filters` payloads are intentionally passed through so API filter keys such as `user_id`, `agent_id`, `created_at`, and `categories` should remain snake_case.

## Hosted Platform Client

Imports:

```ts
import { MemoryClient, Feedback } from "mem0ai";
// or: import MemoryClient from "mem0ai";
```

Constructor:

```ts
const client = new MemoryClient({
  apiKey: process.env.MEM0_API_KEY!,
  host: process.env.MEM0_HOST, // optional; defaults to https://api.mem0.ai
});
```

Current method surface:

| Method | Shape and notes |
| --- | --- |
| `add(messages, options)` | `messages` must be a non-empty array of `{ role, content }`; options include `userId`, `agentId`, `appId`, `runId`, `metadata`, `infer`, `customCategories`, `customInstructions`, `timestamp`, `structuredDataSchema` |
| `search(query, options?)` | posts to v3 search; rejects top-level entity params; use `filters` |
| `get(memoryId)` | gets one memory |
| `getAll(options?)` | posts to v3 list; rejects top-level entity params; supports `page`, `pageSize`, `latestOnly`, `categories`, dates |
| `update(memoryId, { text, metadata, timestamp })` | at least one field is required |
| `delete(memoryId, { deleteLinked? })` | deletes one memory; `deleteLinked` serializes to `delete_linked` |
| `deleteAll({ userId?, agentId?, appId?, runId? })` | destructive scoped delete through query parameters |
| `history(memoryId)` | returns memory history |
| `batchUpdate([{ memoryId, text }])` / `batchDelete([memoryId])` | Platform batch operations |
| `feedback({ memoryId, feedback, feedbackReason })` | sends feedback to `/v1/feedback/` |
| `createMemoryExport({ schema, filters, exportInstructions? })` | requires both `schema` and `filters` |
| `getMemoryExport({ memoryExportId?, filters? })` | requires export id or filters |
| `getProject` / `updateProject` | project-level categories/instructions; requires org/project resolved by API key |

### Hosted CRUD/Search Pattern

```ts
import { MemoryClient } from "mem0ai";

const client = new MemoryClient({ apiKey: process.env.MEM0_API_KEY! });

await client.add(
  [{ role: "user", content: "Alice prefers window seats on flights." }],
  {
    userId: "alice",
    metadata: { source: "booking-chat" },
    infer: true,
  },
);

const search = await client.search("travel seating preference", {
  filters: { user_id: "alice" },
  topK: 5,
  threshold: 0.1,
  latestOnly: true,
});

const page = await client.getAll({
  filters: { user_id: "alice" },
  page: 1,
  pageSize: 50,
});
```

Migration-sensitive rule: `search` and `getAll` reject `{ userId: "alice" }`, `{ user_id: "alice" }`, `{ agentId: ... }`, `{ appId: ... }`, or `{ runId: ... }` at the top level. Put entity scope inside `filters`, and keep filter keys in API snake_case.

### Hosted Update/Delete/Export/Feedback

```ts
await client.update("memory-id", {
  text: "Alice prefers aisle seats for short flights.",
  metadata: { category: "travel" },
});

await client.delete("memory-id", { deleteLinked: true });
await client.deleteAll({ userId: "alice" });
await client.batchUpdate([{ memoryId: "id1", text: "Updated fact" }]);
await client.batchDelete(["id1", "id2"]);

await client.feedback({
  memoryId: "memory-id",
  feedback: Feedback.POSITIVE,
  feedbackReason: "Accurate preference",
});

const exportJob = await client.createMemoryExport({
  schema: { type: "object", properties: { memory: { type: "string" } } },
  filters: { user_id: "alice" },
  exportInstructions: "Group by category",
});

const exportData = await client.getMemoryExport({ memoryExportId: exportJob.id });
```

`createMemoryExport` intentionally preserves user-controlled `schema` and `filters` keys; do not camelCase filter fields inside the schema or filter blob unless the API docs specifically request it.

## OSS Memory from `mem0ai/oss`

Import:

```ts
import { Memory } from "mem0ai/oss";
```

Constructor:

```ts
const memory = new Memory();
```

The default Node OSS path is local-friendly but still may require provider API keys depending on configured LLM/embedder. Use `provider-configuration` for production provider and vector-store setup.

Current method surface:

| Method | Shape and notes |
| --- | --- |
| `add(messages, config)` | messages string or message array; `config` requires one of `userId`, `agentId`, `runId`; options include `metadata`, `filters`, `infer`; `timestamp` raises Platform-only guidance |
| `search(query, config)` | requires `filters` with one of `user_id`, `agent_id`, `run_id`; supports `topK`, `threshold`, `explain`; rejects top-level entity params |
| `getAll(config)` | requires `filters` with one entity key; supports `topK` |
| `get(memoryId)` | returns one memory or `null` |
| `update(memoryId, data)` | replaces memory text |
| `delete(memoryId)` | deletes one memory |
| `deleteAll({ userId?, agentId?, runId? })` | destructive scoped delete; requires at least one scope |
| `history(memoryId)` | returns local history array |
| `reset()` | clears local history and vector collection; destructive |

### OSS CRUD/Search Pattern

```ts
import { Memory } from "mem0ai/oss";

const memory = new Memory();

const added = await memory.add("Alice dislikes thriller movies.", {
  userId: "alice",
  metadata: { category: "movie_recommendations" },
  infer: true,
});

const results = await memory.search("What movies should I avoid?", {
  filters: { user_id: "alice", category: "movie_recommendations" },
  topK: 5,
  threshold: 0.1,
  explain: true,
});

const all = await memory.getAll({ filters: { user_id: "alice" } });
const one = await memory.get(added.results[0].id);
await memory.update(added.results[0].id, "Alice prefers optimistic sci-fi movies.");
await memory.deleteAll({ userId: "alice" });
```

Entity option casing differs by operation:

- OSS `add` and `deleteAll` use TypeScript-friendly top-level `userId`, `agentId`, and `runId`.
- OSS `search` and `getAll` use `filters` with API/storage keys `user_id`, `agent_id`, and `run_id`.
- Hosted `search` and `getAll` follow the same `filters` rule.

## TypeScript Migration Notes

| Concern | Hosted `MemoryClient` | OSS `Memory` |
| --- | --- | --- |
| Package import | `mem0ai` | `mem0ai/oss` |
| Constructor | `new MemoryClient({ apiKey })` | `new Memory(config?)` |
| Messages | hosted `add` expects an array | OSS `add` accepts string or array |
| Search filters | `{ filters: { user_id: "alice" } }` | `{ filters: { user_id: "alice" } }` |
| Add scope | top-level `{ userId: "alice" }` in current types | top-level `{ userId: "alice" }` required |
| Update payload | object with `text`, `metadata`, `timestamp` | string `data` only |
| Batch/export/feedback | supported by hosted client | not part of OSS `Memory` |
| Return casing | SDK converts API responses to camelCase in many hosted types | OSS returns mixed storage fields; filters often appear as snake_case |
| Destructive clear | `deleteAll` scoped by entity options | `deleteAll` scoped; `reset()` wipes local collection/history |

## Minimal TypeScript Checks

For hosted client import only:

```ts
import { MemoryClient } from "mem0ai";
console.log(typeof MemoryClient);
```

For OSS import only:

```ts
import { Memory } from "mem0ai/oss";
console.log(typeof Memory);
```

Do not instantiate hosted `MemoryClient` unless a real `MEM0_API_KEY` is present; initialization pings the API asynchronously. Do not instantiate OSS `Memory` in a generic import check unless provider keys/backends are configured, because initialization may probe embeddings and vector stores.
