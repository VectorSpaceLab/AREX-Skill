# Apps and Local Server

## Install only the needed surface

Marker’s base package covers the core converter. App and server entry points need additional packages that are not required for every conversion workflow.

```bash
pip install marker-pdf
pip install fastapi uvicorn python-multipart      # for marker_server
pip install streamlit                            # for marker_gui
pip install streamlit streamlit-ace              # for marker_extract
pip install marker-pdf[full]                     # for PPTX/DOCX/XLSX/HTML/EPUB inputs
```

Use the sibling conversion sub-skill for output-format details and the sibling LLM sub-skill for any `use_llm` service setup.

## Surface selection

| Need | Entry point | Notes |
| --- | --- | --- |
| Local HTTP conversion API | `marker_server --host 127.0.0.1 --port 8000` | Starts a FastAPI app with `/`, `/docs`, `/marker`, and `/marker/upload`. |
| Quick interactive conversion | `marker_gui` | Starts a Streamlit document/image conversion app. |
| Interactive structured extraction | `marker_extract` | Starts a Streamlit extraction app with JSON schema and Pydantic schema panels. |
| Hosted GPU endpoint | Modal deployment recipe | Requires Modal account setup, cloud runtime, and explicit deployment commands. |

## FastAPI server

`marker_server` accepts only host and port flags:

```bash
marker_server --host 127.0.0.1 --port 8000
```

Useful local URLs after startup:

- `GET /`: simple HTML landing page with links to docs and the conversion route.
- `GET /docs`: FastAPI-generated API documentation.
- `POST /marker`: JSON body that names a filepath visible to the server process.
- `POST /marker/upload`: multipart upload that stores the uploaded file temporarily before conversion.

Operational notes:

- The server loads Marker models during FastAPI lifespan startup, so first startup or first model-cache miss can be slow.
- The server sets `pdftext_workers` to `1` for conversion requests.
- The local server code is intentionally simple: do not treat it as production-hardened without adding authentication, upload validation, request size limits, rate limits, logging, timeout controls, and concurrency controls.
- Use `scripts/server_cli_smoke.py` for bundled checks; it verifies help/imports without starting the server.

## Streamlit GUI launcher

`marker_gui` launches Marker’s Streamlit conversion app through the installed console script:

```bash
marker_gui
```

The launcher runs Streamlit headless with file watching disabled and forwards any extra CLI-style Marker options to the app after Streamlit’s `--` separator internally. The app lets users upload PDF, image, PPTX, DOCX, XLSX, HTML, or EPUB files, choose a page range and output format, and toggle common conversion flags such as `force_ocr`, `strip_existing_ocr`, and debug mode.

If the task only needs non-interactive conversion, route to `../conversion-cli-api/` instead of launching Streamlit.

## Streamlit extraction launcher

`marker_extract` launches the structured extraction app:

```bash
marker_extract
```

The extraction app accepts a file upload plus either a JSON schema or Pydantic schema text, then runs Marker extraction and displays JSON output. Treat the Pydantic schema panel as unsafe for untrusted input because the app converts entered Pydantic code into a runtime class. Do not expose this app to untrusted users without isolating and hardening it.

## Safe adaptation checklist

- Confirm whether the caller needs a UI, a local HTTP server, or a hosted service before installing optional packages.
- Prefer `/marker/upload` when the client file is not on the same filesystem as the server process.
- Prefer `/marker` filepath mode only when the server can read the exact path.
- Prevalidate `output_format` as one of `markdown`, `json`, `html`, or `chunks` before sending requests.
- Route `use_llm` and provider setup to the LLM sub-skill; the bundled local `marker_server` request model does not expose a `use_llm` field by default.
