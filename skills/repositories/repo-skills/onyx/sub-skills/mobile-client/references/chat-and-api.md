# Mobile Chat and API

Use this reference when you touch chat, file, or API layers. The mobile chat data layer is native and should stay in mobile.

## HTTP boundary

- Use `apiFetch<T>` for JSON calls. It injects the bearer token unless `auth: false` is set, normalizes backend errors into `ApiError`, and JSON-serializes plain object bodies.
- `getBaseUrl()` already appends the `/api` prefix. Pass bare paths such as `/chat/...`, `/me`, or `/user/projects/...`.
- Do not call the backend host directly from mobile code when a client helper exists.
- Use `apiFetch` for ordinary JSON reads and writes. Use the streaming transport only when the response body must be read incrementally.

## Streaming chat flow

- The streaming chat endpoints use `expo/fetch`, not the normal fetch helper, because React Native needs a readable `response.body`.
- The transport turns decoded text into NDJSON packets, then hands those packets to the chat store and renderer layer.
- Heartbeats are treated as transport noise on the send path and are ignored by the visible stream. Resume-style reads keep heartbeats so the client can keep re-checking liveness while the backend is quiet.
- Stream errors, message-id info, and wrapped packets are discriminated by shape, not by assumptions about `type` alone.
- AbortControllers own cancellation. Stop the turn by aborting the live controller and then letting the stream cleanup settle the UI state.

## Mobile-native chat data layer

- The chat pure layer is written natively in the mobile app. Do not depend on web chat logic or shared chat code for these behaviors.
- The core pure pieces are the NDJSON buffer, the message tree, the history rehydrator, packet and message contracts, and file-descriptor helpers.
- The synthetic root message uses the negative `-3` id. That root is not part of the visible conversation.
- `buildEmptyMessage` and `buildImmediateMessages` create optimistic nodes before the backend assigns real message IDs.
- `getLatestMessageChain` follows the latest child branch, `getLastSuccessfulMessageId` finds the send parent for the next turn, and `processRawChatHistory` rebuilds a session from backend messages plus packet arrays.
- Rehydrated turns are structural only. If a turn has already streamed, history should rebuild the tree rather than inventing a new conversation shape.

## Typical session flow

1. Create a session if there is no active session yet.
2. Seed optimistic user and assistant nodes in the ephemeral store.
3. Send the message over the streaming transport.
4. Parse NDJSON into packets and batch-flush them into the assistant node.
5. On stop, abort the reader and settle the chat state.
6. On cold open, hydrate from the session snapshot and resume a live run only if the backend says one is still in flight.

## Uploads, files, and attachments

- File upload state is split between a reusable store for file records and a surface-specific membership layer.
- Draft attachments and project files should both resolve through the same file-record store so optimistic records and committed records stay in sync.
- Recent-file, project-file, and attachment flows all rely on the same live file records and the same upload reconciliation rules.
- Upload progress is ephemeral. Keep task state, temporary IDs, and cancellation handles out of persisted query state.
- If a file is still uploading or indexing, treat it as blocking for send until it is ready or removed.
- Convert committed files into message file descriptors before sending, and convert sent descriptors back into display records when you need to render chips or file pills.
- When a project or recent-file read is used as a picker source, keep its query key serverUrl-scoped and out of MMKV persistence if it contains file names or other user content.

## Query keys and cache rules

- Every query key must include `serverUrl`.
- Sensitive or workspace-scoped reads should be excluded from MMKV persistence before they can dehydrate.
- Treat chat sessions, individual chat snapshots, workspace settings, projects, recent files, and agent preferences as cache entries that should refetch after instance or account changes.
- If you add a new sensitive read, update the non-persisted key list before you rely on it in UI state.

## Practical rules to remember

- Use the mobile query client for JSON reads and writes, and the streaming transport only for the readable-body chat path.
- Keep chat state ephemeral and file state reconciled.
- Keep the mobile chat logic mobile-owned unless the surrounding construction policy changes.
