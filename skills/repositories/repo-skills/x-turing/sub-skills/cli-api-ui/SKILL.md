---
name: cli-api-ui
description: "Route xTuring command-line chat, FastAPI serving,
  OpenAI-compatible completions, and Gradio playground usage and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI, API, and UI

Use this sub-skill when the task is about xTuring command-line interaction, the API server, or the Gradio playground.

## Covers

- `xturing chat` interactive terminal chat
- `xturing api` FastAPI serving
- `xturing ui` / `Playground` Gradio usage
- legacy `/api` requests and OpenAI-compatible completions
- streaming skeletons, `n=1` limits, and service errors
- model-path loading for the CLI server and playground

## Use the references

- [CLI reference](references/cli-reference.md)
- [Playground and API reference](references/playground-and-api.md)
- [Troubleshooting](references/troubleshooting.md)
- [API contract smoke script](scripts/api_contract_smoke.py)

## Out of scope

- model registry or generation internals
- dataset preparation
- finetuning or alignment
- evaluation workflows
