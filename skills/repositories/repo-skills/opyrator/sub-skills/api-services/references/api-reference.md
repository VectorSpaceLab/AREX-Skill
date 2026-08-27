# API reference

## Core helpers

| Symbol | Signature | What it does | Important behavior |
| --- | --- | --- | --- |
| `create_api` | `create_api(opyrator: Opyrator) -> FastAPI` | Builds a FastAPI app from a validated `Opyrator`. | Title comes from `opyrator.name`; the helper appends ` - Opyrator` when the name does not already contain `opyrator`. Description comes from the wrapped function docstring. The helper only sets title and description, so the OpenAPI version stays at FastAPI's default unless the caller changes it. |
| `launch_api` | `launch_api(opyrator_path: str, port: int = 8501, host: str = '0.0.0.0') -> None` | Resolves the callable string, builds the app, and starts `uvicorn.run(...)`. | Blocking server launch. Do not use it when you only need the app object for tests or schema inspection. |
| `patch_fastapi` | `patch_fastapi(app: FastAPI) -> None` | Patches FastAPI docs routes for relative deployment. | Removes the stock `/docs` and `/redoc` handlers, re-adds them with relative `./openapi.json`, and adjusts the Swagger UI request interceptor and GraphiQL path handling. |

## Route map

| Route | Method | Response model | Purpose | Expected signal |
| --- | --- | --- | --- | --- |
| `/call` | `POST` | `opyrator.output_type` | Execute the wrapped callable. | Request validation uses the `input` type; bad input should return `422`. |
| `/info` | `GET` | `Dict` | Return metadata. | The handler currently returns `{}`. |
| `/` | `GET` | none | Redirect to docs. | Redirect target is `./docs` and is excluded from the OpenAPI schema. |
| `/docs` | `GET` | HTML docs page | Swagger UI. | HTML should point to `./openapi.json`. |
| `/redoc` | `GET` | HTML docs page | ReDoc. | HTML should point to `./openapi.json`. |
| `/openapi.json` | `GET` | OpenAPI document | Schema source for the service. | `app.openapi()` and this route should describe the same API. |

## CORS defaults
`create_api` installs `CORSMiddleware` with:
- `allow_origins=["*"]`
- `allow_credentials=True`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

## Schema rules
- `Opyrator.input_type` and `Opyrator.output_type` come from the callable type hints.
- The wrapped callable must have a parameter named `input`.
- The `input` parameter must be a Pydantic model, or a list of Pydantic models.
- The return type must be a Pydantic model, or a list of Pydantic models.
- A plain `BaseModel` return becomes an object schema.
- A root model that wraps a list remains an array-shaped schema.
- A direct `list[BaseModel]` return is also preserved as an array schema.

## Service startup defaults
- Direct Python helper: `port=8501`, `host="0.0.0.0"`
- CLI wrapper: `--port 8080`, `--host 0.0.0.0`
- Both launches are blocking and print uvicorn startup logs.

## Usage pattern
1. Create or import a callable with a valid `input` annotation and Pydantic output type.
2. Wrap it with `Opyrator`.
3. Call `create_api(...)` if you need an app object.
4. Call `launch_api(...)` or `opyrator launch-api ...` only when you want to serve the app.
5. Use `app.openapi()` or `/openapi.json` to inspect the schema.

## Examples to keep in mind
- A hello-world wrapper should show an `Input` request model and an `Output` response model.
- A question-answering wrapper should show a custom output schema, not a raw dict.
- A callable returning a list of models should expose an array schema in OpenAPI.
