---
name: server-deployment
description: "Run Marker app, API server, client, and deployment surfaces safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Marker Server Deployment

Use this sub-skill when the task is to run, call, or adapt Marker’s local app/server/deployment surfaces rather than choose the core conversion pipeline.

## Choose the surface

- **Local FastAPI server**: use `marker_server --host HOST --port PORT`; read [apps and server](references/apps-and-server.md) and [API contract](references/api-contract.md).
- **Client integration**: use [scripts/marker_server_client_template.py](scripts/marker_server_client_template.py) for explicit `/marker` filepath or `/marker/upload` multipart requests.
- **Interactive apps**: use `marker_gui` for document-to-markdown/JSON/HTML/chunks trials and `marker_extract` for structured extraction UI; read [apps and server](references/apps-and-server.md).
- **Modal deployment**: adapt the reference-only Modal pattern in [modal deployment](references/modal-deployment.md) when a hosted GPU endpoint is needed.
- **Smoke checks**: run [scripts/server_cli_smoke.py](scripts/server_cli_smoke.py) to verify server CLI help/imports without starting a long-running service.

## Boundaries and routes

- For `output_format` semantics, page ranges, table/OCR converter choices, image extraction, and CLI/Python conversion workflows, route to sibling sub-skill `../conversion-cli-api/`.
- For `use_llm`, service selection, credentials, and structured extraction converter behavior outside the Streamlit launcher, route to sibling sub-skill `../llm-extraction-services/`.
- For custom processors, renderers, converter classes, config JSON, and debug internals, route to sibling sub-skill `../configuration-extension/`.
- Keep deployment checks safe: do not start `marker_server`, `marker_gui`, `marker_extract`, Modal deploys, model downloads, or external network calls unless the user explicitly asks.

## Minimum safe commands

```bash
python scripts/server_cli_smoke.py --check-import
python scripts/marker_server_client_template.py --help
```

Install only the optional surface you need: FastAPI dependencies for `marker_server`, Streamlit dependencies for app launchers, Modal dependencies for cloud deployment, and `marker-pdf[full]` only when non-PDF documents are in scope.
