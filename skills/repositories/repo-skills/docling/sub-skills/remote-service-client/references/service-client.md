# Docling Service Client SDK

## Install And Imports

Use the service-client extra when the environment is slim or remote-only:

```sh
pip install "docling-slim[service-client]"
```

Common imports:

```python
from docling.service_client import DoclingServiceClient, StatusWatcherKind
from docling.datamodel.service.options import ConvertDocumentsOptions
from docling.datamodel.service.targets import InBodyTarget, PresignedUrlTarget, S3Target, ZipTarget
from docling.datamodel.service.requests import HttpSourceRequest, S3SourceRequest
```

`DoclingServiceClient` accepts `url`, optional `api_key`, default `options`, `status_watcher`, websocket fallback, polling cadence, `job_timeout`, `max_concurrency`, HTTP retry/connect/read timeouts, artifact download timeout, and artifact byte limit. The client sends `X-Api-Key` when an API key is supplied. Do not include `/v1` in the base URL; the client appends versioned paths itself.

## High-Level Conversion

Use `convert()` for one source and `convert_all()` for many sources. Sources can be a local `Path`, an HTTP/HTTPS URL string, a `DocumentStream`, or an explicit HTTP source request model.

```python
from pathlib import Path
from docling.service_client import DoclingServiceClient
from docling.datamodel.service.options import ConvertDocumentsOptions

options = ConvertDocumentsOptions(to_formats=["md"], do_ocr=True)

with DoclingServiceClient(url=service_url, api_key=api_key) as client:
    result = client.convert(source=Path("report.pdf"), options=options)
    print(result.status)
    print(result.document.export_to_markdown())

    for item in client.convert_all(
        source=[Path("a.pdf"), "https://example.com/b.pdf"],
        options=options,
        max_concurrency=4,
    ):
        print(item.input.file.name, item.status)
```

`convert()` raises `ConversionError` by default when the resulting status is not success or partial success. Pass `raises_on_error=False` when you want to inspect failed `ConversionResult` objects yourself. `convert_all()` streams results while honoring a concurrency cap; invalid `max_concurrency` values outside the supported range are rejected.

## Options And Limits

`ConvertDocumentsOptions` carries the service conversion options: input and output formats, OCR, table structure, pipeline selection, page ranges, enrichment flags, timeout controls, image export mode, and abort-on-error behavior. `convert()` and `convert_all()` also accept `max_num_pages`, `max_file_size`, and `page_range`; these are resolved into request limits before submission.

Use string enum values when helpful (`"pdf"`, `"md"`, `"standard"`) or import typed enums from Docling datamodels. Common output format values include `md`, `json`, `html`, `text`, `doctags`, `vtt`, and `doclang`.

## Task Jobs

Use `submit()` when you need a long-lived task handle instead of blocking until conversion completes.

```python
from docling.service_client import DoclingServiceClient, StatusWatcherKind
from docling.datamodel.service.targets import InBodyTarget

with DoclingServiceClient(
    url=service_url,
    api_key=api_key,
    status_watcher=StatusWatcherKind.POLLING,
    job_timeout=600,
) as client:
    job = client.submit("https://example.com/report.pdf", target=InBodyTarget())
    for update in job.watch(timeout=600):
        print(update.task_status, update.task_position)
    result = job.result(timeout=600)
```

A `ConversionJob` exposes `task_id`, `submitted_at`, `status`, `queue_position`, `done`, `poll(wait=...)`, `watch(timeout=...)`, and `result(timeout=...)`. Websocket watching is the default; polling is available and websocket fallback to polling is enabled by default.

## Result Targets

If no target is specified, `submit()` first tries `PresignedUrlTarget()` and falls back to `InBodyTarget()` when the service does not support presigned artifact storage. Explicit targets include:

- `InBodyTarget()` for JSON response content in the result body.
- `ZipTarget()` for a raw zip payload returned as `RawServiceResult`.
- `PresignedUrlTarget()` for per-document artifact references.
- `S3Target(...)` for batch output to object storage when the service is configured for it.

For presigned artifacts, the client downloads result artifacts during high-level materialization. Public artifact URLs are required by default; private, loopback, or internal artifact URLs are blocked to reduce SSRF risk. Do not disable that guard unless the user explicitly controls both the service and artifact store and understands the network boundary.

## Batch And Fan-Out

Use `submit_and_retrieve_each()` for many independently submitted conversion items with bounded in-flight tasks:

```python
from docling.service_client import ConversionItem, DoclingServiceClient
from docling.datamodel.service.options import ConvertDocumentsOptions

items = [
    ConversionItem(source="https://example.com/a.pdf"),
    ConversionItem(source="https://example.com/b.pdf", options=ConvertDocumentsOptions(to_formats=["json"])),
]

with DoclingServiceClient(url=service_url, api_key=api_key) as client:
    for item, outcome in client.submit_and_retrieve_each(items, max_in_flight=4, ordered=False):
        if isinstance(outcome, Exception):
            print("failed", item.source, outcome)
        else:
            print("done", item.source, outcome.status)
```

`submit_batch()` is for service-side batch requests over HTTP or S3 source request models with an S3 or presigned target. It returns a task job, so poll or watch it before fetching the result.

## Chunk Endpoints

Use `chunk()` for retrieval-ready chunks from one source, or `submit_chunk()` when you need task lifecycle control.

```python
from docling.service_client import ChunkerKind, DoclingServiceClient

with DoclingServiceClient(url=service_url, api_key=api_key) as client:
    response = client.chunk("https://example.com/report.pdf", chunker=ChunkerKind.HYBRID)
    for chunk in response.chunks:
        print(chunk.chunk_index, chunk.text[:120])
```

The chunk response includes chunk text, optional raw text, token count, headings, captions, doc item references, page numbers, metadata, converted documents when requested by the service, and processing time.

## Async Client

Use `AsyncDoclingServiceClient` for native async programs. It mirrors the sync client surface for task submission, batch submission, chunking, health, version, and async job handles.

```python
from docling.service_client import AsyncDoclingServiceClient

async with AsyncDoclingServiceClient(url=service_url, api_key=api_key) as client:
    job = await client.submit("https://example.com/report.pdf")
    result = await job.result(timeout=300)
```

Do not call sync batch APIs from inside an already-running event loop; use the async client instead.

## Response Datamodels

Important service response models include:

- `HealthCheckResponse(status="ok")` and `/version` JSON for preflight service checks.
- `ConvertDocumentResponse` for inline conversion results.
- `PresignedUrlConvertResponse` with per-document artifact references.
- `ChunkDocumentResponse` with `chunks`, `documents`, and `processing_time`.
- `TaskStatusResponse` with `task_id`, `task_type`, `task_status`, `task_position`, and `task_meta`.
- `TaskFailureResult` and `PublicFailureInfo` for categorized task failures.

Handle response schema mismatch as a likely client/server version skew; upgrade the client or service together.
