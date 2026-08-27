# Streaming and Chat

## Purpose

Read this when you need to trace a backend observer event all the way to the chat UI, especially for message streaming, sub-agent cards, tool output, sources, verification, attachments, or resume behavior.

## Chat surfaces

Nexent currently has two user-facing chat stacks:

| Surface | Main files | Role |
| --- | --- | --- |
| Legacy chat | `app/[locale]/chat/page.tsx`, `internal/chatInterface.tsx`, `streaming/chatStreamHandler.tsx`, `streaming/messageTransformer.ts`, `streaming/chatStreamMain.tsx`, `streaming/chatStreamFinalMessage.tsx` | Imperative chat UI that builds `ChatMessageType` state directly from the SSE stream. |
| assistant-ui chat | `app/[locale]/newchat/page.tsx`, `assistant-ui/chat.tsx`, `assistant-ui/thread.tsx`, `adapter/conversation-thread-list-adapter.tsx`, `adapter/remote-chat-model-adapter.ts`, `adapter/attachment-adapter.ts`, `adapter/server-dictation-adapter.ts` | Threaded chat runtime that maps SSE chunks into assistant-ui parts and persistent thread state. |

## End-to-end trace

### 1. Request creation

`frontend/services/conversationService.ts::runAgent()` sends the chat request to one of these endpoints:

- `/api/agent/run`
- `/api/agent/nl2agent/run`
- `/api/skills/nl2skill/run`

The request body can include:

- `query`
- `conversation_id`
- `history`
- `minio_files`
- `agent_id`
- `model_id`
- `version_no`
- `is_debug`
- `is_resume`
- `enable_plan`
- `runtime_mode`
- `draft_snapshot`
- `complexity`
- `language`

`runAgent()` returns either:

- a `ReadableStreamDefaultReader<Uint8Array>` for SSE streaming, or
- JSON when the backend finishes immediately during a resume/completed path.

It also forwards the server-issued `conversation_id` response header to the caller so the UI can bind the thread to the backend conversation.

### 2. Attachment upload

`adapter/attachment-adapter.ts` uploads files to MinIO through `storageService.uploadFiles()` and then stashes the returned metadata on each attachment:

- `object_name`
- `url`
- `presigned_url`
- `type`
- `size`

`conversationService.runAgent()` forwards those files as `minio_files`.

### 3. SSE parsing and UI mapping

Both chat stacks consume backend chunks with the same general shape:

```json
{ "type": "...", "content": "...", "unit_index": 12, "invocation_id": "..." }
```

The exact shape can also carry `tool_call_id`, `role`, `tool_name`, `tool_arguments`, `agent_id`, `agent_name`, `depth`, and other metadata fields used by sub-agent rendering.

## Stream event map

| Backend chunk family | Legacy chat handling | assistant-ui handling | Main renderers / notes |
| --- | --- | --- | --- |
| `step_count` | Opens a new step block and updates the step title. | Becomes a reasoning part and a timing anchor. | `chatStreamHandler.tsx`, `remote-chat-model-adapter.ts`, `MessageTiming`, `SingleTurnTokenUsage` |
| `token_count` | Updates per-step metrics. | Updates step timing and token usage registries. | `remote-chat-model-adapter.ts`, `types/chat.ts` |
| `model_output`, `model_output_thinking`, `model_output_deep_thinking` | Adds streamed reasoning text. | Maps to `reasoning` parts, with `deep_thinking` kept separate. | `Reasoning`, `GroupReasoningTrigger`, `thread.tsx` |
| `model_output_code` | Shows code-generation state or code text depending on mode. | Usually treated as reasoning/code content and grouped with the current sub-agent run. | `ToolFallback`, `ToolGroup`, `thread.tsx` |
| `tool` | Creates an execution card and keeps parsing content. | Maps to `tool-call`. | `ToolGroup`, `ToolFallback` |
| `parse` | Kept as internal parsing detail. | Skipped. | The UI does not surface it directly. |
| `execution_logs` | Skipped in the legacy step stream. | Attached to the tool call that produced them. | Tool result cards, not a standalone message. |
| `search_content` | Adds search results to the current step and message-level search registry. | Maps to `source` parts. | `Sources`, `SourcesPanel`, right-side source panel |
| `picture_web` | Adds web-image references to the current message. | Maps to `source` parts and image source entries. | `SourcesPanel`, image tabs |
| `card` | Renders a standalone task card. | Skipped or represented as generic content. | Used for structured assistant output. |
| `memory_search` | Adds memory retrieval status/content. | Usually a text part with memory status. | Memory traces and UI notices |
| `verification` | Adds verification blocks to the active step. | Rendered by the verification panel. | `VerificationPanel` |
| `max_steps_reached` | Stores the max-step warning on the step. | Rendered as a text/status part. | `chatStreamHandler.tsx` |
| `skill_files` | Attaches generated files to the assistant message. | Becomes file attachments in the assistant-ui thread. | `SkillFileCard`, `skill_file_uploads` registry |
| `final_answer` | Appends the final answer text and marks the message complete. | Ends the stream and leaves the final assistant content visible. | `MarkdownText`, `chatStreamFinalMessage.tsx` |
| `history_summary` | Updates the historical summary for the covered assistant message. | Updates the matching persisted message in place. | Resume/history synchronization |
| `conversation_created` | Captures the newly created backend conversation id. | Binds the thread to the server conversation. | `conversationThreadListAdapter`, `thread.tsx` |
| `plan`, `plan_step_update` | Planning metadata for the task UI. | Stored in the shared plan registry. | Planning mode in `newchat` |
| `subagent_start`, `subagent_end` | Opens/closes nested sub-agent cards. | Opens/closes grouped sub-agent parts using `invocation_id`. | `SubAgentContainer`, `group-subagent-*` |
| `status`, `stream_status` | Internal resume markers. | Skipped. | Resume recovery only |

## Legacy chat state shape

The legacy stream handler builds `ChatMessageType` objects with these important fields:

- `steps`
- `finalAnswer`
- `searchResults`
- `images`
- `attachments`
- `thinking`
- `maxStepsInfo`
- `isComplete`

If a new backend chunk type is added, the legacy handler usually needs three updates:
1. `frontend/const/chatConfig.ts`
2. `frontend/types/chat.ts`
3. `frontend/app/[locale]/chat/streaming/chatStreamHandler.tsx`

## assistant-ui thread reconstruction

`adapter/conversation-thread-list-adapter.tsx` is responsible for:

- loading historical conversations,
- restoring a thread from persisted messages,
- rebuilding plan state,
- rebuilding historical sub-agent boundaries,
- and keeping `conversation_id` / `thread_id` mapping stable across reloads.

`adapter/remote-chat-model-adapter.ts` is responsible for:

- converting SSE chunks into assistant-ui parts,
- keeping sibling sub-agent runs isolated by `invocation_id`,
- attaching `metadata.subagentId`, `metadata.runId`, `metadata.agentName`, `metadata.depth`, and `metadata.task`,
- and collapsing the grouped parts into a stable stream result.

### Why `invocation_id` matters

When two sub-agents run in parallel, the frontend must not rely on a shared stack order alone. `invocation_id` is the stable key that keeps each nested card, reasoning block, and closing boundary aligned with the right sub-agent.

## Resume and replay behavior

Resume support uses two layers:

- the backend returns persisted `streaming_message` and `unit_index` values,
- the frontend skips already processed chunks and reconstructs the visible state.

Important helpers:

- `conversationService.getDetail()` fetches the persisted conversation snapshot.
- `chatStreamHandler.tsx` skips already replayed `unit_index` values in resume mode.
- `remote-chat-model-adapter.ts` uses `planRegistry`, `stepTokenCounts`, and `conversation_id` thread state to restore a stable run.

## Voice and dictation

`adapter/server-dictation-adapter.ts` handles microphone capture and STT websocket traffic.

It depends on:

- `conversationService.stt.getAudioConstraints()`
- `conversationService.stt.getAudioContextOptions()`
- `conversationService.stt.createWebSocket()`
- `conversationService.stt.processAudioData()`

If dictation is configured incorrectly, the UI usually fails before any chat stream is created.

## Common debugging paths

| Symptom | First place to check |
| --- | --- |
| Raw JSON or a missing stream card | `remote-chat-model-adapter.ts` and `chatStreamHandler.tsx` chunk mapping. |
| Sub-agent cards merge together | `invocation_id` propagation and `thread.tsx` grouping logic. |
| Resume duplicates steps or metrics | `conversation-thread-list-adapter.tsx` and `streaming_message.unit_index`. |
| Sources disappear after a refactor | `searchSourcesRegistry`, `conversationSourcesRegistry`, and the `search_content` / `picture_web` handlers. |
| Generated files do not appear | `skill_file_uploads` parsing and `SkillFileCard` wiring. |
| Dictation never starts | STT config, microphone permission, or websocket proxy behavior. |

## Later verification note

When this sub-skill is verified, compare the frontend stream semantics with the backend streaming/conversation unit tests so a new event type or conversation-field change does not drift on either side.
