# Service Authoring Troubleshooting

## Import Target Errors

Symptoms:

- `service.py:MyService` cannot be imported.
- BentoML says the service object must be defined in a module or assigned at module level.
- The target works from one directory but not another.

Fixes:

- Use `module:ServiceObject`, for example `service:Summarization`; the right side must be a module-level decorated service object.
- Run from the project root or pass `--working-dir` to the validator/serve/build command.
- Do not define the service only in a notebook, REPL, local function, or `if __name__ == "__main__"` block.
- Keep filenames import-safe; avoid hyphens in Python module names.
- Validate with `scripts/validate_service_target.py --target service:MyService --working-dir .`.

## Missing Dependencies Inside `bentoml.importing()`

Symptoms:

- Importing `service.py` fails on `torch`, `transformers`, `fastapi`, `gradio`, or another optional runtime package.
- Build/serve import messages mention trying `with bentoml.importing():` for runtime-only modules.

Fixes:

- Put optional imports used only at runtime inside `with bentoml.importing():` or inside `__init__`/hook methods.
- Add missing packages to the local development environment before local validation.
- Add packages to `bentoml.images.Image(...).python_packages(...)` or packaging config before building a Bento.
- Do not hide imports that are required for schema declarations; types used in annotations must still resolve during service import unless postponed annotations and compatible runtime handling are used.

## Invalid API Specs

Symptoms:

- BentoML cannot infer input or output spec.
- OpenAPI generation fails.
- A Pydantic model accepts fields locally but BentoML rejects the endpoint schema.

Fixes:

- Add explicit return annotations to every API and task method.
- Use `pydantic.BaseModel` for structured JSON payloads.
- Use `bentoml.IODescriptor` or `input_spec=` / `output_spec=` when using ML-specific types that Pydantic cannot represent directly.
- Use `Annotated[..., ContentType(...)]`, `Shape(...)`, `DType(...)`, or `DataframeSchema(...)` for file, tensor, and dataframe constraints.
- Avoid unsupported broad unions; use `Optional[T] = None` for nullable values.

## Batch Dimension Mismatch

Symptoms:

- Batchable endpoint returns the wrong number of responses.
- Requests receive another request's output slice.
- Array batching errors mention shape or split dimensions.

Fixes:

- Ensure a batchable API accepts one batched parameter plus optional `bentoml.Context`.
- Return one result per input request for list-like APIs.
- Set `batch_dim=(input_dim, output_dim)` when array input concatenation and output splitting axes differ.
- Use a composite request model when each request has multiple logical fields.
- Start with small `max_batch_size` and assert output lengths in a local unit test.

## Optional Image Or IO Dependency Gaps

Symptoms:

- `PIL`, `numpy`, `pandas`, `torch`, `tensorflow`, `fastapi`, `gradio`, or content-type handling imports fail.
- File, image, tensor, or dataframe endpoints validate locally but fail in the built runtime.

Fixes:

- Include optional packages in both the local dev environment and the Bento runtime image.
- For file uploads, use `pathlib.Path` and `ContentType` validators rather than custom multipart parsing unless ASGI routes are required.
- For images, choose between `PIL.Image.Image` and `Path` with image content type based on whether the API should deserialize into memory or keep uploaded files on disk.
- Keep packaging changes in the packaging sub-skill, but record service-level runtime hints near the service decorator.

## Service Init Side Effects

Symptoms:

- Validation imports download large models, allocate GPUs, start threads, or call external services.
- Tests hang while merely importing `service.py`.
- Multiple workers duplicate a side effect unexpectedly.

Fixes:

- Keep module import side effects minimal.
- Put model loading in `__init__`, not module top-level code.
- Use `@bentoml.on_deployment` for once-per-deployment setup and `@bentoml.on_startup` for per-worker setup.
- Make `__init__` idempotent and safe to run once per worker.
- Avoid network calls during import; use lazy initialization or explicit startup hooks.

## Async Task Misuse

Symptoms:

- A task endpoint errors because it returns a generator or stream.
- A latency-sensitive endpoint is slow because it was made a task.
- Async APIs block health checks or the event loop.

Fixes:

- Use `@bentoml.api` with `Generator`/`AsyncGenerator` for streaming.
- Use `@bentoml.task` only for background job semantics where clients submit and poll/retry/cancel.
- Do not call blocking sync code directly from `async def`; use dependency `.to_async` wrappers or a thread/offload strategy.
- Keep task payloads serializable and schema-backed like normal APIs.

## ASGI, Gradio, And WebSocket Routing Surprises

Symptoms:

- Mounted route appears at a different path than expected.
- WebSocket client cannot connect through BentoML's Python HTTP client.
- Gradio UI imports fail in the runtime image.

Fixes:

- Combine `path_prefix` and mount path when calculating URLs: `path_prefix="/v1"` plus `@bentoml.asgi_app(app, path="/chat")` yields `/v1/chat/...`.
- Use a WebSocket library/client directly; BentoML HTTP clients do not support WebSockets.
- Include `fastapi` and `gradio` in runtime dependencies for Gradio.
- Use `bentoml.get_current_service()` inside ASGI routes declared outside the class.
