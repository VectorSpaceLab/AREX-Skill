# WebUI v2 reference

`demo/chat_v2` is the browser-first DeepAnalyze surface. It combines a Next.js frontend, a FastAPI backend, a workspace/file layer, and optional Docker-based code execution.

## Safe launch checklist

1. Copy `.env.example` to `.env`.
2. Install frontend deps with `npm install` inside the frontend folder.
3. Confirm the backend/model ports are free or already serving the intended processes.
4. Choose `DEEPANALYZE_EXECUTION_MODE=local` or `docker`.
5. If using Docker execution, build the image first; the demo never auto-builds it.

Use [scripts/check_webui_prereqs.py](../scripts/check_webui_prereqs.py) for a read-only audit before starting.

## Ports and URLs

| Surface | Default | Purpose |
|---|---|---|
| Frontend | `http://localhost:4000` | Browser UI |
| Backend API | `http://localhost:8200` | Workspace, chat, execute, export |
| File service | `http://localhost:8100` | Workspace file downloads/previews |
| Model service | `http://localhost:8000` | OpenAI-compatible model endpoint |
| WebSocket | `ws://localhost:8001` | Frontend live updates when configured |

`start.sh` and `stop.sh` are convenience scripts that manage these ports; they are not read-only helpers.

## Configuration

### Frontend build-time variables

| Key | Default | Meaning |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8200` | Browser calls to the backend |
| `NEXT_PUBLIC_AI_API_URL` | `http://localhost:8000` | Browser-facing model base |
| `NEXT_PUBLIC_WEBSOCKET_URL` | `ws://localhost:8001` | WebSocket endpoint |

### Backend `.env` variables

| Key | Default | Meaning |
|---|---|---|
| `DEEPANALYZE_API_BASE` | `http://localhost:8000/v1` | OpenAI-compatible model base |
| `DEEPANALYZE_MODEL_PATH` | `DeepAnalyze-8B` | Default model name |
| `DEEPANALYZE_WORKSPACE_BASE` | `workspace` | Session workspace root |
| `DEEPANALYZE_FILE_SERVER_PORT` | `8100` | File service port |
| `DEEPANALYZE_BACKEND_PORT` | `8200` | API port |
| `DEEPANALYZE_EXECUTION_MODE` | `local` | `local` or `docker` code execution |
| `DEEPANALYZE_DOCKER_IMAGE` | `deepanalyze-chat-exec:latest` | Prebuilt execution image |
| `DEEPANALYZE_DOCKER_WORKSPACE_DIR` | `/workspace` | Workspace mount path inside the container |
| `DEEPANALYZE_PDF_CJK_MAINFONT` | empty | Preferred CJK font for PDF export |
| `DEEPANALYZE_PDF_AUTO_DOWNLOAD_PANDOC` | `true` | Allow pandoc auto-download |
| `DEEPANALYZE_PDF_PANDOC_CACHE_DIR` | empty | Custom pandoc cache location |

## Provider modes

| Mode | When to use | Notes |
|---|---|---|
| `Local` | You already have a local DeepAnalyze-compatible endpoint | Uses the local endpoint and does not add the custom prompt prefix |
| `HeyWhale API` | You want the hosted HeyWhale provider | Requires an API key; the built-in HeyWhale base is used by default |
| `Custom Model` | You have your own OpenAI-compatible endpoint | Requires a model name and API base; API key is optional |

Important behavior:

- The custom provider injects a structured data-analysis prefix.
- The prefix is localized to the active UI language.
- Local and HeyWhale modes do not inject that extra prefix.
- The custom model name and custom API base are remembered in browser storage.

## Execution modes

### Local

- Runs code on the host Python environment.
- Best when the host already has the needed scientific packages.
- No container image is required.

### Docker

- Runs code inside an isolated container.
- You must build the image manually first:

```bash
docker build -t deepanalyze-chat-exec:latest -f Dockerfile.exec .
```

- If the image is missing, execution fails immediately.
- The container workspace defaults to `/workspace`.
- Do not assume the demo will build or repair the image for you.

## Workspace and file behavior

- Each session gets its own workspace under `workspace/<session_id>`.
- `workspace/files` lists files with download URLs and, when supported, preview URLs.
- `workspace/tree` returns a nested tree view for the sidebar.
- `workspace/upload` and `workspace/upload-to` place files into the session workspace.
- `workspace/move`, `workspace/file`, `workspace/dir`, and `workspace/clear` manage files and folders.
- `.py` uploads are blocked.
- Generated outputs are tracked under `workspace/generated`.

### Preview support

The browser can show a direct preview for images and PDFs, while the backend preview route is richer for data-oriented files.

| Type | Typical handling |
|---|---|
| text / log / JSON / YAML / Markdown | Text or markdown preview |
| CSV / TSV | Paginated table preview |
| Excel | Sheet-aware table preview |
| SQLite / DB | Table list or table preview |
| Image | Direct image preview in the frontend |
| PDF | Direct PDF preview in the frontend |
| Other | Binary fallback or download |

Use download when preview is unavailable or the browser cannot render the file type.

### Download and bundle export

- `workspace/download` returns inline content by default.
- Add `download=true` to force attachment behavior.
- `workspace/download-bundle` can package generated outputs by category:
  - `all`
  - `table`
  - `image`
  - `other`

## Report export

- `/export/report` builds Markdown and PDF reports from the assistant messages.
- It reads the structured `<Analyze> / <Understand> / <Code> / <Execute> / <Answer>` sections.
- Markdown is always the fallback artifact.
- PDF export depends on `pypandoc`, `pandoc`, and `xelatex`.
- When Chinese text is present, the export logic tries a list of CJK fonts and can use `DEEPANALYZE_PDF_CJK_MAINFONT`.
- If PDF dependencies are incomplete, the browser should report the failure and keep the Markdown artifact.

## Legacy note

The older `demo/chat` surface follows the same broad 8200 / 8100 / 4000 service pattern. Mention it only when the user explicitly asks about the legacy demo.
