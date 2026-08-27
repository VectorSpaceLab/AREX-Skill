---
name: opyrator
description: "Guide future agents through Opyrator's callable wrapping, FastAPI
  service, and Streamlit UI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Opyrator

Use this skill when the request mentions **Opyrator**, the `opyrator` CLI, `launch-api`, `launch-ui`, `call`, `export`, `deploy`, `FileContent`, or the schema-driven UI and API surface built around Pydantic models.

## Start here

- If you need to check whether this skill still matches the repository snapshot, read `references/repo-provenance.md` first.
- If you only need a quick map of common workflows, read `references/workflows.md`.
- If install, import, or version pins are failing, read `references/troubleshooting.md` before changing the callable itself.
- If you need package-level API and CLI facts, read `references/api-reference.md`.
- For a safe local smoke check, run `scripts/check_install.py`.

## Install for this snapshot

This repository snapshot is verified on **Python 3.8** with the legacy-compatible stack that keeps the CLI, FastAPI service, and Streamlit UI importable.

Recommended install from the repo root:

```bash
python -m pip install -e . \
  "pydantic<2" \
  "fastapi==0.63.0" \
  "starlette==0.13.6" \
  "typer<0.8" \
  "click<8.1" \
  "streamlit==0.72.0" \
  "protobuf==3.20.3" \
  "altair<5" \
  "pandas<2" \
  "numpy<2" \
  "plotly" \
  "loguru" \
  "uvicorn<0.24"
```

Use the editable install when you are working from a local checkout. Use a normal install from a built source distribution only if you intentionally do not want editable behavior.

## How the skill routes

### 1. Wrap a Python callable and use the CLI

Route to [`sub-skills/wrapping-and-cli/SKILL.md`](sub-skills/wrapping-and-cli/SKILL.md) when the user wants to:

- build an `Opyrator` from a function, callable instance, or import string,
- validate `input` / return annotations,
- call a wrapped function from Python or `opyrator call`,
- or understand the current WIP behavior of `export` and `deploy`.

### 2. Serve the callable as FastAPI

Route to [`sub-skills/api-services/SKILL.md`](sub-skills/api-services/SKILL.md) when the user wants to:

- launch or inspect the FastAPI service,
- check `/call`, `/info`, `/docs`, `/redoc`, or `/openapi.json`,
- or troubleshoot relative docs routing and `patch_fastapi` behavior.

### 3. Launch the Streamlit UI or use FileContent / component renderers

Route to [`sub-skills/ui-and-components/SKILL.md`](sub-skills/ui-and-components/SKILL.md) when the user wants to:

- launch the Streamlit UI,
- understand schema-driven widgets,
- work with `FileContent`, `ClassificationOutput`, or custom render hooks,
- or debug widget/schema compatibility problems.

## Minimal verification

Use the bundled smoke helper after install:

```bash
python scripts/check_install.py --json
```

Expected result: the script reports `status: ok`, confirms the package version, checks a tiny `Opyrator` wrapper, verifies FastAPI app creation, confirms `FileContent` round-tripping, and checks the CLI help surface without starting any long-running server.

## What not to do here

- Do not tell future agents to depend on the original repo checkout for runtime behavior.
- Do not promise ZIP export, Docker export, PEX export, or cloud deployment from `export` / `deploy`; those commands are WIP placeholders in the verified snapshot.
- Do not route callable wrapping questions into the API or UI sub-skills just because those workflows also use the same callable contract.
