# Storage Backend Reference

## Storage classes exposed by Upsonic

| Backend | Typical use |
| --- | --- |
| `InMemoryStorage` | Default lightweight persistence for local tests and smoke checks. |
| `JSONStorage` | Simple file-backed persistence. |
| `SqliteStorage` / `AsyncSqliteStorage` | Local persistent storage when you want a real database without service dependencies. |
| `RedisStorage` | Shared session/memory persistence for distributed deployments. |
| `PostgresStorage` / `AsyncPostgresStorage` | Durable relational backend for production memory/session data. |
| `MongoStorage` / `AsyncMongoStorage` | Document-oriented session or memory persistence. |
| `Mem0Storage` / `AsyncMem0Storage` | Mem0 integration for memory persistence workflows. |

## Common configuration guidance

- Start with `InMemoryStorage` when the workflow only needs a smoke check.
- Choose a persistent backend only when the user explicitly needs cross-process or cross-session storage.
- Keep storage connection strings and credentials in the environment, not in the skill tree.
- The root optional-extras reference explains which backend extras need installation.
