# Session Backends

## Decision Matrix

| Backend | Import | Install requirement | Best fit | Caveats |
| --- | --- | --- | --- | --- |
| `SQLiteSession` | `from agents import SQLiteSession` | Base package | Local development, tests, single-process apps, simple file-backed persistence | `:memory:` is process-local and lost on exit; close file-backed sessions when finished. |
| `AsyncSQLiteSession` | `from agents.extensions.memory import AsyncSQLiteSession` | `aiosqlite` must be installed separately | Async apps that want SQLite without worker-thread `sqlite3` usage | Not listed as a package extra; install `aiosqlite` explicitly if missing. |
| `RedisSession` | `from agents.extensions.memory import RedisSession` | `openai-agents[redis]` | Shared low-latency session memory across workers/services | Requires an async Redis client or URL and live Redis service; TTL is optional. |
| `SQLAlchemySession` | `from agents.extensions.memory import SQLAlchemySession` | `openai-agents[sqlalchemy]` | Production apps with existing SQLAlchemy-supported databases | Use async engines/drivers; `create_tables=True` is convenient for dev/tests but production often uses migrations. |
| `MongoDBSession` | `from agents.extensions.memory import MongoDBSession` | `openai-agents[mongodb]` | Apps already using MongoDB or needing multi-process horizontal storage | Uses async PyMongo; message ordering uses a per-session monotonic `seq` counter. |
| `DaprSession` | `from agents.extensions.memory import DaprSession` | `openai-agents[dapr]` | Cloud-native deployments already using Dapr state stores | Requires a Dapr sidecar and state store; TTL support depends on the backing store. |
| `OpenAIConversationsSession` | `from agents import OpenAIConversationsSession` | Base package plus OpenAI API access | OpenAI-hosted conversation item storage through the Conversations API | Networked; do not confuse with `conversation_id` runner continuation parameters. |
| `OpenAIResponsesCompactionSession` | `from agents.memory import OpenAIResponsesCompactionSession` | Base package plus OpenAI API access | Long SDK-session histories that should be compacted through `responses.compact` | Wraps another session but cannot wrap `OpenAIConversationsSession`; model must look like an OpenAI `gpt-*`, `o*`, or `ft:gpt-*` name. |
| `AdvancedSQLiteSession` | `from agents.extensions.memory import AdvancedSQLiteSession` | Base package | SQLite with branching, usage analytics, and structured queries | Set `create_tables=True` when the advanced schema should be created; usage analytics require calling `store_run_usage(result)` after each run. |
| `EncryptedSession` | `from agents.extensions.memory import EncryptedSession` | `openai-agents[encrypt]` | Encrypting any underlying session with optional TTL expiration | Content-based advanced queries are limited because stored content is encrypted; expired items are silently skipped on retrieval. |

## Built-In Protocol

Every session backend follows the `Session` protocol:

| Operation | Purpose | Notes |
| --- | --- | --- |
| `await session.get_items(limit=None)` | Read stored input items in chronological order | A numeric limit returns the latest N items, still chronological. |
| `await session.add_items(items)` | Append new turn items | Runner calls this automatically when `session=` is used. |
| `await session.pop_item()` | Remove and return the latest item | Useful for correcting the last assistant/user exchange. |
| `await session.clear_session()` | Remove all stored items for that session | For `OpenAIConversationsSession`, this deletes the remote conversation and clears the local ID. |

## SQLiteSession

`SQLiteSession(session_id, db_path=':memory:', sessions_table='agent_sessions', messages_table='agent_messages', session_settings=None)` is available from the base install. It stores JSON-serialized input items in two tables and supports custom table names.

Use `SQLiteSession("user-123")` for ephemeral memory, or pass a file path for persistence across process restarts. Multiple session IDs can share one database file while keeping independent histories.

## Extension Backends and Extras

The extension namespace lazy-loads optional backends and raises install guidance when an extra is missing. Typical install names are:

| Backend | Extra or package |
| --- | --- |
| `RedisSession` | `pip install 'openai-agents[redis]'` |
| `SQLAlchemySession` | `pip install 'openai-agents[sqlalchemy]'` |
| `MongoDBSession` | `pip install 'openai-agents[mongodb]'` |
| `DaprSession` | `pip install 'openai-agents[dapr]'` |
| `EncryptedSession` | `pip install 'openai-agents[encrypt]'` |
| `AsyncSQLiteSession` | `pip install aiosqlite` |

Use `scripts/check_session_backend.py` to verify imports without contacting Redis, MongoDB, Dapr, SQL databases, or OpenAI.

## Backend Selection Rules

- Choose `SQLiteSession` first for local apps, tests, single-host assistants, and prototypes.
- Choose `SQLAlchemySession` when the application already has database migrations, pooled async engines, or a production SQL database.
- Choose `RedisSession` for shared memory where low latency and TTL are more important than rich querying.
- Choose `MongoDBSession` when MongoDB is already the operational store or multi-process ordering matters.
- Choose `DaprSession` only when Dapr is part of the deployment; otherwise it adds sidecar complexity.
- Wrap an existing backend in `EncryptedSession` when stored conversation content needs encryption and TTL-based expiration.
- Wrap an existing backend in `OpenAIResponsesCompactionSession` when long histories should be compacted while staying in SDK-managed session mode.
- Use `OpenAIConversationsSession` only when remote OpenAI Conversations item storage is desired and network/API credentials are available.

## Server-Managed Continuation Is Not A Session Backend

Runner parameters `conversation_id`, `previous_response_id`, and `auto_previous_response_id` activate OpenAI server-managed continuation. They are mutually exclusive with `session=`. Use those parameters when OpenAI should retain/chain context on the server and only deltas should be sent; use a `Session` backend when your application owns stored history.
