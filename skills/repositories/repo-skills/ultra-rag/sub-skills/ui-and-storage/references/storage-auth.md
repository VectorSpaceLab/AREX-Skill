# UltraRAG Storage, Auth, and Session State

## Purpose

Read this when the task is about where the UI stores its data, how auth works,
or which environment variables affect session and KB behavior.

## Storage root

The storage tree is resolved by `ui/backend/storage_paths.py`.

- Environment variable: `ULTRARAG_UI_STORAGE_ROOT`
- Default root: `ui/storage`

Key subdirectories:

- `db/users.sqlite3`
- `chat_sessions/`
- `knowledge_base/raw/`
- `knowledge_base/corpus/`
- `knowledge_base/chunks/`
- `knowledge_base/index/`
- `knowledge_base/kb_config.json`
- `knowledge_base/_memory_sync/`
- `memory/`
- `ext/`

## Authentication store

`ui/backend/auth.py` provides `SQLiteUserStore`.

Verified behavior:

- Usernames must match `^[A-Za-z][A-Za-z0-9_]{2,31}$`.
- `default` is reserved.
- Passwords must be at least 6 characters.
- The database auto-creates a default admin user.
- The default admin password constant in source is `12345678`.
- Model settings are stored per user for retriever and generation roles.

## Chat store

`ui/backend/chat_store.py` provides `SQLiteChatStore`.

It validates:

- session ids
- user ownership
- session titles
- message structure and timestamps

It stores chat sessions and messages in SQLite tables under the UI database.

## KB visibility store

`ui/backend/kb_visibility_store.py` provides `SQLiteKbVisibilityStore`.

It tracks:

- collection ownership
- public/private/shared visibility
- per-user visibility lists

This store is used by the UI backend when showing and managing collections.

## Session and runtime environment variables

- `ULTRARAG_SESSION_SECRET`
- `ULTRARAG_SESSION_COOKIE_SECURE`
- `ULTRARAG_SESSION_TIMEOUT`
- `ULTRARAG_BG_SESSION_TIMEOUT`
- `ULTRARAG_LOG_TS`

## Memory sync behavior

The UI backend can sync per-user memory content into KB collections and clear
vector state for a user-owned memory collection. This is part of the chat / KB
workflow, not the pipeline DSL itself.

## Practical reminders

- If the UI or case-study viewer starts failing after a storage-path change,
  check the root and the writable permissions first.
- If auth or chat state looks inconsistent, inspect the SQLite database under
  the resolved storage root before touching pipeline code.
