# API route map

Honcho's public HTTP surface is organized under `/v3`.

## Top-level routes

- `GET /health` — liveness.
- `GET /metrics` — Prometheus metrics when enabled.
- `POST /v3/keys` — create scoped JWTs.

## Workspace routes

Workspace routes manage tenancy and the top-level container for peers,
sessions, conclusions, search, webhooks, and queue inspection.

- `POST /v3/workspaces`
- `POST /v3/workspaces/list`
- `GET /v3/workspaces/{workspace_id}`
- `PUT /v3/workspaces/{workspace_id}`
- `DELETE /v3/workspaces/{workspace_id}`
- `POST /v3/workspaces/{workspace_id}/search`
- `GET /v3/workspaces/{workspace_id}/queue/status`
- `POST /v3/workspaces/{workspace_id}/schedule_dream`

## Peer routes

Peers are the memory subjects. Common peer surfaces are:

- `POST /v3/workspaces/{workspace_id}/peers`
- `POST /v3/workspaces/{workspace_id}/peers/list`
- `PUT /v3/workspaces/{workspace_id}/peers/{peer_id}`
- `GET /v3/workspaces/{workspace_id}/peers/{peer_id}/card`
- `PUT /v3/workspaces/{workspace_id}/peers/{peer_id}/card`
- `POST /v3/workspaces/{workspace_id}/peers/{peer_id}/chat`
- `GET /v3/workspaces/{workspace_id}/peers/{peer_id}/context`
- `POST /v3/workspaces/{workspace_id}/peers/{peer_id}/representation`
- `POST /v3/workspaces/{workspace_id}/peers/{peer_id}/search`
- `POST /v3/workspaces/{workspace_id}/peers/{peer_id}/sessions`

## Scope routes

Scope routes group sessions under an additional organizational layer.
They are useful when a deployment wants a structured container above the
individual session.

- `POST /v3/workspaces/{workspace_id}/scopes`
- `POST /v3/workspaces/{workspace_id}/scopes/list`
- `GET /v3/workspaces/{workspace_id}/scopes/{scope_id}`
- `GET /v3/workspaces/{workspace_id}/scopes/{scope_id}/status`
- `POST /v3/workspaces/{workspace_id}/scopes/{scope_id}/sessions`
- `POST /v3/workspaces/{workspace_id}/scopes/{scope_id}/sessions/list`

## Session routes

Sessions hold messages, summaries, and scoped conversation context.

- `POST /v3/workspaces/{workspace_id}/sessions`
- `POST /v3/workspaces/{workspace_id}/sessions/list`
- `GET /v3/workspaces/{workspace_id}/sessions/{session_id}/context`
- `GET /v3/workspaces/{workspace_id}/sessions/{session_id}/summaries`
- `POST /v3/workspaces/{workspace_id}/sessions/{session_id}/messages`
- `POST /v3/workspaces/{workspace_id}/sessions/{session_id}/messages/list`
- `POST /v3/workspaces/{workspace_id}/sessions/{session_id}/messages/upload`
- `GET /v3/workspaces/{workspace_id}/sessions/{session_id}/messages/{message_id}`
- `PUT /v3/workspaces/{workspace_id}/sessions/{session_id}/messages/{message_id}`
- `DELETE /v3/workspaces/{workspace_id}/sessions/{session_id}`
- `POST /v3/workspaces/{workspace_id}/sessions/{session_id}/clone`
- `GET|PUT|POST|DELETE /v3/workspaces/{workspace_id}/sessions/{session_id}/peers`
- `GET|PUT /v3/workspaces/{workspace_id}/sessions/{session_id}/peers/{peer_id}/config`
- `POST /v3/workspaces/{workspace_id}/sessions/{session_id}/search`

## Message and conclusion routes

- `POST /v3/workspaces/{workspace_id}/conclusions`
- `POST /v3/workspaces/{workspace_id}/conclusions/list`
- `POST /v3/workspaces/{workspace_id}/conclusions/query`
- `DELETE /v3/workspaces/{workspace_id}/conclusions/{conclusion_id}`

Messages also appear through the session-scoped message routes above.

## Webhook routes

- `GET|POST /v3/workspaces/{workspace_id}/webhooks`
- `GET /v3/workspaces/{workspace_id}/webhooks/test`
- `DELETE /v3/workspaces/{workspace_id}/webhooks/{endpoint_id}`

## How to use the map

- Start with workspace routes when you need a tenant boundary.
- Use peer routes when the task is about memory or dialectic answers.
- Use session routes when the task is about conversation history.
- Use conclusion routes when the task is about derived observations.
- Use webhook routes when the task is about outbound notifications.

If a user asks for the exact request body or response schema, move to the
integrations sub-skill and the SDK/API reference there.
