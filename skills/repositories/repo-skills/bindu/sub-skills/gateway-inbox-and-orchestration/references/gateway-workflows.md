# Gateway Workflows

Gateway exposes a task-first planner service that takes a user question and a caller-supplied catalog of Bindu A2A peers, then streams Server-Sent Events.

## Endpoints

| Route | Auth | Purpose |
|---|---|---|
| `POST /plan` | Bearer by default | Plan, call peers, stream progress/results. |
| `GET /health` | none | Liveness and config probe. |
| `GET /.well-known/did.json` | none when identity configured | Gateway DID document. |

Default port: `3774` unless configured.

## Minimal request

```json
{
  "question": "Ask the research peer for a short summary.",
  "agents": [
    {
      "name": "research",
      "endpoint": "http://127.0.0.1:3773",
      "auth": {"type": "none"},
      "skills": [{"id": "summarize", "description": "Summarize text", "outputModes": ["text/plain"]}]
    }
  ],
  "preferences": {"timeout_ms": 60000, "max_steps": 5}
}
```

Send `Authorization: Bearer <gateway token>` when inbound auth is enabled.

## Stateless history

Gateway keeps state only for the lifetime of one `/plan` call. Persist relevant user/assistant turns and `compaction-summary` SSE frames in the caller, then send them back as `history` and `prior_summary`.

## Send-and-poll

For each peer tool call, Gateway sends A2A `message/send`, then polls `tasks/get` until terminal, deadline, abort, or configured poll exhaustion.
