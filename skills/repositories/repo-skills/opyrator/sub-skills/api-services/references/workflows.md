# API service workflows

This sub-skill is for in-process FastAPI app creation, schema inspection, and service startup.

## 1) Build an app in-process
Use `create_api` when you need the app object itself.

```python
from opyrator import Opyrator
from opyrator.api import create_api

app = create_api(Opyrator("module:function"))
```

Check the resulting app:
- `app.routes` should include `/call`, `/info`, `/`, `/docs`, `/redoc`, and `/openapi.json`
- FastAPI may also add helper routes such as `/docs/oauth2-redirect`; treat them as expected extras
- `app.openapi()["paths"]["/call"]` should have a `post` operation
- `GET /info` should return `{}`
- the `/call` request schema should come from `opyrator.input_type`
- the `/call` 200 response schema should come from `opyrator.output_type`

Do not use `launch_api` when you only need schema or route inspection. `launch_api` starts `uvicorn.run(...)` and blocks.

## 2) Launch a service
CLI launch:

```bash
opyrator launch-api module:function --host 0.0.0.0 --port 8080
```

Python launch helper:

```python
from opyrator.api.fastapi_app import launch_api

launch_api("module:function", port=8501, host="0.0.0.0")
```

Expected signals:
- uvicorn prints an info startup line
- `http://HOST:PORT/docs` shows the Swagger UI
- `http://HOST:PORT/redoc` shows ReDoc
- `/` redirects to `./docs`

Remember:
- CLI default port is `8080`
- direct helper default port is `8501`
- both default host to `0.0.0.0`

## 3) Check relative docs behavior
`patch_fastapi(app)` must be applied before serving. It:
- removes the stock `/docs` and `/redoc` routes
- re-adds them with relative `./openapi.json`
- rewrites the Swagger UI request interceptor so subpath deployments still call the right backend
- adjusts GraphiQL relative-path handling for the older pinned Starlette stack

Use a smoke request pattern like this:

```python
from fastapi.testclient import TestClient

client = TestClient(app)
assert client.get("/", allow_redirects=False).headers["location"] == "./docs"
assert "./openapi.json" in client.get("/docs").text
assert "./openapi.json" in client.get("/redoc").text
```

## 4) Validate schema shapes
A wrapped callable is API-compatible only when:
- its parameter named `input` is type-annotated with a `pydantic.BaseModel`
- its return annotation is a `pydantic.BaseModel` or a `list` of `BaseModel` items

If a callable returns `list[BaseModel]`, the OpenAPI response schema should stay an array schema. Do not flatten it into a single object.

## 5) Use the bundled smoke helper

```bash
python scripts/api_smoke.py
python scripts/api_smoke.py --json
```

Expected:
- route summary
- OpenAPI title and path list
- `/call` request and response refs
- redirect and docs-relative URL checks when `TestClient` is available

## Route elsewhere
If the ask is about CLI call/export/deploy or about wrapping raw callables into Opyrators, use `../wrapping-and-cli/SKILL.md`.
If the ask is about Streamlit UI or file/component rendering, use `../ui-and-components/SKILL.md`.
