# Backend API and shared protocol reference

This reference distills the backend REST route map, shared protocol schemas, task lifecycle, Python API client behavior, and API error handling. It is self-contained; do not reopen repository source files to answer ordinary backend/API questions.

## Service shape and authentication

- FastAPI app title comes from `Settings.PROJECT_NAME` and the API router is mounted under `Settings.API_V1_STR`, default `/api/v1`.
- OpenAPI JSON is exposed at `/api/v1/openapi.json` when the server is running.
- API-key auth accepts either `X-API-Key` header or `api_key` query parameter.
- Frontend user identity accepts either `x-oasst-user` header or `oasst_user` query parameter in the form `auth_method:username`.
- Trusted API clients are required for sensitive read/write endpoints such as tree-state changes, user updates/deletes, stats internals, and most admin routes.
- Root-token admin bootstrap uses an HTTP bearer token whose value is in `Settings.ROOT_TOKENS`; this is separate from `X-API-Key`.
- Browser auth check uses the configured NextAuth cookie name, derives a key with HKDF, decrypts JWE payload, and returns the email from token data.

## FastAPI route map

All paths below are under the `/api/v1` prefix.

### Tasks: `/tasks`

| Method/path | Handler purpose | Request/response model | Notes |
| --- | --- | --- | --- |
| `POST /tasks/` | Request the next task | request `TaskRequest`; response `AnyTask` | Applies API-client and user/task-type rate limits when `RATE_LIMIT=True`; calls task selection with requested type/lang/collective. |
| `POST /tasks/availability` | Query task counts by type | optional `User`, `lang`; response `dict[TaskRequestType, int]` | Uses TreeManager availability logic. |
| `POST /tasks/{task_id}/ack` | Acknowledge that a frontend accepted a task | `TaskAck(message_id)`; 204 | Binds the frontend message id to a task. Idempotent only for the same already-bound frontend id. |
| `POST /tasks/{task_id}/nack` | Report inability to do a task | `TaskNAck(reason)`; 204 | Skips non-collective tasks and may add a skip emoji for reply/ranking/labeling tasks. |
| `POST /tasks/interaction` | Submit a completed task interaction | `AnyInteraction`; response `TaskDone` | Handles text replies, ratings, rankings, and labels; task must match the user and lifecycle constraints. |
| `POST /tasks/close` | Close a collective task | `TaskClose(message_id)`; response `TaskDone` | Uses frontend message id and rejects non-collective tasks unless lower-level code explicitly allows personal tasks. |

### Messages: `/messages`

| Method/path | Purpose | Important inputs |
| --- | --- | --- |
| `GET /messages/` | Query messages ordered by created date | auth/username/api-client filters, `max_count` 1..1000, date range, roots-only, deletion/lang flags. |
| `GET /messages/cursor` | Cursor-paginated message query | `before`/`after` cursor as ISO datetime or `uuid$iso_datetime`, sort direction, search query, include-user. |
| `GET /messages/{message_id}` | Fetch by internal UUID | Returns `Message`. |
| `GET /messages/{message_id}/conversation` | Conversation from root to message | Returns `Conversation`. |
| `GET /messages/{message_id}/tree` | Entire containing tree | `include_spam`, `include_deleted`; returns `MessageTree`. |
| `GET /messages/{message_id}/tree/state` | TreeManager state for containing tree | Returns state, active flag, limits, origin. |
| `PUT /messages/{message_id}/tree/state?halt=...` | Halt/unhalt tree | Trusted API client required. |
| `GET /messages/{message_id}/children` | Immediate children | Returns list of `Message`. |
| `GET /messages/{message_id}/descendants` | Subtree rooted at message | Returns `MessageTree`. |
| `GET /messages/{message_id}/longest_conversation_in_tree` | Longest conversation branch | Returns `Conversation`. |
| `GET /messages/{message_id}/max_children_in_tree` | Node with most children plus children | Returns `MessageTree`. |
| `DELETE /messages/{message_id}` | Mark message deleted | Trusted API client required; 204. |
| `PUT /messages/{message_id}/undelete` | Undo deletion | 202. |
| `POST /messages/{message_id}/edit` | Revise message content | Trusted API client; request `MessageEditRequest`. |
| `GET /messages/{message_id}/history` | Fetch revision history | Trusted API client; returns `MessageRevision` list. |
| `POST /messages/{message_id}/emoji` | Toggle/add/remove emoji | `MessageEmojiRequest`; 202. |

### Frontend-message id lookup: `/frontend_messages`

These mirror read-only message lookup routes but identify the message by frontend id instead of internal UUID:

- `GET /frontend_messages/{message_id}`
- `GET /frontend_messages/{message_id}/conversation`
- `GET /frontend_messages/{message_id}/tree?include_spam=...&include_deleted=...`
- `GET /frontend_messages/{message_id}/children`
- `GET /frontend_messages/{message_id}/descendants`
- `GET /frontend_messages/{message_id}/longest_conversation_in_tree`
- `GET /frontend_messages/{message_id}/max_children_in_tree`

### Frontend users: `/frontend_users`

| Method/path | Purpose |
| --- | --- |
| `GET /frontend_users/` | Deprecated username-ordered list with cursor-like bounds and search filters. |
| `GET /frontend_users/{auth_method}/{username}` | Resolve a frontend user for an auth method and username. |
| `POST /frontend_users/` | Create or update a frontend user from `CreateFrontendUserRequest`; toggles enabled, leaderboard, ToS, notes when changed. |
| `GET /frontend_users/{auth_method}/{username}/messages` | Query a frontend user's messages. |
| `GET /frontend_users/{auth_method}/{username}/messages/cursor` | Cursor-paginated frontend-user message query. |
| `DELETE /frontend_users/{auth_method}/{username}/messages` | Mark all messages by that frontend user/API client deleted; trusted API client required. |

### Users: `/users`

| Method/path | Purpose |
| --- | --- |
| `GET /users/by_username` | List frontend users ordered by username. |
| `GET /users/by_display_name` | List frontend users ordered by display name. |
| `GET /users/cursor` | Cursor page over users; `sort_key` is `username` or `display_name`. |
| `GET /users/{user_id}` | Fetch global user by UUID; trusted clients can resolve users beyond their own registrations. |
| `PUT /users/{user_id}` | Update display name, enabled flag, notes, leaderboard visibility, ToS; trusted client required. |
| `DELETE /users/{user_id}` | Anonymizing delete; trusted client required. |
| `GET /users/{user_id}/messages` | Query a user's messages. |
| `GET /users/{user_id}/messages/cursor` | Cursor-paginated user messages. |
| `DELETE /users/{user_id}/messages` | Mark all messages by global user deleted; trusted client required. |
| `GET /users/{user_id}/stats` | All timeframe user stats. |
| `GET /users/{user_id}/stats/{time_frame}` | User stats for one timeframe. |
| `GET /users/{user_id}/stats/{time_frame}/window` | Leaderboard window around a user. |

### Text labels: `/text_labels`

| Method/path | Purpose |
| --- | --- |
| `POST /text_labels/` | Store `TextLabels` for a piece of text/message; 204 on success. |
| `GET /text_labels/valid_labels?message_id=...` | Return valid label descriptions for an initial prompt, assistant reply, prompter reply, or all labels when no message id is supplied. |
| `GET /text_labels/report_labels` | Return the label set used for report flows. |

### Stats: `/stats`

| Method/path | Purpose |
| --- | --- |
| `GET /stats/` | System message stats; trusted client required. |
| `GET /stats/tree_manager/state_counts` | Tree counts by state; trusted client required. |
| `GET /stats/tree_manager/message_counts?only_active=...` | Tree message-count stats; trusted client required. |
| `GET /stats/tree_manager` | TreeManager aggregate stats; trusted client required. |
| `GET /stats/cached/{name}` | One cached stat by `CachedStatsName`. |
| `GET /stats/cached` | All cached stats. |
| `POST /stats/cached/update` | Refresh cached stats; trusted client required; 204. |

### Admin: `/admin`

| Method/path | Purpose | Safety |
| --- | --- | --- |
| `POST /admin/api_client` | Create API client; returns new key. | Requires root bearer token. |
| `GET /admin/backend_settings/full` | Return full Settings model. | Trusted client; may reveal secrets in a live system. |
| `GET /admin/backend_settings/public` | Return public settings subset. | API-key auth. |
| `POST /admin/purge_user/{user_id}` | Purge/ban user with preview mode by default. | Trusted client; preview rolls back. |
| `POST /admin/purge_user/{user_id}/messages` | Purge user's messages with filters and preview mode. | Trusted client; preview rolls back. |
| `GET /admin/flagged_messages/cursor` | Cursor page flagged messages. | Trusted client; cursor errors match message cursor behavior. |
| `GET /admin/flagged_messages` | List flagged messages. | Trusted client. |
| `POST /admin/flagged_messages/{message_id}/processed` | Mark flagged message processed. | Trusted client. |
| `POST /admin/merge_users` | Merge source users into destination. | Trusted client; DB-mutating. |

### Auth: `/auth`

- `GET /auth/check`: decrypts the configured auth cookie and returns the token email when decryption succeeds.

## Shared protocol schemas

### Task request types

`TaskRequestType` values:

```text
random, summarize_story, rate_summary, initial_prompt, prompter_reply, assistant_reply,
rank_initial_prompts, rank_prompter_replies, rank_assistant_replies,
label_initial_prompt, label_assistant_reply, label_prompter_reply
```

Common task request envelope:

```python
TaskRequest(type=TaskRequestType.random, user=None, collective=False, lang=None)
```

User identity model:

```python
User(id="frontend-user-id", display_name="Name", auth_method="discord|google|local|system")
```

Task model families returned by `POST /tasks/` include:

- `InitialPromptTask`: user writes an initial prompt; optional `hint`.
- `PrompterReplyTask`: user replies as prompter to a `Conversation`; optional `hint`.
- `AssistantReplyTask`: user replies as assistant to a `Conversation`.
- `RankInitialPromptsTask`: rank prompt candidates; prefer `prompt_messages` over deprecated `prompts`.
- `RankPrompterRepliesTask` and `RankAssistantRepliesTask`: rank reply candidates; prefer `reply_messages`; include `message_tree_id`, `ranking_parent_id`, and `reveal_synthetic`.
- `LabelInitialPromptTask`, `LabelPrompterReplyTask`, `LabelAssistantReplyTask`: label message/conversation with `valid_labels`, `mandatory_labels`, `mode`, and `disposition`.
- Legacy `SummarizeStoryTask` and `RateSummaryTask` exist in protocol models but are not core OA conversation collection paths.
- `TaskDone`: terminal response from interaction/close.

### Interaction models

`AnyInteraction` is one of:

| Model | `type` value | Required task-specific fields |
| --- | --- | --- |
| `TextReplyToMessage` | `text_reply_to_message` | `message_id` (frontend task message id), `user_message_id` (frontend id for user's new message), non-empty trimmed `text`, optional `lang`, `user`. |
| `MessageRating` | `message_rating` | `message_id`, positive integer `rating`, `user`. |
| `MessageRanking` | `message_ranking` | `message_id` of ranked parent, non-empty integer `ranking`, optional `not_rankable`, `user`. |
| `TextLabels` | `text_labels` | `text`, `labels` dict keyed by `TextLabel`, `message_id`, optional `task_id`, optional `is_report`, `user`. Label values must be between 0 and 1. |

`TextLabel` values are:

```text
spam, fails_task, lang_mismatch, pii, not_appropriate, hate_speech, sexual_content,
moral_judgement, political_content, quality, toxicity, humor, helpfulness, creativity, violence
```

## Task lifecycle patterns

### Normal text-reply flow

1. Client requests a task:
   ```python
   task = await client.fetch_task(TaskRequestType.assistant_reply, user=user, lang="en")
   ```
2. Frontend creates a local/frontend message id for the task and acknowledges it:
   ```python
   await client.ack_task(task.id, message_id="frontend-task-message-id")
   ```
3. User completes the task with an interaction referencing the acknowledged frontend task message id:
   ```python
   interaction = TextReplyToMessage(
       type="text_reply_to_message",
       message_id="frontend-task-message-id",
       user_message_id="frontend-user-message-id",
       text="The reply text",
       lang="en",
       user=user,
   )
   done = await client.post_interaction(interaction)
   ```
4. Backend stores the reply, updates message/tree state, optionally schedules embedding/toxicity Celery work depending on debug flags, and returns `TaskDone`.

### NACK/skip flow

Use `nack_task(task.id, reason="...")` when the frontend received a task but cannot present or complete it. NACK validates that the task exists, is not expired, and belongs to the user unless the task is collective.

### Collective close flow

Use `/tasks/close` with `TaskClose(message_id=<frontend message id>)` to mark a collective task done. Non-collective tasks are rejected by default.

### Lifecycle constraints that frequently matter

- Tasks expire after `Settings.TASK_VALIDITY_MINUTES`, default 2880 minutes (two days).
- ACK can only bind a task once; repeating the same ACK is idempotent, but changing the frontend message id after ACK raises `TASK_ALREADY_UPDATED`.
- Interaction requires an acknowledged, not-expired, not-done task and the same assigned user for personal tasks.
- `TextReplyToMessage.text` cannot be empty/whitespace and cannot exceed `Settings.MESSAGE_SIZE_LIMIT`, default 2000 characters.
- Duplicate recent replies and duplicate replies to the same parent are rejected unless debug duplicate flags are enabled.
- Cursor values are ISO datetimes or `uuid$iso_datetime`; malformed values raise `INVALID_CURSOR_VALUE`.

## Python API client

Constructor:

```python
OasstApiClient(backend_url: str, api_key: str, session: Optional[aiohttp.ClientSession] = None)
```

- If no session is supplied, the client opens an `aiohttp.ClientSession`; call `await client.close()` when done.
- All POST requests send JSON with header `x-api-key: <api_key>`.
- Non-2xx responses are parsed as `OasstErrorResponse(error_code, message)` when possible, then raised as `OasstError`. If parsing fails, a generic `OasstError` is raised with the raw response/status.
- HTTP 204 returns `None`; other successful POST responses are JSON-decoded.

Client methods:

| Method | Behavior |
| --- | --- |
| `fetch_task(task_type, user=None, collective=False, lang=None)` | POSTs `TaskRequest` to `/api/v1/tasks/`, parses response by task `type`, returns a protocol task model. |
| `fetch_random_task(user=None, collective=False, lang=None)` | Convenience wrapper for `TaskRequestType.random`. |
| `ack_task(task_id, message_id)` | POSTs `TaskAck` to `/api/v1/tasks/{task_id}/ack`; expects 204. |
| `nack_task(task_id, reason)` | POSTs `TaskNAck` to `/api/v1/tasks/{task_id}/nack`; expects 204. |
| `post_interaction(interaction)` | POSTs any interaction model to `/api/v1/tasks/interaction`; parses returned task, usually `TaskDone`. |
| `close()` | Closes the underlying aiohttp session. |

Minimal fake-HTTP testing pattern:

```python
from unittest import mock
from oasst_shared.api_client import OasstApiClient
from oasst_shared.schemas import protocol

class FakeSession:
    async def post(self, url, json, headers):
        return mock.AsyncMock(status=204, text=mock.AsyncMock(return_value=""))

client = OasstApiClient("http://backend", "key", session=FakeSession())
await client.ack_task("00000000-0000-0000-0000-000000000000", "frontend-id")
```

## Error model quick map

`OasstError` carries `message`, integer `error_code`, and `http_status_code`. Common codes for backend/API work:

| Error code name | Typical trigger |
| --- | --- |
| `API_CLIENT_NOT_AUTHORIZED` | Missing/invalid `X-API-Key` or untrusted client where trusted client is required. |
| `ROOT_TOKEN_NOT_AUTHORIZED` | Missing/invalid bearer root token for admin API-client creation. |
| `TOO_MANY_REQUESTS` | Redis-backed FastAPI limiter rejects a request. |
| `INVALID_CURSOR_VALUE` | Cursor is neither ISO datetime nor `uuid$iso_datetime`. |
| `TASK_ACK_FAILED`, `TASK_NACK_FAILED`, `TASK_INTERACTION_REQUEST_FAILED`, `TASK_GENERATION_FAILED` | Handler-level task endpoint failure wrappers. |
| `TASK_MESSAGE_TOO_LONG`, `TASK_MESSAGE_TEXT_EMPTY`, `TASK_MESSAGE_DUPLICATED`, `TASK_MESSAGE_DUPLICATE_REPLY` | Text reply validation failure. |
| `TASK_TOO_MANY_PENDING` | User has too many pending tasks in the configured recent time span. |
| `TASK_NOT_FOUND`, `TASK_EXPIRED`, `TASK_NOT_ACK`, `TASK_ALREADY_UPDATED`, `TASK_ALREADY_DONE`, `TASK_NOT_ASSIGNED_TO_USER` | Task lifecycle mismatch. |
| `MESSAGE_NOT_FOUND`, `NO_MESSAGE_TREE_FOUND`, `BROKEN_CONVERSATION`, `TREE_IN_ABORTED_STATE` | Message/tree lookup or state failure. |
| `TEXT_LABELS_INVALID_LABEL`, `TEXT_LABELS_MANDATORY_LABEL_MISSING`, `TEXT_LABELS_NO_SELF_LABELING` | Label submission validation failure. |
| `USER_DISABLED`, `USER_NOT_FOUND`, `USER_HAS_NOT_ACCEPTED_TOS` | User repository checks. |
| `CACHED_STATS_NOT_AVAILABLE` | Cached stats not yet populated for a requested name. |
