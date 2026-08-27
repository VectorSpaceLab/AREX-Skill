# Opyrator Workflows

## Purpose

Read this when you know the task is about Opyrator but you have not yet chosen the narrow sub-skill route. This page maps common user requests to the owning sub-skill and highlights the commands that matter.

## 1. Wrap a callable and call it locally

Use the wrapping path when the user wants to turn a Python function into an Opyrator-compatible callable and execute it locally.

Typical request signals:
- "wrap this function"
- "call it from the CLI"
- "why is my callable rejected?"
- "what does export/deploy do here?"

Route to: [`sub-skills/wrapping-and-cli/SKILL.md`](../sub-skills/wrapping-and-cli/SKILL.md)

Common commands:

```bash
opyrator call my_module:hello_world '{"message": "hello"}'
opyrator call --help
opyrator export --help
opyrator deploy --help
```

Notes:
- `call` executes the wrapped callable locally and prints JSON.
- `export` and `deploy` currently print WIP messages in the verified 0.0.12 snapshot.
- The callable contract requires a parameter named exactly `input` and a Pydantic-compatible return annotation.

## 2. Serve the callable as FastAPI

Use the API path when the user wants a local HTTP service, OpenAPI output, or route inspection.

Typical request signals:
- "launch the API"
- "OpenAPI schema"
- "why does `/docs` break under a subpath?"
- "what is the response model for `/call`?"

Route to: [`sub-skills/api-services/SKILL.md`](../sub-skills/api-services/SKILL.md)

Common commands:

```bash
opyrator launch-api my_module:hello_world --host 0.0.0.0 --port 8080
```

Notes:
- `create_api(Opyrator(...))` builds the `FastAPI` app in-process.
- `launch_api` starts `uvicorn` and blocks.
- `patch_fastapi` is what keeps docs routes compatible with relative subpath deployment.

## 3. Launch the Streamlit UI or render component widgets

Use the UI/component path when the user wants the interactive form or custom renderers.

Typical request signals:
- "launch the UI"
- "why is this field a slider instead of a text box?"
- "how do I upload a file?"
- "how do I customize the output renderer?"

Route to: [`sub-skills/ui-and-components/SKILL.md`](../sub-skills/ui-and-components/SKILL.md)

Common commands:

```bash
opyrator launch-ui my_module:hello_world --port 8051
python sub-skills/ui-and-components/scripts/schema_smoke.py --json
```

Notes:
- The UI is schema-driven and built on `streamlit`.
- `FileContent` values use `format: byte` in Pydantic/OpenAPI.
- Custom `render_input_ui` and `render_output_ui` hooks are supported for advanced cases.

## 4. Check the install before deeper debugging

If anything looks stale or broken at install time, run the bundled smoke helper before changing code:

```bash
python scripts/check_install.py --json
```

Use this to confirm the installed package, CLI entry point, core wrapper, API app creation, and FileContent behavior from the current environment.
