# Sessions Troubleshooting

## `Session persistence cannot be combined...`

Symptom: `Runner.run(...)` or `Runner.run_streamed(...)` raises:

```text
Session persistence cannot be combined with conversation_id, previous_response_id, or auto_previous_response_id.
```

Cause: `session=` was passed at the same time as a server-managed continuation setting.

Fix:

- Keep `session=...` and remove `conversation_id`, `previous_response_id`, and `auto_previous_response_id` when the app owns history.
- Or remove `session=` and use OpenAI server-managed continuation when the provider should own history.
- If resuming a `RunState`, do not add `session=` if that state was created with server-managed conversation settings.

## Optional Backend Import Fails

Symptom: importing an extension backend raises an `ImportError` with an install hint.

Common fixes:

| Backend | Install |
| --- | --- |
| `RedisSession` | `pip install 'openai-agents[redis]'` |
| `SQLAlchemySession` | `pip install 'openai-agents[sqlalchemy]'` |
| `MongoDBSession` | `pip install 'openai-agents[mongodb]'` |
| `DaprSession` | `pip install 'openai-agents[dapr]'` |
| `EncryptedSession` | `pip install 'openai-agents[encrypt]'` |
| `AsyncSQLiteSession` | `pip install aiosqlite` |

Run `python scripts/check_session_backend.py --backend all --json` to see which imports are available without contacting external services.

## SQLite Database Path Or Table Surprise

Symptoms:

- History disappears between processes.
- Multiple users see mixed history.
- A custom table name creates unexpected schema.

Causes and fixes:

- `SQLiteSession("id")` defaults to `db_path=":memory:"`; pass a file path for persistence.
- Distinct conversations require distinct `session_id` values even if they share a database file.
- Custom `sessions_table` and `messages_table` names must be stable across all app instances that need to share the same stored history.
- Call `session.close()` for long-lived file-backed SQLite sessions when the app is done with the session.

## Stale Or Missing History

Symptoms:

- The model ignores old context.
- A later turn sees only recent items.
- The database still has older rows, but the model does not receive them.

Check:

- `RunConfig(session_settings=SessionSettings(limit=N))` only retrieves the latest N items; it does not delete old rows.
- `limit=0` intentionally sends no previous history while still saving the new turn.
- `session_input_callback` can filter or reorder history for the model call without changing stored history.
- `call_model_input_filter` runs later and can also trim the final model input; route detailed model-input shaping questions to [core-runtime](../../core-runtime/SKILL.md).

## Duplicate History Or Replayed Tool Outputs

Symptoms:

- Old messages appear twice in model input.
- Retried or resumed runs duplicate tool call outputs.

Fixes:

- Do not manually call `session.add_items(result.to_input_list())` after a run that already used `session=`.
- In a `session_input_callback`, return only the final model input; the SDK detects which returned items are new and persists only new-turn items.
- For interrupted approval flows, resume with `Runner.run(agent, state, session=session)` rather than replaying previous user input manually.

## Compaction Confusion

Symptoms:

- Streaming appears complete but `stream_events()` stays open briefly.
- Compaction raises a model or response ID error.
- History is shorter after a run.

Causes and fixes:

- Auto-compaction runs at run completion and may block final completion while the session is cleared and rewritten.
- Use `should_trigger_compaction=lambda _: False` and manually call `run_compaction({"force": True})` during idle time for lower-latency streaming.
- `compaction_mode="previous_response_id"` requires a usable response ID and an OpenAI Responses API chain.
- `compaction_mode="input"` compacts from current session items and is safer when response IDs are unavailable or `store=False` is used.
- `OpenAIResponsesCompactionSession` cannot wrap `OpenAIConversationsSession`; choose one history-management path.

## Encryption Key Or TTL Pitfalls

Symptoms:

- Old encrypted items disappear from retrieval.
- Existing encrypted history cannot be read after a deploy.
- Advanced content search no longer works well.

Causes and fixes:

- `EncryptedSession` derives per-session encryption from the supplied key and session ID; keep the key stable and application-managed.
- Items older than `ttl` are skipped during retrieval, which can look like missing memory.
- Content-based queries in advanced backends are limited because payloads are encrypted.
- Wrap an underlying backend first, then apply `EncryptedSession`; do not expect encryption to add database migrations or backend connectivity.

## OpenAIConversationsSession ID Is Not Available Yet

Symptom: reading `session.session_id` raises that the session ID is not yet available.

Cause: `OpenAIConversationsSession()` lazily creates a conversation on the first API operation.

Fix: call `await session.get_items()`, `await session.add_items(...)`, or run the agent once before reading `session.session_id`; or construct with `OpenAIConversationsSession(conversation_id="...")` when resuming an existing conversation.
