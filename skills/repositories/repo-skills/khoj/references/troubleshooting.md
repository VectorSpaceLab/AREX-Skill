# Khoj Cross-Cutting Troubleshooting

## Start Here

Use this file when the failure spans multiple Khoj surfaces. For route-specific details, jump to the nearest sub-skill troubleshooting reference.

## Setup and Startup

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `khoj --help` shows a PostgreSQL connection error | The console script imports `khoj.main`, which runs Django migrations before parser output | Use `sub-skills/deployment-api/scripts/inspect_cli.py` for parser-only validation; configure PostgreSQL or embedded DB before running the real service |
| Dependency conflict during `pip install khoj` | Khoj pins broad AI/runtime dependencies that can conflict with an existing environment | Install in an isolated virtual environment, pipx, conda env, or Docker container |
| Tokenizer/Rust build failure | A dependency needs Rust or no wheel is available for the platform/Python version | Use a supported Python version and install Rust only if a wheel is unavailable |
| Docker process exits with `Killed` | Container memory is too low for ML/runtime dependencies | Increase Docker memory or use a lighter deployment path |
| Admin user cannot be created in non-interactive mode | Missing admin email/password environment variables | Provide admin credentials through environment variables before first non-interactive start |

## API, Auth, and Host Errors

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| CSRF, host, cookie, or login errors | Domain/proxy/HTTPS settings do not match request host | Check `KHOJ_DOMAIN`, `KHOJ_ALLOWED_DOMAIN`, `KHOJ_NO_HTTPS`, and whether the browser uses `localhost` vs `127.0.0.1` |
| `401` or unauthenticated API responses | Missing session or bearer token | Use the authenticated web session, client token, or anonymous mode only for local trusted setups |
| `503` or model-not-configured chat errors | No valid chat model/API key/base URL is configured | Use `deployment-api` for provider setup, then `chat-agents` for chat-specific validation |

## Indexing and Search

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Upload succeeds but search returns nothing | Entries may not be embedded, filters may exclude results, or query is under a different user/agent | Use `content-indexing` to validate ingestion and `search-retrieval` to inspect filters, `SearchType`, distance threshold, and user isolation |
| Remote GitHub/Notion sync yields no entries | Missing token, repo/page access, or unsupported source configuration | Validate remote source config in `content-indexing` before debugging retrieval |
| Parser output looks different from expected | Chunking, heading ancestry, line-number URI handling, or deletion-marker semantics are involved | Use `content-indexing/scripts/parse_content_fixture.py` with a tiny fixture and compare `raw`, `compiled`, `heading`, `file`, and `uri` |

## Chat, Agents, Tools, and Automations

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `/online`, `/webpage`, `/code`, `/image`, `/operator`, or voice fails | Optional service, model provider, sandbox, or credentials are unavailable | Use `chat-agents` troubleshooting and route provider/base URL issues back to `deployment-api` |
| Agent cannot access expected files or tools | Agent privacy, creator, file knowledge base, input tools, output modes, or subscription restrictions are mismatched | Use `chat-agents` agent-configuration reference and verify accessible files/tools for the current user |
| Automation is rejected | Invalid cron, unsupported minute-level recurrence, duplicate automation, missing user/conversation, or timezone mismatch | Use `automations-memory/scripts/validate_cron.py` and the automation troubleshooting reference |
| Memory is missing after update | Memory updates delete and recreate rows, and memories can be scoped by user/agent | Use `automations-memory` memory reference to check ownership and settings |

## Development

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Focused test selection is unclear | Khoj spans API routes, parser code, search filters, chat actors, scheduler, database models, and frontend/docs | Use `development/scripts/select_focused_tests.py` and `development/references/test-selection.md` |
| Migration/model change breaks runtime | Adapters/admin/fixtures/default rows or PostgreSQL/pgvector expectations were missed | Use `development/references/migrations-and-models.md` and test against a disposable database |
| Tests try to call real external services | Chat/provider/tool tests may require mocks or skip markers | Prefer focused unit/parser/filter/API tests first; avoid network, credentials, long evals, and production DBs unless explicitly approved |
