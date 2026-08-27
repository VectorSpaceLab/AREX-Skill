# `docling convert-remote`

`docling convert-remote` converts through a remote `docling-serve` service instead of running conversion locally. It uses the synchronous `DoclingServiceClient` internally and writes local outputs with the same exporter as `docling convert`.

## Install And Credentials

Install the service-client extra when needed:

```sh
pip install "docling-slim[service-client]"
```

Authentication precedence is flag, then environment variable, then a `.env` file in the current working directory:

```sh
export DOCLING_SERVICE_URL="https://docling.example.com"
export DOCLING_SERVICE_API_KEY="optional-key"
```

`DOCLING_SERVICE_URL` is required unless `--service-url` is passed. `DOCLING_SERVICE_API_KEY` is optional unless the service requires authentication.

## Basic Usage

```sh
docling convert-remote report.pdf

docling convert-remote \
  --service-url https://docling.example.com \
  --api-key "$DOCLING_SERVICE_API_KEY" \
  --to md --to json \
  --output ./out \
  report.pdf

docling convert-remote \
  --from pdf --from docx \
  --no-ocr \
  --output ./out \
  ./inbox
```

Sources can be local files, local directories, or HTTP/HTTPS URLs. Local directories are walked and filtered by `--from`; HTTP/HTTPS sources remain URLs and are sent to the service rather than downloaded by the CLI.

## Remote-Supported Options

The remote command intentionally exposes only options the service honors. Local execution options such as device selection, thread count, PDF backend internals, and debug visualizers do not apply to remote conversion.

Common flags:

- `--service-url` and `--api-key` for credentials.
- `--from` for accepted input formats and directory filtering.
- `--to` for requested output formats; default is Markdown.
- `--ocr/--no-ocr`, `--force-ocr`, `--tables/--no-tables`, and `--ocr-lang` for OCR/table behavior.
- `--pipeline` for service-side processing pipeline selection, such as `standard`, `legacy`, `vlm`, or `asr` when the service supports it.
- Enrichment flags for code, formula, picture classification, picture description, and chart extraction.
- `--image-export-mode` for image handling in JSON, YAML, HTML, and Markdown outputs.
- `--page-range START-END` or `--page-range PAGE` for page-limited conversion.
- `--document-timeout` for server-side per-document processing time.
- `--abort-on-error/--no-abort-on-error` for batch behavior.
- `--max-concurrency` for client-side concurrent remote conversions.
- `--timeout` for client-side waiting on each job.
- `--watcher websocket|polling` for status tracking.
- `--output` for the local output directory.
- `-v` or `-vv` for logging verbosity.

## Output Behavior

The service performs conversion and the CLI writes requested formats locally. Requested output formats are mapped into the same local export path used by the local CLI, so filenames and supported output types should match local conversion behavior.

If `--image-export-mode` is not set, the service/datamodel default applies. If multiple `--to` formats are supplied, each requested output is written locally when the conversion succeeds.

## Exit Codes

- `0`: success.
- `1`: runtime or connection failure, including unreachable service, missing input path, conversion failure, or health-check failure.
- `2`: usage/configuration error, including no resolved service URL.

## Remote CLI Checklist

Before running real conversion:

1. Confirm `DOCLING_SERVICE_URL` or `--service-url` is set and does not include a trailing `/v1` path.
2. Confirm whether the service requires an API key and avoid printing it.
3. Run `scripts/check_service_config.py` without `--ping` for no-network validation.
4. If the user authorizes network access, run `scripts/check_service_config.py --ping` to call `/health` only; this does not upload documents.
5. Choose `--watcher polling` if websocket traffic is blocked by proxies or firewalls.
6. Increase `--timeout` and optionally `--document-timeout` for large, OCR-heavy, VLM, ASR, or queue-delayed jobs.

## Service API Context

A typical `docling-serve` base URL exposes interactive OpenAPI docs at `/docs`, health at `/health`, version at `/version`, convert endpoints under `/v1/convert/...`, status polling under `/v1/status/poll/{task_id}`, websocket status under `/v1/status/ws/{task_id}`, and result fetching under `/v1/result/{task_id}`. Prefer the Python client or CLI unless the task explicitly needs raw REST calls.
