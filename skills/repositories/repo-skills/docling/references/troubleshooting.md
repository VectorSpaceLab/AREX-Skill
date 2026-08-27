# Cross-Cutting Troubleshooting

Use this reference for failures that span multiple Docling workflows. For workflow-specific details, continue into the owning sub-skill's `references/troubleshooting.md`.

## Import or Install Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: typer` or `rich` from CLI import | `docling-slim` installed without CLI extra | Install full `docling` or `docling-slim[cli]`. |
| Converter import fails on model-related modules | Local pipeline modules import Torch/Torchvision/model foundations | Use full `docling` or add the relevant model/local extras; for inspection-only environments CPU Torch is sufficient. |
| `pip check` reports conflicts | Mixed extras or old transitive dependencies | Recreate a clean environment and install only needed extras; avoid piling broad extras onto a stale env. |
| Python version is unsupported | Runtime not in `>=3.10,<4.0` | Use a supported Python version such as 3.10, 3.11, or 3.12 unless package metadata changes. |

## Optional Backend Failures

- OCR engines can require Python packages, model artifacts, or external binaries. Route OCR/table tuning to `sub-skills/pipeline-configuration/`.
- VLM and enrichment workflows can require Torch, Transformers, MLX, GPU drivers, local model downloads, or remote API endpoints. Route them to `sub-skills/advanced-pipelines/`.
- ASR requires `docling[asr]` and a system `ffmpeg` executable for common audio/video formats.
- HTML rendering requires the `htmlrender` extra and Playwright/browser setup.
- XBRL requires the XBRL extra; do not include it in minimal environments unless needed.

## Remote Service Boundaries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OperationNotAllowed` while using a remote model option | Pipeline remote calls are gated | Set `enable_remote_services=True` only after confirming data may leave the local process. |
| `docling convert-remote` says no service URL | Missing `--service-url` / `DOCLING_SERVICE_URL` | Use `remote-service-client` preflight before uploading documents. |
| Timeout or websocket errors | Service not reachable, long-running job, or watcher issue | Validate URL/API key, use polling fallback, tune client and document timeouts. |
| Auth or quota failure | Missing/invalid API key or service-side quota | Confirm `DOCLING_SERVICE_API_KEY` and service policy; do not retry blindly with documents. |

## Empty or Low-Quality Outputs

- Check whether OCR was disabled, an unsupported format was forced, or the document is scanned/image-heavy.
- For PDF table issues, tune `do_table_structure`, `TableFormerMode`, and `do_cell_matching` in `pipeline-configuration`.
- For text-heavy pages with hallucinated VLM text, use `advanced-pipelines` and consider `force_backend_text=True` through the Python API.
- For JSON validation or table export issues, use `document-outputs` and check the `docling-core` version against the exported JSON schema.

## Repository Editing Failures

- If changing CLI flags, update docs generation paths and focused CLI tests; route to `repo-maintenance`.
- If changing conversion outputs intentionally, regenerate and review reference data carefully.
- Run targeted tests first, then `make validate` before considering repository edits complete.
