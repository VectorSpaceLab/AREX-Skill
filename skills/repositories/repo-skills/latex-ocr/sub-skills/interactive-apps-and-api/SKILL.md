---
name: interactive-apps-and-api
description: "Guides LaTeX-OCR GUI, FastAPI, Streamlit, and Docker service
  workflows for interactive or deployed pix2tex OCR."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Interactive Apps and API

Use this sub-skill when the user wants the `latexocr` desktop GUI, screenshot
capture, formatted output, the FastAPI service, Streamlit demo, Docker API
container, or optional dependency troubleshooting for these interactive routes.

## Quick Route

- For API, Streamlit, Docker, request formats, and ports, read
  [references/api-and-ui.md](references/api-and-ui.md).
- For desktop GUI behavior, screenshot tools, formatting, and desktop entries,
  read [references/gui-workflow.md](references/gui-workflow.md).
- For failures, read [references/troubleshooting.md](references/troubleshooting.md).
- Run [scripts/check_api_dependencies.py](scripts/check_api_dependencies.py)
  before starting a server; it imports the FastAPI app without loading the
  model startup event or launching uvicorn.

## API Summary

Install API dependencies:

```bash
pip install "pix2tex[api]"
```

Run the API app directly when model downloads and long-lived processes are
allowed:

```bash
uvicorn pix2tex.api.app:app --host 0.0.0.0 --port 8502
```

The app exposes `/` for health, `/predict/` for image uploads, and `/bytes/` for
raw byte uploads. Both prediction endpoints expect multipart field name `file`.

## GUI Summary

Install GUI dependencies:

```bash
pip install "pix2tex[gui]"
latexocr
```

Use `SCREENSHOT_TOOL=grim`, `SCREENSHOT_TOOL=spectacle`,
`SCREENSHOT_TOOL=gnome-screenshot`, or `SCREENSHOT_TOOL=pil` to override the
screenshot backend when auto-detection picks the wrong one.

## Boundaries

- Core model inference and image-quality guidance belongs in
  [../ocr-inference/SKILL.md](../ocr-inference/SKILL.md).
- Dataset rendering, scraping, and training belong in sibling sub-skills.
- Do not launch GUI windows, desktop installers, uvicorn, Streamlit, or Docker
  unless the user explicitly wants a long-running or desktop-side-effect action.
