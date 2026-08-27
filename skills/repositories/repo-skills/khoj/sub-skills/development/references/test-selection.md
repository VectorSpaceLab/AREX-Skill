# Focused Test Selection

## Principles

Start with tests closest to the changed code, then expand only when the change crosses boundaries. Prefer file-level pytest commands over full `pytest` during development. Avoid `tests/evals` and broad chat-quality suites unless the user asks for expensive quality validation or the change directly targets those behaviors.

Common safe command patterns:

- Single file: `pytest tests/test_markdown_to_entries.py`
- One test: `pytest tests/test_client.py::test_index_update`
- Multiple focused files: `pytest tests/test_client.py tests/test_markdown_to_entries.py`
- Broad non-eval backend confidence: `pytest -m "not chatquality"`
- CLI parser only: `pytest tests/test_cli.py`

## Changed Area Map

| Changed area or capability | Focused tests to start with | Notes |
| --- | --- | --- |
| CLI parser, flags, defaults, non-interactive mode | `tests/test_cli.py` | Import `khoj.utils.cli.cli`; do not use `khoj --help` as a harmless probe. |
| Markdown parser | `tests/test_markdown_to_entries.py` | Add tiny fixtures in the test when parsing semantics change. |
| Org parser and orgnode tree handling | `tests/test_org_to_entries.py`, `tests/test_orgnode.py` | Keep entry ancestry, line numbers, and splitting behavior explicit. |
| Plaintext/HTML/XML parser | `tests/test_plaintext_to_entries.py` | Use small local strings/fixtures; avoid network reads. |
| PDF parser | `tests/test_pdf_to_entries.py` | OCR coverage is intentionally skipped for performance in current tests. |
| DOCX parser | `tests/test_docx_to_entries.py` | Fixture files live under `tests/data/docx`. |
| Image parser/OCR | `tests/test_image_to_entries.py` | Watch for slow OCR/runtime dependencies. |
| Content upload/index API | `tests/test_client.py` | Covers `/api/content`, `/api/update`, auth, content type validation, size limits, search endpoint basics. |
| Multi-user isolation for content/search | `tests/test_multiple_users.py`, selected `tests/test_client.py` cases | Include when changing auth, API tokens, or user scoping. |
| Text search setup/update/delete | `tests/test_text_search.py` | Uses embeddings/cross-encoder fixtures; can be slower than pure parser tests. |
| Date filters | `tests/test_date_filter.py` | Include natural-date parsing and term extraction cases. |
| File filters | `tests/test_file_filter.py` | Include include/exclude and regex cases. |
| Word filters | `tests/test_word_filter.py` | Include include/exclude term extraction. |
| Grep files helper/tool | `tests/test_grep_files.py` | Async and DB-backed; covers regex, context, path prefixes, and multi-file behavior. |
| Generic helpers and web reads | `tests/test_helpers.py` | External webpage test coverage can be environment-sensitive; respect skips. |
| Conversation utility JSON/message handling | `tests/test_conversation_utils.py` | Pure utility coverage for truncation and complex JSON loading. |
| Chat actors, online search, tool choice, prompt actors | `tests/test_online_chat_actors.py` | Many cases are `chatquality` or provider-dependent; use selected tests or `-m "not chatquality"` when avoiding expensive quality tests. |
| Chat director and answer synthesis | `tests/test_online_chat_director.py` | DB-backed; includes expected xfails and chat-quality markers. |
| Agent CRUD, knowledge base, atomic update behavior | `tests/test_agents.py` | Includes large-KB and concurrent update tests; choose specific tests for performance. |
| Automation API and scheduling | `tests/test_api_automation.py` | Requires provider API key for current tests; otherwise skip behavior is expected. |
| Memory settings and memory scoping | `tests/test_memory_settings.py` | Include server/user config matrix and async memory tool tests. |
| Process lock model/helper behavior | `tests/test_db_lock.py` | Use when editing lock model/adapters or scheduler lock logic. |
| Django models, migrations, admin, adapters | Model-specific focused tests plus `tests/test_db_lock.py`, `tests/test_agents.py`, `tests/test_memory_settings.py`, `tests/test_client.py` as applicable | Also run migration checks manually in a disposable DB when changing schema. |
| FastAPI router changes | Route-specific tests: `tests/test_client.py`, `tests/test_api_automation.py`, `tests/test_agents.py`, `tests/test_memory_settings.py`, `tests/test_online_chat_actors.py`, or `tests/test_online_chat_director.py` | Match the router: content/search, automation, agents, memory, chat/research. |
| Frontend web code | Client package build/test command plus backend route tests if API contracts changed | The web app uses Bun in contributor docs. Do not assume backend pytest validates frontend. |
| Documentation-only changes | No backend tests required unless code snippets or behavior claims changed | Validate formatting/build only if the user asks or the docs build is in scope. |

## API Route Examples

- `src/khoj/routers/api_content.py`: start with `pytest tests/test_client.py`; add parser tests when upload parsing or content-type behavior changes.
- `src/khoj/routers/api_chat.py` or `src/khoj/routers/research.py`: start with a selected chat actor/director test and avoid the full chat-quality matrix unless needed.
- `src/khoj/routers/api_agents.py`: start with selected `tests/test_agents.py` cases; include memory/search tests if agent knowledge-base scoping changes.
- `src/khoj/routers/api_automation.py`: start with `tests/test_api_automation.py`; expect provider-key skip behavior for tests marked with `GEMINI_API_KEY` dependency.
- `src/khoj/routers/api_memories.py`: start with `tests/test_memory_settings.py`; include agent scoping cases when memory ownership changes.
- Auth/session/router helper changes: include `tests/test_client.py`, `tests/test_multiple_users.py`, and any route-specific tests touched by the helper.

## Parser Plus API Example

For a change touching an API route plus Markdown parsing, use a staged selection:

1. `pytest tests/test_markdown_to_entries.py` to validate parser entry splitting, headings, compiled/raw fields, and line-number behavior.
2. `pytest tests/test_client.py::test_index_update tests/test_client.py::test_regenerate_with_valid_content_type` to validate upload/update integration through the API.
3. Add `pytest tests/test_text_search.py::test_update_index_with_new_entry` if search index update semantics changed.
4. Do not run `tests/evals` or all chat-quality tests unless the change affects answer quality or retrieval behavior beyond ingestion/search mechanics.

## Model Or Migration Example

For a Django schema change, pair migration validation with behavior tests:

1. Update `src/khoj/database/models/__init__.py` and generate or edit a migration in `src/khoj/database/migrations`.
2. Add or update adapter/admin behavior where the model is read, written, displayed, or filtered.
3. Select focused tests for model ownership: `tests/test_db_lock.py` for `ProcessLock`, `tests/test_agents.py` for `Agent`, `tests/test_memory_settings.py` for `UserMemory`/memory config, `tests/test_client.py` and `tests/test_text_search.py` for `Entry`/`FileObject`/search models.
4. In a disposable database, run migration commands before broader pytest: `python src/manage.py makemigrations --check --dry-run`, `python src/manage.py migrate`, and a focused pytest command.

## Helper Script

Use `scripts/select_focused_tests.py` from this sub-skill to turn changed paths or capability names into candidate pytest files. It is deterministic and prints commands only; it never imports Khoj, starts services, connects to a database, or executes pytest.
