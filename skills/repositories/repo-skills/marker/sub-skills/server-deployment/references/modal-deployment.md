# Modal Deployment Reference

Marker includes a Modal deployment example in its source distribution. This skill does not bundle or execute that cloud script because it requires an external account, cloud credentials, network access, GPU runtime, and cost-bearing deployment. Use this page as a self-contained recipe for adapting the pattern safely.

## When to use Modal

Choose Modal when the user needs a hosted GPU-backed endpoint for document conversion and accepts cloud execution. For local development or private filesystem conversion, prefer `marker_server`, `marker_single`, or the Python API instead.

## Reference architecture

The inspected deployment example uses these building blocks:

- A Modal app named for a Marker demo service.
- A Debian slim Python 3.10 image with CUDA-oriented Torch packages plus `marker-pdf[full]`, `fastapi`, `uvicorn`, and `python-multipart`.
- A persistent Modal Volume for Marker model cache reuse.
- A `download_models` function that calls Marker model creation once and commits the volume to reduce first-request latency.
- A class-based service that loads models in `@modal.enter()` so each container reuses loaded models across requests.
- A Modal ASGI app exposing `GET /health` and `POST /convert`.
- A local entrypoint that discovers the deployed endpoint URL, checks health, uploads a PDF, and writes the JSON response locally.

## Hosted API shape from the example

The Modal adaptation is not the same as local `marker_server`:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Reports model-loaded state, model count, and cache status. |
| `POST /convert` | Multipart upload conversion endpoint. |

The example `/convert` form fields are:

- `file`: uploaded document.
- `page_range`: optional page range.
- `force_ocr`: boolean.
- `paginate_output`: boolean.
- `output_format`: `markdown`, `json`, `html`, or `chunks`.
- `use_llm`: boolean for an adapted LLM path; route service setup to `../llm-extraction-services/`.

The response separates `json`, `html`, and `markdown` fields, includes base64 images, metadata, page count, filename, output format, and `success`.

## Deployment flow

Use this flow only after the user authorizes cloud deployment:

```bash
pip install modal
modal setup
# create or adapt a Modal deployment script from the architecture above
modal deploy marker_modal_deployment.py
modal run marker_modal_deployment.py::download_models
modal run marker_modal_deployment.py::invoke_conversion --pdf-file sample.pdf --output-format markdown
```

If the deploy command prints the web endpoint URL, clients can call:

```bash
curl --request POST \
  --url "${BASE_URL}/convert" \
  --form file=@sample.pdf \
  --form output_format=html
```

## Adaptation checklist

- Pick a GPU type, memory limit, and timeout that match expected document size and concurrency.
- Warm the model cache before promising low-latency responses.
- Validate file extensions, request sizes, output formats, and timeouts before conversion.
- Use unique temporary filenames and clean them on both success and failure.
- Return structured errors with HTTP status codes instead of raw tracebacks.
- Add authentication, quotas, logging, and monitoring before exposing the endpoint beyond a trusted test group.
- Keep `local_entrypoint` usage limited to testing an already deployed service; it does not deploy the app by itself.

## Common Modal caveats

- Modal authentication must be configured before deployment commands work.
- A missing or uncommitted model volume can make the first request slow.
- Endpoint URLs are assigned by Modal after deployment; capture the URL from deploy output or discover it through Modal APIs/dashboard.
- The example targets a demo app name and environment; update names deliberately when creating multiple deployments.
- Cloud deployment can incur cost and download model artifacts, so do not run it as a routine skill validation step.
