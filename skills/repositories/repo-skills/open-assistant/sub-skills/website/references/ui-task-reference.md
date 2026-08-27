# Website UI, task, API client, and chat reference

This reference is self-contained operating context for the Open-Assistant website layer. It summarizes route/component/API behavior so future agents can edit and debug the checkout without depending on original repository docs.

## Contribution route map

The contribution pages are thin Next pages that render a shared `TaskPage` with a `TaskType`. `TaskInfos` is the central UI map: each entry binds a category, stable UI id, route pathname, backend task type, optional label mode, and update type.

| User route | `TaskInfos` id | Category | Backend task type | Update type | UI component family |
|---|---|---|---|---|---|
| `/tasks/random` | `random` | Random | `random` | `random` | selected dynamically from returned task |
| `/create/initial_prompt` | `create_initial_prompt` | Create | `initial_prompt` | `text_reply_to_message` | `CreateTask` |
| `/create/user_reply` | `reply_as_user` | Create | `prompter_reply` | `text_reply_to_message` | `CreateTask` |
| `/create/assistant_reply` | `reply_as_assistant` | Create | `assistant_reply` | `text_reply_to_message` | `CreateTask` |
| `/evaluate/rank_user_replies` | `rank_user_replies` | Evaluate | `rank_prompter_replies` | `message_ranking` | `EvaluateTask` |
| `/evaluate/rank_assistant_replies` | `rank_assistant_replies` | Evaluate | `rank_assistant_replies` | `message_ranking` | `EvaluateTask` |
| `/evaluate/rank_initial_prompts` | `rank_initial_prompts` | Evaluate | `rank_initial_prompts` | `message_ranking` | `EvaluateTask` |
| `/label/label_initial_prompt` | `label_initial_prompt` | Label | `label_initial_prompt` | `text_labels` | `LabelTask`, full mode |
| `/label/label_prompter_reply` | `label_prompter_reply` | Label | `label_prompter_reply` | `text_labels` | `LabelTask`, full mode |
| `/label/label_assistant_reply` | `label_assistant_reply` | Label | `label_assistant_reply` | `text_labels` | `LabelTask`, full mode |
| `/label/label_initial_prompt` | `classify_initial_prompt` | Label | `label_initial_prompt` | `text_labels` | `LabelTask`, simple mode |
| `/label/label_prompter_reply` | `classify_prompter_reply` | Label | `label_prompter_reply` | `text_labels` | `LabelTask`, simple mode |
| `/label/label_assistant_reply` | `classify_assistant_reply` | Label | `label_assistant_reply` | `text_labels` | `LabelTask`, simple mode |

Other important website routes:

| Route | Purpose |
|---|---|
| `/chat` | Chat list. Hidden or redirected when browser config disables chat/end-of-life behavior. |
| `/chat/[id]` | Chat conversation page with model/plugin config drawer, streamed assistant responses, voting, retries, and multi-draft selection. |
| `/messages`, `/messages/[id]` | Message browsing/detail UI. |
| `/dashboard`, `/stats`, `/leaderboard`, `/contributors`, `/account/*`, `/auth/*` | Authenticated dashboard, stats/leaderboard, profile/account, and sign-in flows. |
| `/admin/*` | Admin and moderator surfaces; role handling starts in NextAuth and backend authorization. |

## Task page lifecycle

`TaskPage` chooses a task API hook based on the requested `TaskType`, then renders one of three states:

1. `AWAITING_INITIAL`: loading screen while the initial task request is in flight.
2. `NONE_AVAILABLE`: empty state when a task cannot be fetched.
3. `AVAILABLE`: task context is provided and the shared `Task` container renders the task family.

The generic task hook performs the frontend lifecycle:

1. Request a new task through the website API route for `new_task` with the active locale.
2. Store the returned task response locally and derive `taskInfo` from `TaskInfos` using the returned task type. This matters for `/tasks/random`, because the returned concrete task may not be `random`.
3. On completion, post `{ id, update_type, content, lang }` to the website `update_task` API route.
4. On successful completion, request the next task.
5. On skip/reject, post the frontend task id to the reject route and then request the next task.

The Next API routes then bridge to the backend: new task fetch, local task registration, ack, local task interaction record, backend task interaction, and next-task refresh. Backend semantics are routed to `backend`; the website layer owns request wiring, UI state, local registration, and user-visible error handling.

## Shared `Task` review/submit state machine

The shared task container uses four states:

| State | Meaning | Primary controls |
|---|---|---|
| `EDIT` | User can modify the task answer. Reply validity controls whether review is enabled. | Skip, Review |
| `DEFAULT_WARN` | A default but valid answer was detected; user must confirm continuing. | Edit, Continue anyway |
| `REVIEW` | Answer is frozen for review before final submission. | Edit, Submit |
| `SUBMITTED` | Submit in progress; controls disable repeated submission. | disabled Submit |

Important behavior:

- `onReplyChanged` stores raw content in a ref so child components do not need to own submission.
- `onValidityChanged` drives whether Review is disabled, whether a default-answer warning appears, or whether Submit is reachable.
- `CreateTask` can call the shared submit handler with `Ctrl+Enter` or `Cmd+Enter`.
- Submission catches `OasstError`; task-type-unavailable is rethrown for the hook to turn into `NONE_AVAILABLE`, while other backend errors produce a toast and return to edit mode.
- Stable task-control selectors are `data-cy="review"`, `data-cy="submit"`, and `data-cy="edit"`.

## Create task UI pattern

`CreateTask` handles initial prompts, user replies, and assistant replies.

Key behavior:

- Top-level selector: `data-cy="task"` with `data-task-type="create-task"`.
- Non-initial prompt tasks render the prior conversation and highlight the last message.
- Blank or whitespace-only text marks the reply invalid.
- Non-blank text marks the reply valid and stores `{ text }` as the reply content.
- The editor is a ByteMD-backed Markdown editor wrapped by `TrackedTextarea`; it adds a stable `data-cy="reply"` hook for Cypress.
- The UI has Write and Preview tabs; preview lazy-renders markdown.
- The word-progress thresholds are low 20, medium 40, goal 50 words.
- `TrackedTextarea` detects language after more than four words and compares the detected language with the active locale; wrong-language warnings can be locale-sensitive and should be tested with realistic text.
- Desktop users see the keyboard-submit hint; `Ctrl+Enter` or `Cmd+Enter` triggers review or submission depending on current state.

When adding new create-style tasks, keep the route, `TaskInfos` entry, translation keys, task hook mapping, content shape `{ text }`, and tests aligned.

## Evaluate/ranking task UI pattern

`EvaluateTask` handles ranking initial prompts, user replies, and assistant replies.

Key behavior:

- Top-level selector: `data-cy="task"` with `data-task-type="evaluate-task"`.
- For initial prompt ranking, sortable items are prompt candidates. For reply ranking, sortable items are reply messages and the prior conversation is shown above the sorter.
- Initial ranking is the natural order of items and is treated as `DEFAULT` unless the user toggles `not_rankable` or changes order.
- Reply content shape is `{ ranking: number[], not_rankable: boolean }`.
- `not_rankable` makes the reply valid even if the sort order was unchanged.
- The sorter uses dnd-kit pointer, mouse, and keyboard sensors; keyboard tests can focus a sortable item, press Enter, move with arrow keys, and press Enter again.
- If `reveal_synthetic` is set, synthetic markers are shown through the sortable item UI.

When debugging rank tests, prefer accessibility and `data-cy` selectors over CSS classes. The existing sortable accessibility role description is a useful stable hook.

## Label task UI pattern

`LabelTask` handles full and simple labeling/classification tasks for initial prompts, prompter replies, and assistant replies.

Key behavior:

- Top-level selector: `data-cy="task"` with `data-task-type="label-task"`, except simple spam-only tasks use `data-task-type="spam-task"`.
- The left side renders the conversation and highlights the last message.
- The right side renders `LabelInputGroup`, which groups labels by widget type: `yes_no`, `flag`, and `likert`.
- Required labels come from `mandatory_labels`; if any required label has not been answered, validity is `INVALID`.
- If no required labels exist and the user has made no input, validity is `DEFAULT`.
- Any user input makes validity `VALID` once required labels are satisfied.
- Reply content shape is `{ text: "unused?", labels: Record<labelName, number>, message_id }`.
- `LabelYesNoGroup` uses selectors `data-cy="label-question"`, `data-cy="yes"`, and `data-cy="no"`.
- Likert rows expose `data-cy="label-options"`; individual radio buttons expose `data-cy="radio-option"`.
- Flag buttons are label-name-driven and show tooltip explanations; tests should assert visible translated labels or state changes rather than internal arrays.

When adding label behavior, keep translation keys in the labelling namespace, preserve required-label validation, and avoid changing the response numeric scale unless backend semantics are coordinated through `backend`.

## Frontend OASST API client behavior

`OasstApiClient` is the website layer's typed wrapper around backend HTTP calls.

Request behavior:

- Constructor takes `oasstApiUrl`, `oasstApiKey`, and optionally a backend user core.
- All requests include `X-API-Key` and `Content-Type: application/json`.
- When a user is present, requests also include `X-OASST-USER` as `<auth_method>:<id>`.
- `204 No Content` returns `null`.
- HTTP status `>= 300` reads response text and tries to parse JSON. If parsing succeeds, it throws `OasstError` with `message`, `error_code`, HTTP status, path, and method. If parsing fails, it throws `OasstError` with the raw text and error code 0.
- Query helper drops undefined query values before building search params.

Methods grouped by responsibility:

| Group | Representative methods |
|---|---|
| Tasks | `fetchTask`, `ackTask`, `nackTask`, `interactTask`, `fetch_tasks_availability`, `fetch_available_tasks` |
| Messages and trees | `fetch_message`, `fetch_message_tree`, `fetch_message_tree_state`, `fetch_message_revision_history`, `delete_message`, `undelete_message`, `edit_message`, `set_tree_halted`, `fetch_message_children`, `fetch_conversation`, cursor methods |
| Users and accounts | `fetch_user`, `fetch_users`, `fetch_frontend_user`, `upsert_frontend_user`, `set_user_status`, `delete_account`, stats methods |
| Labels/reports/emoji | `fetch_valid_text`, `send_report`, `set_user_message_emoji` |
| Stats and leaderboards | cached stats, live stats, tree-manager stats, leaderboard, trollboard |
| Settings/admin | public/full backend settings |

The Axios helper used by browser-side SWR routes also wraps errors into `OasstError`. Check both wrappers when frontend error fields appear inconsistent.

## Website API route map

Important Next API routes and ownership:

| Website API route | Website responsibility | Routed-out semantics |
|---|---|---|
| `/api/new_task/[task_type]` | Translate locale/user/session into backend task fetch and local task registration. | Which tasks are available and task payload semantics. |
| `/api/update_task` | Ack task, store local interaction JSON, submit backend interaction, and return status. | Backend update validation, scheduler state, and task state machine. |
| `/api/reject_task` | Reject/skip current frontend task and request another. | Backend rejection policy. |
| `/api/available_tasks`, `/api/valid_labels` | Frontend fetch/proxy and locale/user handling. | Backend counts and label schema ownership. |
| `/api/messages/*`, `/api/stats/*`, `/api/leaderboard`, `/api/admin/*` | Website request shapes and UI consumption. | Backend data model and authorization semantics. |
| `/api/config` | Browser-safe config projection. | Secret management and infrastructure policy. |
| `/api/auth/*` | NextAuth providers, debug credentials, email sign-in, role projection. | OAuth provider configuration outside local dev. |
| `/api/chat/*` | Session-gated proxy to inference, chat CRUD, message creation, voting, model/plugin fetch, and event stream pipe. | Inference server/worker protocol and model execution. |

## Chat UI and SSE flow

Chat route behavior:

- `/chat` lists chats and can allow hidden/visible views in development.
- `/chat/[id]` fetches model configs and plugins, initializes default generation parameters from the first model config, and renders the chat conversation plus config UI.
- Server-side chat routes return 404 when `ENABLE_CHAT` is not truthy.

Chat form behavior:

- `Enter` submits unless `Shift` is held.
- `Shift+Enter` inserts a newline.
- While sending, the send icon is replaced by an indeterminate progress spinner.
- On desktop, the textarea is focused automatically.

Conversation flow:

1. User text is trimmed; empty text or a send already in progress is ignored.
2. If a draft-selection flow is pending, submitting is blocked with a toast.
3. The active assistant parent is read from the rendered conversation tree; incomplete parent messages cannot be replied to.
4. A prompter message is posted through the website chat API route and appended locally.
5. An assistant message request is posted with model config, sampling parameters, plugins, and optional custom instructions.
6. The browser fetches the website event-stream API route for the assistant message.
7. If the stream route returns `204`, the final message is fetched immediately.
8. Otherwise `handleChatEventStream` parses events and updates queue info, token text, plugin intermediate response, or final message.
9. Final assistant messages are appended and the active thread tail is updated.

SSE parser behavior:

- The iterator decodes a `ReadableStream<Uint8Array>` through `TextDecoderStream`.
- It buffers unfinished lines across chunks. This is essential for tokens or JSON split across network boundaries.
- Both LF and CRLF line endings are accepted.
- Empty lines are ignored.
- Multiple `field: value` lines in one chunk yield multiple objects.
- An unfinished final line without a trailing newline is intentionally not yielded.
- Parsed event data is JSON-decoded by `handleChatEventStream`; malformed JSON logs a parse error but does not crash the loop.

Known chat event types handled at the website layer:

| Event type | UI effect |
|---|---|
| `pending` | Updates queue position/size badge and clears plugin intermediate text. |
| `token` | Appends token text to the streamed assistant response and clears queue/plugin status once text arrives. |
| `message` | Returns the final inference message and finishes streaming. |
| `error` | Calls error handler and returns the message carried by the error event if present. |
| `plugin_intermediate` | Shows current plugin thought/action/action response/input data. |
| `ping` SSE event | Ignored. |

When debugging chat UI, separate the website-side symptoms (wrong key behavior, missing config, SSE line buffering, stale SWR state, toast/error mapping) from inference-side symptoms (model config invalid, worker disconnected, websocket/API key failure, model OOM/download).
