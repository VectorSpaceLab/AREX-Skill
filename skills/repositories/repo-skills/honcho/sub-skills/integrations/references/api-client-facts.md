# API and Client Facts for Honcho Integrations

## Purpose

Read this when you need exact object names, method names, REST route shapes, body
fields, and behavioral constraints for integrating Honcho memory without opening
the original repository.

## Core object model

- **Workspace**: the top-level namespace. SDK clients create or ensure the
  workspace before workspace-scoped operations.
- **Peer**: any participant: human, assistant, agent, bot, external identity, or
  imported-data actor.
- **Session**: a coherent context bucket: chat thread, project, channel,
  meeting, email thread, ingestion batch, or agent run.
- **Message**: raw content attributed to one peer within one session. Message
  creation enqueues background representation and summary work.
- **Conclusion**: a fact or observation about an observed peer from an observer
  peer's perspective. Conclusions power representations and peer cards.
- **Representation**: formatted text synthesized from conclusions. It may be
  global, session-scoped, target-scoped, search-curated, or scope-curated.
- **Dialectic chat**: a live reasoning endpoint that answers natural-language
  questions about a peer using messages and conclusions.

## Environment and install knobs

Python package: `honcho-ai`.

```bash
uv add honcho-ai
# or: pip install honcho-ai
```

TypeScript package: `@honcho-ai/sdk`.

```bash
npm install @honcho-ai/sdk
# or: bun add @honcho-ai/sdk
```

Common configuration:

| Setting | Python | TypeScript | Notes |
| --- | --- | --- | --- |
| API key | `api_key=` or `HONCHO_API_KEY` | `apiKey` or `HONCHO_API_KEY` | Managed API keys are bearer tokens. |
| Base URL | `base_url=` or `HONCHO_URL`; `environment="local"` maps local server | `baseURL` or `HONCHO_URL`; `environment: "local"` maps local server | Production default is the managed Honcho API. |
| Workspace | `workspace_id=` or `HONCHO_WORKSPACE_ID` | `workspaceId` or `HONCHO_WORKSPACE_ID` | Defaults to `default` when omitted. |
| Timeout/retries | `timeout=`, `max_retries=` | `timeout`, `maxRetries` | Use for production agents with strict latency budgets. |

## Python SDK surface

The Python SDK is sync-first. Async access is available through `.aio` on the
client, peer, session, and conclusion scope.

```python
from honcho import Honcho
from honcho.api_types import PeerConfig, SessionPeerConfig

honcho = Honcho(workspace_id="my-app", api_key=os.environ["HONCHO_API_KEY"])
user = honcho.peer("user-123", metadata={"plan": "pro"})
assistant = honcho.peer("assistant", configuration=PeerConfig(observe_me=False))
session = honcho.session("thread-123")
session.add_peers([
    (user, SessionPeerConfig(observe_me=True, observe_others=True)),
    (assistant, SessionPeerConfig(observe_me=False, observe_others=True)),
])
session.add_messages([
    user.message("I prefer direct summaries.", metadata={"channel": "web"}),
    assistant.message("I'll be concise."),
])
```

Client methods:

- `peer(id, metadata=None, configuration=None)` -> get/create `Peer`.
- `peers(filters=None, page=1, size=50, reverse=False)` -> paginated peers.
- `session(id, metadata=None, configuration=None, peers=None)` -> get/create
  `Session`, optionally attaching peers.
- `sessions(...)`, `workspaces(...)`, `delete_workspace(workspace_id)`.
- `search(query, filters=None, limit=10)` -> workspace message search.
- `queue_status(observer=None, sender=None, session=None)`.
- `schedule_dream(observer, session=None, observed=None)`.

Peer methods:

- `message(content, metadata=None, configuration=None, created_at=None)` builds
  a message object but does not send it.
- `chat(query, target=None, session=None, reasoning_level=None,
  response_format=None)` calls the Dialectic endpoint; `response_format` may be
  a Pydantic model class or a JSON Schema dict.
- `chat_stream(...)` streams Dialectic text chunks.
- `sessions(...)`, `search(query, filters=None, limit=10)`.
- `get_card(target=None)`, `set_card(peer_card, target=None)`.
- `representation(session=None, target=None, search_query=None,
  search_top_k=None, search_max_distance=None, include_most_frequent=None,
  max_conclusions=None)`.
- `context(target=None, search_query=None, ...)` returns representation plus
  peer card from the observer's perspective.
- `conclusions` for self-conclusions; `conclusions_of(target)` for local
  observer/observed conclusion scopes.

Session methods:

- `add_peers`, `set_peers`, `remove_peers`, `peers`.
- `get_peer_configuration(peer)`, `set_peer_configuration(peer, config)`.
- `add_messages(message_or_list)`, `messages(filters=None, page=1, size=50,
  reverse=False)`, `get_message(message_id)`, `update_message(message, metadata)`.
- `context(summary=True, tokens=None, peer_target=None, search_query=None,
  peer_perspective=None, limit_to_session=False, ...)`.
- `summaries()`, `search(query, filters=None, limit=10)`, `upload_file(...)`.
- `representation(peer, target=None, search_query=None, ...)`.
- `queue_status(observer=None, sender=None)`, `clone(message_id=None)`, `delete()`.

Conclusion-scope methods:

- `list(page=1, size=50, session=None, filters=None, reverse=False)`.
- `query(query, top_k=10, distance=None, filters=None)`.
- `create([{ "content": ..., "session_id": ... }, ...])`.
- `delete(conclusion_id)`.
- `representation(search_query=None, ...)`.

Reserved filters in SDK conclusion scopes are rejected: do not pass
`observer`, `observed`, `observer_id`, or `observed_id` in `filters`; choose the
scope through `peer.conclusions` or `peer.conclusions_of(target)` instead.

## TypeScript SDK surface

The TypeScript SDK is promise-first.

```typescript
import { Honcho } from "@honcho-ai/sdk";

const honcho = new Honcho({ workspaceId: "my-app", apiKey: process.env.HONCHO_API_KEY });
const user = await honcho.peer("user-123", { metadata: { plan: "pro" } });
const assistant = await honcho.peer("assistant", { configuration: { observeMe: false } });
const session = await honcho.session("thread-123");
await session.addPeers([
  [user, { observeMe: true, observeOthers: true }],
  [assistant, { observeMe: false, observeOthers: true }],
]);
await session.addMessages([
  user.message("I prefer direct summaries.", { metadata: { channel: "web" } }),
  assistant.message("I'll be concise."),
]);
```

Client methods:

- `peer(id, { metadata, configuration }?)`, `peers({ filters, page, size,
  reverse }?)`.
- `session(id, { metadata, configuration, peers }?)`, `sessions(...)`.
- `getMetadata`, `setMetadata`, `getConfiguration`, `setConfiguration`,
  `refresh`, `workspaces`, `deleteWorkspace`.
- `search(query, { filters, limit }?)`, `queueStatus(...)`, `scheduleDream(...)`.

Peer methods:

- `message(content, { metadata, configuration, createdAt }?)` creates a message
  input but does not send it.
- `chat(query, { target, session, reasoningLevel, responseFormat }?)` returns a
  string, parsed Zod result, JSON string, or `null`.
- `chatStream(...)` returns an async iterable stream.
- `sessions`, `search`, `getCard`, `setCard`, `representation`, `context`.
- `conclusions` and `conclusionsOf(target)` return `ConclusionScope` objects.

Session methods:

- `addPeers`, `setPeers`, `removePeers`, `peers`.
- `getPeerConfiguration`, `setPeerConfiguration`.
- `addMessages`, `messages`, `getMessage`, `updateMessage`.
- `context({ summary, tokens, peerTarget, peerPerspective, limitToSession,
  representationOptions }?)` returns `SessionContext`.
- `summaries`, `search`, `queueStatus`, `uploadFile`, `representation`, `clone`,
  `delete`.

Conclusion-scope methods:

- `list({ page, size, session, filters, reverse }?)`.
- `query(query, topK=10, distance?, filters?)`.
- `create(conclusionOrList)`, `delete(conclusionId)`, `representation(options?)`.

## REST route map

All public v3 API routes are under:

```text
/v3/workspaces/{workspace_id}/...
```

Core workspace, peer, session, and message routes:

| Task | Method and path | Important body/query fields |
| --- | --- | --- |
| Get/create peer | `POST /peers` | `{ "id": "peer-id", "metadata": {...}, "configuration": {"observe_me": false} }` |
| List peers | `POST /peers/list` | `{ "filters": {...} }`, query `page`, `size`, `reverse` |
| Update peer | `PUT /peers/{peer_id}` | `metadata`, `configuration` replace provided fields |
| Get/create session | `POST /sessions` | `{ "id": "session-id", "peers": {"peer": {"observe_me": true, "observe_others": true}}, "metadata": {...}, "configuration": {...}, "scopes": [...] }` |
| List sessions | `POST /sessions/list` | optional `filters`, pagination query |
| Update session | `PUT /sessions/{session_id}` | `metadata`, `configuration` |
| Delete session | `DELETE /sessions/{session_id}` | marks inactive and enqueues deletion |
| Clone session | `POST /sessions/{session_id}/clone` | query `message_id` optional cutoff |
| Add/set/remove session peers | `POST` / `PUT` / `DELETE /sessions/{session_id}/peers` | peer map for add/set, peer-id list for remove |
| Get/set peer config in session | `GET` / `PUT /sessions/{session_id}/peers/{peer_id}/config` | `observe_me`, `observe_others` |
| List session peers | `GET /sessions/{session_id}/peers` | paginated response |
| Create messages | `POST /sessions/{session_id}/messages` | `{ "messages": [{"peer_id", "content", "metadata", "configuration", "created_at"}] }`, 1-100 messages |
| Upload file as messages | `POST /sessions/{session_id}/messages/upload` | multipart `file`, `peer_id`, optional JSON `metadata`, `configuration`, `created_at` |
| List messages | `POST /sessions/{session_id}/messages/list` | optional `filters`, pagination query |
| Get/update message | `GET` / `PUT /sessions/{session_id}/messages/{message_id}` | update supports `metadata` |
| Workspace message search | `POST /search` | `{ "query", "filters", "limit" }` |
| Peer message search | `POST /peers/{peer_id}/search` | adds workspace and peer filters |
| Session message search | `POST /sessions/{session_id}/search` | adds workspace and session filters |

Memory-read routes:

| Task | Method and path | Important fields |
| --- | --- | --- |
| Dialectic chat | `POST /peers/{peer_id}/chat` | body `query`, optional `target`, `session_id`, `stream`, `reasoning_level`, `response_format`, `filters`, `scope` |
| Peer representation | `POST /peers/{peer_id}/representation` | body `target`, `session_id`, `search_query`, `search_top_k`, `search_max_distance`, `include_most_frequent`, `max_conclusions`, `filters`, `scope` |
| Peer card | `GET` / `PUT /peers/{peer_id}/card` | query `target`; `PUT` body `peer_card` |
| Peer context | `GET /peers/{peer_id}/context` | query `target`, `search_query`, `search_top_k`, `search_max_distance`, `include_most_frequent`, `max_conclusions` |
| Session context | `GET /sessions/{session_id}/context` | query `tokens`, `summary`, `peer_target`, `peer_perspective`, `scope`, `limit_to_session`, representation search options |
| Session summaries | `GET /sessions/{session_id}/summaries` | returns short and long summaries when available |
| Queue status | `GET /queue/status` | query `observer_id`, `sender_id`, `session_id` optional |
| Schedule dream | `POST /schedule_dream` | body `observer`, optional `observed`, `session_id`, server uses dream type `omni` |

Conclusion routes:

| Task | Method and path | Important fields |
| --- | --- | --- |
| Create conclusions | `POST /conclusions` | `{ "conclusions": [{"content", "observer_id", "observed_id", "session_id"}] }`, 1-100 conclusions |
| List conclusions | `POST /conclusions/list` | optional `filters`, pagination query |
| Query conclusions | `POST /conclusions/query` | `query`, `top_k`, `distance`, `filters` with `observer`/`observer_id` and `observed`/`observed_id` required |
| Delete conclusion | `DELETE /conclusions/{conclusion_id}` | destructive |

Webhook routes are covered in `webhooks.md`.

## Dialectic chat details

`peer.chat(...)` and `POST /peers/{peer_id}/chat` take a required natural
language `query`. The effective observer is the path peer unless a supported
scope option changes it. The observed peer is `target` if supplied; otherwise it
is the path peer.

Reasoning levels are `minimal`, `low`, `medium`, `high`, and `max`; `low` is
the default balance. Use `minimal` for fast factual lookup, and reserve `high`
or `max` for expensive synthesis.

`response_format` can be a conservative JSON Schema object. SDKs can accept a
Pydantic model class (Python) or Zod schema (TypeScript) and convert it to JSON
Schema. The server returns `content` as a JSON string when a schema is used.

Streaming chat returns server-sent event chunks. SDK streaming helpers expose an
iterable of text deltas.

## Context and representation details

- `session.context()` without `peer_target` returns session history and
  summaries only; it does not include cross-session memory.
- `peer_target` adds the target peer's representation and peer card.
- `peer_perspective` requires `peer_target`; it means "what this perspective
  peer knows about the target".
- `limit_to_session=True` restricts representation conclusions to the session.
- `search_query` curates representation contents using semantic search.
- Search options include `search_top_k`, `search_max_distance`,
  `include_most_frequent`, and `max_conclusions`.

## Auth and scope notes

- Workspace/admin keys can manage workspace-level resources such as webhooks.
- Peer-scoped keys can read only permitted peer/session resources. Session
  member-read access is read-only and does not grant access to a co-member's
  representation or card.
- Scope peers are a special observer mechanism. They cannot be the observed
  target of chat, representation, or context. Use the documented `scope` option
  on read routes instead of treating scope names as ordinary peers.

## Background work and freshness

Message creation returns before background reasoning finishes. The API enqueues
representation and summary tasks; embeddings may be scheduled immediately when
enabled, with a reconciler as fallback. Use queue status or webhooks when an
application needs a readiness hint, but design normal user responses to proceed
without waiting.
