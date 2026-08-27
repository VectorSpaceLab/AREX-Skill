---
name: demos-and-serving
description: "Guides Janus Gradio demos, FastAPI services, and client workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Demos and Serving

Use this sub-skill when the task is about running or adapting a Janus-family Gradio demo, a FastAPI service, or a small client for the demo endpoints.

## Read first

- [`references/gradio-and-fastapi.md`](references/gradio-and-fastapi.md) for demo commands, endpoint contracts, and safe launch patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for optional dependency, port, payload, and streaming failures.
- [`scripts/janus_fastapi_skeleton.py`](scripts/janus_fastapi_skeleton.py) for a lazy-loading service skeleton.
- [`scripts/janus_fastapi_client.py`](scripts/janus_fastapi_client.py) for a configurable client.

For the core model workflows, use the sibling sub-skills:

- [`../multimodal-understanding/SKILL.md`](../multimodal-understanding/SKILL.md)
- [`../image-generation/SKILL.md`](../image-generation/SKILL.md)
- [`../janusflow-workflows/SKILL.md`](../janusflow-workflows/SKILL.md)

## When to use this route

Choose this route when the user asks to:

- Launch or adapt the Gradio demos.
- Serve Janus understanding or generation through FastAPI.
- Build a small client that calls the demo endpoints.
- Change endpoint names, form fields, output paths, or port settings.
- Replace import-time model loading with safer lazy loading.

## Core workflow

1. Decide whether the user wants an interactive demo or an API.
2. Pick the correct model family and dependencies.
3. Load the model lazily if you are serving it.
4. Keep the launch command and the client command separate.
5. Verify the request payload names before testing the server.
6. Prefer a local-only launch unless the user explicitly wants sharing.

## Safe launch guidance

The upstream demo scripts load models at import time and some use `share=True`. Use the generated helper scripts instead when you want a safer starting point.

- `gradio` is only needed for the UI path.
- `fastapi`, `uvicorn`, and `python-multipart` are only needed for the API path.
- `requests` is only needed for the client path.

## Route elsewhere

- Use the model sub-skills for prompt construction, generation, and decoding details.
- Use the root installation reference when you need the dependency matrix.
