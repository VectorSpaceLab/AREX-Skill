# UltraRAG UI Backend

## Purpose

Read this when you need the Flask routes, UI entry points, or the high-level
behavior of `ui/backend/app.py` and `ui/backend/pipeline_manager.py`.

## UI entry points

- `ultrarag.show ui` calls `ultrarag.client.launch_ui()`.
- `ultrarag.show case` calls `ultrarag.client.launch_case_study()`.
- `create_app(admin_mode=False)` builds the Flask application.
- The frontend static files are served from `ui/frontend/dist` by default, or
  from `ULTRARAG_FRONTEND_DIR` when that environment variable is set.

## Route catalog

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/change-password`
- `POST /api/auth/nickname`
- `POST /api/auth/model-settings`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Chat sessions and exports

- `GET /api/chat/sessions`
- `POST /api/chat/sessions`
- `GET /api/chat/sessions/<session_id>`
- `PUT /api/chat/sessions/<session_id>`
- `DELETE /api/chat/sessions/<session_id>`
- `DELETE /api/chat/sessions`
- `POST /api/chat/export/docx`

### Memory and configuration

- `GET /api/memory`
- `PUT /api/memory`
- `GET /api/memory/<user_id>`
- `PUT /api/memory/<user_id>`
- `GET /api/config/mode`
- `GET /api/templates`

### Server and tool discovery

- `GET /api/servers`
- `GET /api/tools`

### Pipelines

- `GET /api/pipelines`
- `POST /api/pipelines`
- `PUT /api/pipelines/<name>/yaml`
- `POST /api/pipelines/parse`
- `GET /api/pipelines/<name>`
- `DELETE /api/pipelines/<name>`
- `POST /api/pipelines/<name>/rename`
- `GET /api/pipelines/<name>/parameters`
- `PUT /api/pipelines/<name>/parameters`
- `POST /api/pipelines/<name>/build`
- `POST /api/pipelines/<name>/demo/start`
- `POST /api/pipelines/demo/stop`
- `POST /api/pipelines/<name>/chat`
- `POST /api/pipelines/chat/stop`
- `POST /api/pipelines/chat/clear-history`
- `GET /api/pipelines/chat/history`
- `POST /api/pipelines/<name>/chat/background`

### Background tasks

- `GET /api/background-tasks`
- `GET /api/background-tasks/<task_id>`
- `DELETE /api/background-tasks/<task_id>`
- `POST /api/background-tasks/clear-completed`

### Knowledge base

- `GET /api/kb/config`
- `POST /api/kb/config`
- `GET /api/kb/files`
- `GET /api/kb/visibility/users`
- `GET /api/kb/visibility/<collection_name>`
- `POST /api/kb/visibility/<collection_name>`
- `GET /api/kb/files/inspect`
- `POST /api/kb/upload`
- `DELETE /api/kb/files/<category>/<filename>`
- `POST /api/kb/staging/clear`
- `POST /api/kb/sync-memory`
- `POST /api/kb/clear-memory`
- `POST /api/kb/run`
- `GET /api/kb/status/<task_id>`

### Prompts and AI assistant

- `GET /api/prompts`
- `GET /api/prompts/<filepath>`
- `POST /api/prompts`
- `PUT /api/prompts/<filepath>`
- `DELETE /api/prompts/<filepath>`
- `POST /api/prompts/<filepath>/rename`
- `POST /api/ai/test`
- `POST /api/ai/chat`

### System

- `POST /api/system/shutdown`

## Pipeline manager highlights

`ui/backend/pipeline_manager.py` is the workhorse for:

- `list_servers()` / `list_server_tools()`
- `list_pipelines()` / `load_pipeline()` / `save_pipeline()` / `save_pipeline_yaml()`
- `rename_pipeline()` / `delete_pipeline()`
- `load_parameters()` / `save_parameters()` / `build()`
- `load_kb_config()` / `save_kb_config()`
- `list_kb_files()` / `upload_kb_files_batch()` / `delete_kb_file()`
- `clear_staging_area()` / `run_kb_pipeline_tool()`
- `sync_user_memory_to_kb()` / `clear_user_memory_collection_vectors()`
- background chat task helpers

## Case-study data shape

The case-study viewer consumes JSON or JSONL with cases shaped like:

```json
[
  [
    {"step": "...", "memory": {"q_ls": ["..."], "ans_ls": ["..."]}}
  ]
]
```

It also accepts a container object with keys such as `cases`, `data`,
`items`, `dataset`, `results`, `records`, or `list`.

## Frontend notes

- `ui/frontend/dist` is committed so `show ui` can work without a local frontend
  build.
- Rebuild the frontend when the React source changes and the committed dist is
  stale.
