# Gradio and FastAPI Reference

## Purpose

Read this when turning Janus-family workflows into a local UI or HTTP service.

## Demo variants and dependency choices

The upstream evidence includes separate UI variants for Janus, Janus-Pro, and JanusFlow. Do not require future agents to run those source files directly; use the bundled service skeleton or recreate a small UI from the workflow references.

Use these public install choices when building a UI:

- `pip install -e .[gradio]` for the Gradio dependency set.
- `pip install diffusers[torch]` in addition to the base install for JanusFlow generation.

## FastAPI endpoints from the repo

The FastAPI demo exposes:

### `POST /understand_image_and_question/`

Form fields:

- `file`: upload file
- `question`: string
- `seed`: integer, default `42`
- `top_p`: float, default `0.95`
- `temperature`: float, default `0.1`

Returns JSON containing a `response` field.

### `POST /generate_images/`

Form fields:

- `prompt`: string
- `seed`: integer or omitted
- `guidance`: float, default `5.0`

Returns streamed image data.

## Safe serving patterns

- Lazy-load the model inside a factory or startup hook instead of at import time.
- Keep `share=False` by default for local-only usage.
- Separate server startup from client requests.
- Keep the model id configurable so the same skeleton can host Janus, Janus-Pro, or JanusFlow as appropriate.
- Make the host and port explicit in the server command.

## Client patterns

A useful local client should:

- accept a base URL,
- accept image and prompt/question inputs,
- validate the request fields before posting,
- save or print responses in a user-friendly format.

## When to choose which dependency set

- Gradio demo only: install the `gradio` extra.
- FastAPI service only: install `fastapi`, `uvicorn`, and `python-multipart` in addition to the base package.
- Client only: install `requests` in addition to the base package.
