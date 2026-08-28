# Streaming, Events, Reconnect, and MCP

## User event stream

```text
GET /api/events
Accept: text/event-stream
Authorization: Bearer <token>
Last-Event-ID: <redis-stream-id>
```

Events include ingestion progress, tool approval, MCP OAuth completion and `backlog.truncated`. Redis Stream replay is bounded by per-user backlog, page size, connection cap and replay budget.

Client algorithm:

1. send last processed id;
2. parse complete SSE frames;
3. process one event idempotently;
4. persist cursor after processing;
5. reconnect with exponential backoff/jitter;
6. on `backlog.truncated`, clear cursor and refetch current state;
7. on `429`, honor backoff rather than opening more connections.

## Chat reconnect

```text
GET /api/messages/<message_id>/events
```

This replays/tails message events from the Postgres journal. It is native async and only exists on the full ASGI target. Retention is bounded by `MESSAGE_EVENTS_RETENTION_DAYS`.

A lightweight tail route may expose the current message tail, but the async event route is the continuity mechanism for a live interrupted answer.

## Proxy requirements

- disable response buffering for SSE;
- keep HTTP connection and upstream read timeout above expected idle periods;
- pass `Last-Event-ID` and authorization headers;
- do not apply transformations that coalesce/delay frames;
- set keepalive below proxy idle timeout;
- capacity-plan per-user and global connections.

## MCP route

`/mcp` is mounted on the ASGI shell. A Flask-only process returns 404. Validate:

1. web process serves `application.asgi:asgi_app`;
2. proxy forwards `/mcp` without stripping transport headers;
3. auth/OAuth redirect uses the public backend URL;
4. server/client timeouts cover intended tools;
5. MCP tools are separately configured and approved.

Do not confuse the `/mcp` server route (other MCP clients call DocsGPT) with the MCP tool integration (DocsGPT calls remote MCP servers).

## Event durability limits

User notifications use Redis stream retention; chat answer events use a Postgres message journal. These are different cursors and retention systems. A client must not reuse one cursor format for the other.
