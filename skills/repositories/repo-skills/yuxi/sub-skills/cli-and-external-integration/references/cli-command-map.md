# CLI command map

This matrix tells a future Researcher which command group to load, which remote
or service state is required, and which native tests prove the behavior.

## Command matrix

| Command group | Examples | Offline-only? | Required state | Side effects | Key endpoints |
| --- | --- | --- | --- | --- | --- |
| Install/help | `yuxi --version`, `python -m yuxi_cli --help`, `yuxi remote --help`, `yuxi kb --help`, `yuxi agent eval --help` | yes | none | none | none |
| Remote config | `yuxi remote add`, `yuxi remote use`, `yuxi remote list` | yes | none | writes `~/.yuxi/config.toml` only | config file only |
| Health probe | `yuxi remote ping [name]` | no | reachable remote | read-only remote call | `GET /api/system/health` |
| Login | `yuxi login --browser`, `yuxi login --api-key ...` | no | discovery and auth endpoints reachable | stores local API key; browser flow can mint or delete remote API keys | `GET /api/system/discovery`, `POST /api/auth/cli/sessions`, `POST /api/auth/cli/sessions/token`, `GET /api/auth/me` |
| Identity/status | `yuxi whoami`, `yuxi status`, `yuxi logout [--local-only]` | no | logged-in remote | logout may delete remote API key unless `--local-only` | `GET /api/auth/me`, `GET /api/system/health`, `DELETE /api/user/apikey/{api_key_id}` |
| Browser chat | `yuxi chat [--agent-slug ...] [--no-open]` | no | logged-in remote and local browser | creates chat/run traffic on the remote; local page is temporary | `POST /api/agent-invocation/channel/messages`, `GET /api/agent/runs/{run_id}/events` |
| KB read/query | `yuxi kb list`, `files`, `query`, `open`, `find` | no | logged-in remote with `cli.kb_*` capability | read-only remote calls | `/api/knowledge/databases/external*` |
| KB upload | `yuxi kb upload PATH ...` | no | logged-in remote with `cli.kb_upload` and an uploadable KB | writes MinIO and document records | `GET /api/knowledge/databases/{kb_id}/documents/exists`, `POST /api/knowledge/files/upload`, `POST /api/knowledge/databases/{kb_id}/documents/add` |
| Langfuse eval | `yuxi agent eval ...` | no | logged-in remote plus `LANGFUSE_*` env and dataset access | writes Langfuse experiment results and calls the remote eval API | `POST /api/agent-invocation/eval/runs` |

## Canonical local bootstrap

Use this only for a running local development stack:

```bash
yuxi remote add local http://localhost:5173
yuxi remote use local
yuxi login --browser
```

## Command notes

- `remote add` normalizes the URL and strips any trailing `/api` before saving.
- `login --browser` is the preferred login path; `login --api-key` requires a
  token that starts with `yxkey_`.
- `status` checks health first and then auth state when a key is stored.
- `chat` defaults to `default-chatbot` and serves a temporary local page on
  `127.0.0.1`.
- `kb upload` syntax is `yuxi kb upload [OPTIONS] PATH`; key options are `--kb-id TEXT`, `--remote TEXT`, `--yes/-y`, `--concurrency INTEGER` (1-300, default 10), `--include-ext TEXT`, `--exclude-ext TEXT`, and `--force-upload-file`. It prompts when `--kb-id` or confirmation is omitted in an interactive terminal.
- `kb upload` does not expose a documented per-upload OCR-engine flag. OCR selection is server-side through the configured default engine or backend parse parameters; check the remote OCR options/health before uploading scanned PDFs.
- `kb query` syntax is `yuxi kb query --kb-id KB_ID [--file-name TEXT] [--top-k N] [--search-mode TEXT] [--remote NAME] [--json] QUERY`.
- `kb files` lists/searches files with `--kb-id`, optional `--query`, `--offset`, `--limit`, `--status`, `--remote`, and `--json`.
- `kb open` reads parsed file content with `--kb-id`, `--file-id`, `--offset`, `--limit`, `--remote`, and `--json`.
- `kb find` searches inside a parsed file with `--kb-id`, `--file-id`, repeatable `--pattern/-p`, optional `--regex`, `--case-sensitive`, `--max-windows`, `--window-size`, `--remote`, and `--json`.
- `agent eval` reads an existing Langfuse dataset; it does not create or upload that dataset.

## Native proof points

- Config and remote persistence: `packages/yuxi-cli/tests/test_config.py`
- Login, status, and logout behavior: `packages/yuxi-cli/tests/test_commands.py`
- CLI registration and help output: `packages/yuxi-cli/tests/test_main.py`
- API client and SSE parsing: `packages/yuxi-cli/tests/test_client.py`
- Browser chat helper and stream bridge: `packages/yuxi-cli/tests/test_chat_web.py`
- KB external commands and help: `packages/yuxi-cli/tests/test_kb_commands.py`
- KB upload behavior and safety gates: `packages/yuxi-cli/tests/test_kb_upload.py`
- Langfuse eval command behavior: `packages/yuxi-cli/tests/test_agent_eval.py`
