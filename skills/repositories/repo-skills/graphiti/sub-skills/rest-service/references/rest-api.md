# REST API reference

The REST service is a FastAPI app exposed as `graph_service.main:app`. It wraps
Graphiti operations behind request/response DTOs.

## Ingest and mutation routes

| Method | Path | Request | Response | Notes |
| --- | --- | --- | --- | --- |
| `POST` | `/messages` | `AddMessagesRequest` | `Result` with `202 Accepted` | Queues one async job per message. |
| `POST` | `/entity-node` | `AddEntityNodeRequest` | saved entity node | Direct node creation, no LLM extraction. |
| `DELETE` | `/entity-edge/{uuid}` | path UUID | `Result` | Deletes one fact edge. |
| `DELETE` | `/group/{group_id}` | path group | `Result` | Deletes data in one group. |
| `DELETE` | `/episode/{uuid}` | path UUID | `Result` | Deletes one episodic node and related data. |
| `POST` | `/clear` | none | `Result` | Clears the graph and rebuilds indices. Destructive. |

### `AddMessagesRequest`

```json
{
  "group_id": "customer-123",
  "messages": [
    {
      "content": "Alice works at Acme Corporation.",
      "uuid": "optional-message-id",
      "name": "optional episode name",
      "role_type": "user",
      "role": "Alice",
      "timestamp": "2026-01-15T12:00:00Z",
      "source_description": "support transcript"
    }
  ]
}
```

`role_type` must be one of `user`, `assistant`, or `system`. The service formats
episodes as `role(role_type): content` before calling Graphiti.

### `AddEntityNodeRequest`

```json
{
  "uuid": "entity-id",
  "group_id": "customer-123",
  "name": "Alice",
  "summary": "Alice is an engineer at Acme."
}
```

## Retrieval routes

| Method | Path | Request | Response | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/healthcheck` | none | `{"status":"healthy"}` | Service startup/lifespan check. |
| `POST` | `/search` | `SearchQuery` | `SearchResults` | Fact search over edges. |
| `GET` | `/entity-edge/{uuid}` | path UUID | `FactResult` | Retrieve one fact edge. |
| `GET` | `/episodes/{group_id}?last_n=N` | path + query | list of episodes | Poll this after `/messages`. |
| `POST` | `/get-memory` | `GetMemoryRequest` | `GetMemoryResponse` | Builds a query from messages then searches. |

### `SearchQuery`

```json
{
  "group_ids": ["customer-123"],
  "query": "Who works at Acme?",
  "max_facts": 10
}
```

Returns:

```json
{
  "facts": [
    {
      "uuid": "edge-id",
      "name": "WORKS_FOR",
      "fact": "Alice works at Acme Corporation.",
      "valid_at": "2026-01-15T12:00:00Z",
      "invalid_at": null,
      "created_at": "2026-01-15T12:01:00Z",
      "expired_at": null
    }
  ]
}
```

### `GetMemoryRequest`

```json
{
  "group_id": "customer-123",
  "max_facts": 10,
  "center_node_uuid": null,
  "messages": [
    {
      "content": "Does Alice still work for Acme?",
      "role_type": "user",
      "role": "Alice"
    }
  ]
}
```

The service builds one string query from the messages and calls Graphiti search
against the requested group.

## Queue semantics

The ingest router owns an `AsyncWorker` with an in-process queue. `/messages` puts
jobs on the queue and returns immediately. This means:

- A `202 Accepted` response confirms queueing, not completed extraction.
- Search may be empty until the background job has run.
- Poll `/episodes/{group_id}` before asserting that ingest produced graph data.
- Long LLM provider latency shows up as delayed episode visibility.

## Safety notes

- `POST /clear` clears the entire graph used by the service instance.
- `DELETE /group/{group_id}` is the safer cleanup path for smoke tests because it
  scopes deletion to the generated group.
- Use unique group IDs for automated smoke tests.
