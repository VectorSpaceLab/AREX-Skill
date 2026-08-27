# Migrations And Models

## Model Layout

Khoj keeps Django models in `src/khoj/database/models/__init__.py`, not separate per-model files. The same module also contains Pydantic models used for chat/conversation payload validation, so distinguish database schema changes from pure payload-schema changes.

Important model families include:

- User/auth/subscription: `KhojUser`, `GoogleUser`, `KhojApiUser`, `Subscription`, `ClientApplication`.
- Model-provider configuration: `AiModelApi`, `ChatModel`, `SearchModelConfig`, `TextToImageModelConfig`, `SpeechToTextModelOptions`, voice model config, and user-specific config models.
- Agent/chat/conversation: `Agent`, `Conversation`, `PublicConversation`, chat message Pydantic models, and related server/user conversation settings.
- Content/search persistence: `FileObject`, `Entry`, `EntryDates`, GitHub/Notion config, web scraper config, and vector fields using pgvector.
- Operations: `ProcessLock`, scheduler-related Django APScheduler models, `UserRequests`, `RateLimitRecord`, `DataStore`, `McpServer`, `UserMemory`.

Most concrete database models inherit `DbBaseModel`, which supplies `created_at` and `updated_at`. Preserve nullability, defaults, related names, and uniqueness semantics deliberately because adapters and tests often assume them.

## Migration Patterns

Migrations live under `src/khoj/database/migrations` and show these recurring patterns:

- pgvector extension setup uses `VectorExtension()` early in the migration chain.
- Ordinary model changes use Django-generated `CreateModel`, `AddField`, `AlterField`, `RemoveField`, `RenameField`, `RenameModel`, and merge migrations.
- Data migrations use `migrations.RunPython` with `apps.get_model(...)`; avoid importing runtime model classes directly in migration functions.
- Some data migrations use `reverse_code=migrations.RunPython.noop` when rollback is intentionally not data-restoring; prefer a real reverse function when practical.
- Long or risky migrations iterate records and catch per-record exceptions only when preserving deployment progress is more important than strict all-or-nothing behavior.
- Migrations that touch existing JSON/conversation logs should handle missing keys and older shapes defensively.

For new fields on tables with data, choose defaults and nullability intentionally. Avoid adding a non-null field without a safe default or staged migration plan. For high-volume data changes, prefer chunked iteration and idempotent logic.

## Model Change Checklist

Before editing schema:

1. Identify every adapter, router, admin class, fixture/factory, and test that reads or writes the model.
2. Decide whether the change is schema-only, data migration, API contract, admin visibility, or client-visible behavior.
3. Plan rollback behavior for migrations, especially when renaming fields, moving data, or changing JSON structures.
4. Check whether the model participates in auth/user isolation, agent scoping, file ownership, vector search, scheduler jobs, or billing/rate limiting.
5. Add focused tests that prove both direct adapter behavior and route-level behavior when the model is exposed through FastAPI.

After editing schema:

- Generate or update a migration in `src/khoj/database/migrations` with a dependency on the latest relevant database migration.
- Validate `makemigrations --check --dry-run` in a disposable development environment after the migration exists to ensure no untracked model drift remains.
- Run `migrate` against a disposable PostgreSQL/pgvector database before trusting schema-dependent tests.
- Run the focused pytest files from `test-selection.md`; avoid real user databases.

## Admin Considerations

Django admin registrations are in `src/khoj/database/admin.py` and use `unfold_admin.ModelAdmin` for most models. When adding or changing a model that operators need to inspect:

- Register the model or update its existing admin class.
- Add `list_display`, `search_fields`, `list_filter`, and `ordering` only for fields that are safe and useful in admin.
- Avoid exposing secrets such as API keys or tokens in list displays.
- For user-facing records, include user/email/search fields when helpful, but preserve privacy and access expectations.
- For scheduler/job models, keep custom job-store lookup behavior intact.

## Adapter Considerations

`src/khoj/database/adapters/__init__.py` centralizes much of the ORM access used by routers and processors. Adapter functions frequently enforce user scoping with `require_valid_user` or `arequire_valid_user`, use async ORM methods for async routes, and raise HTTP exceptions for route-facing validation.

When changing models:

- Update adapter create/read/update/delete helpers instead of duplicating ORM logic in routers.
- Keep async routes on async adapter methods where possible; avoid accidental sync ORM calls in async code.
- Preserve user scoping for `KhojUser`, `Agent`, `Conversation`, `Entry`, `FileObject`, `UserMemory`, and config models.
- Use `transaction.atomic` or existing atomic patterns for multi-step updates such as agent knowledge-base replacement.
- Keep vector-search queries and file/content deletion semantics aligned with `Entry`, `FileObject`, and search tests.

## Tests And Fixtures

`tests/conftest.py` creates default users, API tokens, subscriptions, chat clients, search models, and indexed fixture content. Factories in `tests/helpers.py` create model/provider settings used across chat, search, memory, automation, and agent tests.

When a schema change affects fixtures:

- Update factories and fixtures first so route-level tests fail for behavior, not missing required fields.
- Include multi-user isolation tests when ownership fields or query filters change.
- Include memory/agent-specific scoping tests when adding fields to `Agent`, `Conversation`, `UserMemory`, or config models.
- Include search/index tests when changing `Entry`, `FileObject`, `SearchModelConfig`, embeddings fields, or content source metadata.

## Runtime Database Safety

Khoj startup and the console script can initialize Django, collect static files, and run migrations before CLI parsing. Avoid using runtime startup commands as parser checks. For schema work, run migration commands only against a disposable development database with known `POSTGRES_*` env vars or the Docker test database.

Never plan a migration by testing only on SQLite. Khoj relies on PostgreSQL and pgvector, including vector fields and extension setup. If PostgreSQL is unavailable, keep the migration plan explicit and mark runtime migration validation as pending rather than pretending parser-only tests prove database safety.
