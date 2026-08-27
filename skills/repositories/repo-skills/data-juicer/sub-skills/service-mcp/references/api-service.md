# API service

## What it is
The Data-Juicer service exposes public functions and selected class methods from installed `data_juicer` modules as HTTP routes.
The bundled script in `scripts/start_api_service.py` must discover modules from the installed package, not from a source checkout.

## Route pattern
- Public functions become `GET /<module-path>/<function>`
- Public class methods become `POST /<module-path>/<ClassName>/<method>`

Examples:
- `GET /data_juicer.core.analyzer/analyze`
- `POST /data_juicer.core.exporter/Exporter/export`

## Request encoding
- Function arguments and method arguments come from the query string.
- Class constructors use the POST body as JSON.
- Values that begin with `<json_dumps>` are decoded as JSON before the call.
- `cfg` may be a JSON string or dict and is converted to initialized config objects.
- If `dataset` is a string path, the service may auto-load it and export the result to the default output location.
- `skip_return=true` suppresses the response body after a successful call.

## Running the service
```bash
uvicorn scripts.start_api_service:app --host 0.0.0.0 --port 8000
```
Or run the bundled script directly if it includes a `__main__` entry.

## Practical advice
- Keep the first call small and explicit.
- Prefer a single function or method route when debugging the transport.
- If a request fails, inspect whether the issue is route shape, JSON encoding, or a missing dependency.
