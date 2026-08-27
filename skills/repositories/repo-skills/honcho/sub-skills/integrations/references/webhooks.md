# Webhook Integration

## Purpose

Read this when an integration needs push notifications after Honcho background
work drains. Webhooks are useful for refreshing UI state, scheduling a follow-up
read, or avoiding aggressive polling. They are not a reliable event log.

## Management routes

Webhook endpoints are registered per workspace. Every event for that workspace
is delivered to every registered endpoint.

| Task | Method and path | Notes |
| --- | --- | --- |
| Register or get existing endpoint | `POST /v3/workspaces/{workspace_id}/webhooks` | Body `{ "url": "https://example.com/honcho/webhook" }`; returns `201` for new endpoint or `200` for existing URL. |
| List endpoints | `GET /v3/workspaces/{workspace_id}/webhooks` | Paginated endpoint list. |
| Delete endpoint | `DELETE /v3/workspaces/{workspace_id}/webhooks/{endpoint_id}` | Returns `204`; destructive. |
| Emit test event | `GET /v3/workspaces/{workspace_id}/webhooks/test` | Sends `test.event` to all endpoints in the workspace. |

Webhook management requires an admin key or a workspace-scoped key for that
workspace. Peer-scoped and session-scoped keys should not manage webhooks.

## URL requirements

- URL must be absolute.
- Scheme must be `http` or `https`.
- IP-literal hosts in private, loopback, link-local, reserved, multicast, or
  unspecified ranges are rejected.
- Hostnames are accepted without DNS resolution. For self-hosted deployments,
  use network egress controls as the real internal-address defense.
- A workspace has a configured maximum endpoint count; exceeding it returns a
  conflict error.

## Event types

| Event | When it fires | Data fields |
| --- | --- | --- |
| `queue.empty` | A unit of queued background work finished draining | `workspace_id`, `queue_type` (`representation` or `summary`), optional `session_id`, optional `observer`, optional `observed` |
| `test.event` | The test route was called | `workspace_id` |

A `queue.empty` event is scoped to one task type for one session and
observer/observed pair. It is not proof that the whole workspace is idle.
A session that produces representation and summary work can emit separate events
for each task type.

## Payload shape

Every delivery is a `POST` with `Content-Type: application/json`.

```json
{
  "type": "queue.empty",
  "data": {
    "workspace_id": "my-app",
    "queue_type": "representation",
    "session_id": "support-chat-1",
    "observer": "assistant",
    "observed": "user-123"
  },
  "timestamp": "2026-08-10T18:24:05.123456Z"
}
```

`data` is event-specific. A test event has only workspace ID:

```json
{
  "type": "test.event",
  "data": { "workspace_id": "my-app" },
  "timestamp": "2026-08-10T18:24:05.123456Z"
}
```

Parse defensively:

- Branch on `type` as the discriminator.
- Treat every `data` key as optional unless your branch requires it.
- Tolerate new event types and new fields.
- Do not require `queue.empty` keys on `test.event`.

## Signature verification

Each delivery carries `X-Honcho-Signature`, the hex HMAC-SHA256 of the raw
request body using the deployment's webhook secret. Verify the bytes received,
not a parsed or re-serialized JSON object. Use constant-time comparison.

Python FastAPI example:

```python
import hashlib
import hmac
import json
import os
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()


def verify(raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        os.environ["WEBHOOK_SECRET"].encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/honcho/webhook")
async def handle_honcho_webhook(request: Request):
    raw = await request.body()
    signature = request.headers.get("X-Honcho-Signature", "")
    if not verify(raw, signature):
        raise HTTPException(status_code=401)
    event = json.loads(raw)
    if event.get("type") == "queue.empty":
        # Re-read state from Honcho; do not treat the event itself as state.
        pass
    return {"ok": True}
```

TypeScript Express example:

```typescript
import crypto from "node:crypto";
import express from "express";

const app = express();

function verify(rawBody: Buffer, signature: string): boolean {
  const expected = crypto
    .createHmac("sha256", process.env.WEBHOOK_SECRET!)
    .update(rawBody)
    .digest("hex");
  const a = Buffer.from(expected);
  const b = Buffer.from(signature);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

app.post("/honcho/webhook", express.raw({ type: "application/json" }), (req, res) => {
  const signature = req.header("X-Honcho-Signature") ?? "";
  if (!verify(req.body, signature)) return res.sendStatus(401);
  const event = JSON.parse(req.body.toString("utf8"));
  if (event.type === "queue.empty") {
    // Re-read representation, context, queue status, or messages from Honcho.
  }
  return res.sendStatus(200);
});
```

Do not use `express.json()` before signature verification; it consumes and
changes the body representation needed for HMAC verification.

## Delivery semantics

Webhook delivery is best-effort and fire-and-forget:

- Events fan out to all registered endpoints concurrently.
- Each delivery has a fixed timeout.
- Non-2xx responses, timeouts, and connection errors are logged and dropped.
- There are no retries.

Design receivers to be idempotent and to re-read Honcho state when notified. If
your product requires guaranteed completion detection, combine webhooks with
`queue_status` polling and a timeout/backoff policy.

## Self-hosting requirements

- A webhook secret must be configured; otherwise payload signing fails and
  deliveries are dropped even though registration can succeed.
- A deriver/background worker must be running because webhook delivery is
  background work.
- Configure the workspace endpoint limit according to expected fan-out.
- Keep the public webhook receiver reachable from the server or worker network.

## Receiver workflow

1. Register endpoint with a workspace/admin key.
2. Call the test route.
3. In the receiver, verify signature using raw bytes.
4. Branch on `event.type`.
5. For `queue.empty`, re-read the specific session, representation, context, or
   queue status that matters to the app.
6. Return a 2xx quickly. Do slow work in your own background queue.
7. Treat duplicate or out-of-order events as possible; keep receiver state
   idempotent.

## Common failure symptoms

See `troubleshooting.md` for detailed recovery, especially when:

- Endpoint registration succeeds but no deliveries arrive.
- Signature verification fails in Express or FastAPI.
- Test events work but `queue.empty` does not appear.
- Events arrive but representations still look stale.
