---
name: "interactive-frontends"
description: "Operate DeepAnalyze CLI, WebUI v2, and Jupyter frontend workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# interactive-frontends

Use this sub-skill for terminal, browser, and Jupyter-facing DeepAnalyze tasks.

## Route first

- Terminal commands, file IDs, `clear` / `clear-all`, history paths, downloads -> [CLI reference](./references/cli-reference.md)
- Browser workspace, file preview, download bundles, report export, provider choice, local vs Docker execution, frontend/backend/file ports -> [WebUI v2](./references/webui-v2.md)
- Jupyter setup, `uv sync`, `.env`, `config.toml`, `uv run CLI.py`, notebook workspace, MCP -> [Jupyter frontend](./references/jupyter-frontend.md)
- Port conflicts, Node/npm, Docker image, PDF export, fonts, MCP failures, unsupported previews -> [Troubleshooting](./references/troubleshooting.md)
- Safe preflight audit -> [WebUI prereq checker](./scripts/check_webui_prereqs.py)

## What this skill must cover

- CLI command help, upload, files, delete, download, status, history, fid, clear, clear-all.
- WebUI v2 provider modes: Local, HeyWhale API, Custom Model.
- Workspace behavior: preview, download, generated-file handling, export, session separation.
- Local vs Docker execution and the ports used by the browser demo.
- Jupyter notebook startup, config, workspace, and MCP connection behavior.

## Boundaries

- Do not expand into raw API request/response schemas.
- Do not explain model serving, quantization, training, or evaluation here.
- Use the legacy `demo/chat` notes only when the user explicitly asks about the older demo.
- Prefer the bundled references in this subtree over memory when answering.

## Operating hints

- If a task sounds like "can I start it?" or "why is it failing?", consult [Troubleshooting](./references/troubleshooting.md) first.
- If the task is about a browser demo coming up cleanly, run or describe [scripts/check_webui_prereqs.py](./scripts/check_webui_prereqs.py) before changing ports or deleting files.
- If the task is about notebook-first work, keep the answer centered on `uv`, `config.toml`, the generated notebook, and the local workspace directory.
