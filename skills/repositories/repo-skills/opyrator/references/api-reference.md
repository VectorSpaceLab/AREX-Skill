# API Reference

## Purpose

Read this when you need the verified public surface of Opyrator itself before dropping into a narrower sub-skill.

## Core callable wrapper

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `Opyrator` | `Opyrator(func: Union[Callable, str]) -> None` | Accepts either a callable object or an import string. Rejects uninitialized classes. |
| `Opyrator.__call__` | `Opyrator.__call__(self, input: Any, **kwargs: Any) -> Any` | Accepts a Pydantic model, a `dict`, or a JSON string. |
| `name_to_title` | `name_to_title(name: str) -> str` | Converts `hello_world` to `Hello World`. |
| `get_callable` | `get_callable(import_string: str) -> Callable` | Prefers `module:callable` and falls back to `module.callable`. |
| `get_input_type` | `get_input_type(func: Callable) -> Type` | Requires an annotated parameter named exactly `input`. |
| `get_output_type` | `get_output_type(func: Callable) -> Type` | Requires an annotated return type. |
| `is_compatible_type` | `is_compatible_type(type: Type) -> bool` | Accepts `BaseModel` subclasses and lists of `BaseModel` items. |

## Service helpers

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `create_api` | `create_api(opyrator: Opyrator) -> FastAPI` | Builds the app object, applies the relative-docs patch, installs CORS, and defines `/call` and `/info`. |
| `launch_api` | `launch_api(opyrator_path: str, port: int = 8501, host: str = '0.0.0.0') -> None` | Starts `uvicorn.run(...)` and blocks. |
| `patch_fastapi` | `patch_fastapi(app: FastAPI) -> None` | Rewrites the docs routes so relative `/docs` and `/redoc` work under subpaths. |
| `as_form` | `as_form(cls: Type[pydantic.main.BaseModel]) -> Any` | Adds a FastAPI `as_form` helper to a Pydantic model. |

## UI and component helpers

| Symbol | Verified signature | Notes |
| --- | --- | --- |
| `launch_ui` | `launch_ui(opyrator_path: str, port: int = 8501) -> None` | Starts a temporary Streamlit runner and launches the UI server. |
| `render_streamlit_ui` | `render_streamlit_ui(opyrator: opyrator.core.Opyrator) -> None` | Renders the generated UI inside a Streamlit runtime. |
| `FileContent.validate` | `FileContent.validate(value: Any) -> 'FileContent'` | Base64-encodes bytes-like values or wraps strings. |
| `FileContent.as_bytes` | `FileContent.as_bytes(self) -> bytes` | Decodes base64 to raw bytes. |
| `FileContent.as_str` | `FileContent.as_str(self) -> str` | Decodes bytes as UTF-8 text. |
| `ClassificationOutput.render_output_ui` | `ClassificationOutput.render_output_ui(self, streamlit) -> None` | Renders a Plotly bar chart for scored labels. |

## CLI commands

Verified `opyrator --help` exposes these commands:

- `call`
- `deploy`
- `export`
- `launch-api`
- `launch-ui`

The wrapping sub-skill owns the local `call` / `export` / `deploy` behavior. The API and UI sub-skills own the launch commands.

## Important runtime facts

- `create_api` returns a FastAPI app without starting a server.
- The `/call` route uses the wrapped callable's `input` type for request validation and its return type for `response_model`.
- `/info` currently returns `{}`.
- `export` and `deploy` are placeholder commands in this snapshot.
- `FileContent` is the bridge between JSON/OpenAPI and media/file widgets in the UI.

## Where to go next

- Callable wrapping, CLI calls, and WIP export/deploy: [`../sub-skills/wrapping-and-cli/SKILL.md`](../sub-skills/wrapping-and-cli/SKILL.md)
- FastAPI service and OpenAPI inspection: [`../sub-skills/api-services/SKILL.md`](../sub-skills/api-services/SKILL.md)
- Streamlit UI and component rendering: [`../sub-skills/ui-and-components/SKILL.md`](../sub-skills/ui-and-components/SKILL.md)
