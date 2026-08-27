# Memory Operations Reference

Use this reference to design Mem0 SDK workflows without reopening the source repository. It covers hosted Platform and OSS SDK call-site behavior in Python and TypeScript.

## Core Operation Flow

1. Choose mode: hosted Platform for managed API/dashboard/scaling, OSS for local in-process memory.
2. Scope every memory to a user/session: use `user_id`, `agent_id`, `app_id`, and/or `run_id` where supported.
3. Add when a user states a durable preference, fact, goal, decision, correction, or feedback.
4. Search before generation to retrieve relevant context.
5. Generate with retrieved memories as auxiliary context, not as hidden authoritative truth.
6. Store only new durable facts after generation or user confirmation.
7. Update/delete when a memory is wrong, stale, or subject to erasure.

## Add

Mem0 accepts OpenAI-style messages, and most SDKs also accept a simple string.

### Python Platform

```python
client.add(
    "Alice prefers vegetarian meals.",
    user_id="alice",
    metadata={"source": "profile", "category": "diet"},
    infer=True,
)
```

### Python OSS

```python
memory.add(
    "Alice prefers vegetarian meals.",
    user_id="alice",
    metadata={"source": "profile", "category": "diet"},
    infer=True,
)
```

### TypeScript Platform

```ts
await client.add(
  [{ role: "user", content: "Alice prefers vegetarian meals." }],
  { userId: "alice", metadata: { source: "profile", category: "diet" }, infer: true },
);
```

### TypeScript OSS

```ts
await memory.add("Alice prefers vegetarian meals.", {
  userId: "alice",
  metadata: { source: "profile", category: "diet" },
  infer: true,
});
```

`infer=True` / `infer: true` lets Mem0 extract concise facts and decide add/update/delete actions. `infer=False` / `infer: false` stores raw message content and can duplicate later inferred facts if mixed for the same scope.

## Search and Get All

Search/list operations are where migration bugs most often happen. For current Python and TypeScript SDKs, entity IDs go inside `filters` for `search` and `get_all` / `getAll`.

Correct:

```python
client.search("dietary preferences", filters={"user_id": "alice"})
memory.search("dietary preferences", filters={"user_id": "alice"})
```

```ts
await client.search("dietary preferences", { filters: { user_id: "alice" } });
await memory.search("dietary preferences", { filters: { user_id: "alice" } });
```

Incorrect for search/get-all:

```python
client.search("dietary preferences", user_id="alice")
```

```ts
await client.search("dietary preferences", { userId: "alice" });
```

For Platform filters, nested logical operators are passed through:

```python
filters = {
    "AND": [
        {"user_id": "alice"},
        {"created_at": {"gte": "2024-01-01T00:00:00Z"}},
        {"NOT": {"categories": {"in": ["spam", "test"]}}},
    ]
}
client.search("travel preferences", filters=filters, top_k=10)
```

For OSS filters, include at least one entity key plus optional metadata constraints:

```python
memory.search(
    "movie preferences",
    filters={"user_id": "alice", "category": "movie_recommendations"},
    top_k=5,
    explain=True,
)
```

```ts
await memory.search("movie preferences", {
  filters: { user_id: "alice", category: "movie_recommendations" },
  topK: 5,
  explain: true,
});
```

## Update

Use update when a specific memory ID is known and the fact should be corrected in place.

| SDK | Call shape |
| --- | --- |
| Python Platform | `client.update(memory_id, text="...", metadata={...}, timestamp="...")` |
| TypeScript Platform | `client.update(memoryId, { text: "...", metadata: {...}, timestamp: "..." })` |
| Python OSS | `memory.update(memory_id, data="...", metadata={...})` |
| TypeScript OSS | `memory.update(memoryId, "new text")` |

Platform batch update exists for large correction jobs:

```python
client.batch_update([{"memory_id": "id1", "text": "Updated fact"}])
```

```ts
await client.batchUpdate([{ memoryId: "id1", text: "Updated fact" }]);
```

## Delete and Reset

Use `delete` when you know the memory ID. Use scoped bulk delete only with explicit user/agent/run/project intent.

| SDK | Delete one | Delete scope | Full wipe |
| --- | --- | --- | --- |
| Python Platform | `client.delete("id", delete_linked=False)` | `client.delete_all(user_id="alice")` | Avoid unless explicitly requested |
| TypeScript Platform | `client.delete("id", { deleteLinked: true })` | `client.deleteAll({ userId: "alice" })` | Avoid; wildcard patterns require explicit confirmation |
| Python OSS | `memory.delete("id")` | `memory.delete_all(user_id="alice")` | `memory.reset()` |
| TypeScript OSS | `memory.delete("id")` | `memory.deleteAll({ userId: "alice" })` | `memory.reset()` |

`delete_linked` / `deleteLinked` is useful when a current Platform memory superseded older linked memories and deleting only the latest would allow old facts to resurface.

## Metadata, Categories, and Custom Extraction

Use `metadata` for application-owned fields such as source, tenant, category, document ID, or retention policy. Include metadata at add time and update it when correcting a memory.

Use Platform categories in two ways:

- Per-add custom categories: `custom_categories` in Python or `customCategories` in TypeScript.
- Project-level custom categories/instructions: `client.project` in Python or `getProject` / `updateProject` in TypeScript.

Keep filter key casing consistent:

- API and Platform filter blobs usually use snake_case keys such as `user_id`, `agent_id`, `created_at`, and `categories`.
- TypeScript method option names outside `filters` use camelCase such as `topK`, `latestOnly`, `customCategories`, and `feedbackReason`.

## Export and Feedback

Platform clients support memory export and feedback. OSS `Memory` does not expose these operations.

Python:

```python
client.feedback("memory-id", feedback="NEGATIVE", feedback_reason="Outdated after user correction")
job = client.create_memory_export(
    schema='{"type":"object","properties":{"memory":{"type":"string"}}}',
    filters={"user_id": "alice"},
)
exported = client.get_memory_export(filters={"user_id": "alice"})
```

TypeScript:

```ts
await client.feedback({
  memoryId: "memory-id",
  feedback: Feedback.NEGATIVE,
  feedbackReason: "Outdated after user correction",
});

const job = await client.createMemoryExport({
  schema: { type: "object", properties: { memory: { type: "string" } } },
  filters: { user_id: "alice" },
});

const exported = await client.getMemoryExport({ memoryExportId: job.id });
```

Feedback values are `POSITIVE`, `NEGATIVE`, `VERY_NEGATIVE`, or null/omitted. Python uppercases feedback strings before validation.

## Retrieve-Generate-Store Pattern

Use this pattern when adding Mem0 to an agent workflow:

```python
def answer_with_memory(client, user_id: str, user_message: str, llm_call):
    retrieved = client.search(user_message, filters={"user_id": user_id}, top_k=5)
    memory_context = "\n".join(item.get("memory", "") for item in retrieved.get("results", []))

    answer = llm_call(
        system=f"Use these memories when relevant:\n{memory_context}",
        user=user_message,
    )

    client.add(
        [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer},
        ],
        user_id=user_id,
        metadata={"source": "agent-chat"},
    )
    return answer
```

Operational guidance:

- Search before generation, not after, so relevant memories can influence the answer.
- Store after generation only when the conversation includes durable information.
- Keep the user scope stable across add/search/update/delete. Empty searches often come from adding under one scope and searching another.
- In async services, await add/search calls or explicitly decide that storage can be fire-and-forget with error logging.

## Empty Search Diagnostic Checklist

1. Confirm the add call succeeded. Hosted Platform `add` can return a pending event; allow processing time or poll event status in workflows that need immediate verification.
2. Confirm the same scope is used for add and search: top-level `user_id` / `userId` on add maps to `filters: { user_id: ... }` on search.
3. Confirm search uses `filters`, not top-level entity params.
4. Reduce `threshold`, increase `top_k` / `topK`, and try a query closer to the stored fact.
5. Check `infer=False` vs inferred storage. Raw transcripts and extracted facts search differently.
6. Check metadata/category filters for casing and operator errors.
7. For OSS, confirm provider dependencies, vector store initialization, embedding dimensions, and configured collection/path.
8. For async code, confirm `await memory.add(...)` completed before searching.

## Dual Python/TypeScript Integration Plan

For teams using Python services and TypeScript apps under one user scope:

- Choose one canonical scope contract: `user_id`, optional `agent_id`, optional `run_id`, and any tenant metadata.
- Hosted production: use Python/TS Platform clients with the same `MEM0_API_KEY` project and `filters: { user_id }` search contract.
- Local tests: use Python `Memory` and/or TypeScript `Memory` with deterministic provider/vector-store config from `provider-configuration`.
- Normalize response handling: Python often returns snake_case fields; TypeScript hosted responses often surface camelCase fields, while filter blobs remain snake_case.
- Keep destructive cleanup environment-specific: test scopes can call scoped delete/reset; production cleanup should require explicit approval and audit logging.
