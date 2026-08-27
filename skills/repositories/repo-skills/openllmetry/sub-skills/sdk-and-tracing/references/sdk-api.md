# SDK API surface

This file captures the public Traceloop SDK entry points that matter for initialization, offline tracing, decorator workflows, manual LLM spans, and the client-facing prompt/dataset/experiment/guardrail surfaces.

## Install and import checks

Base import checks:

```python
import traceloop.sdk
from traceloop.sdk import Traceloop
from traceloop.sdk.instruments import Instruments
from traceloop.sdk.decorators import workflow, task, agent, tool, conversation, guardrail
from traceloop.sdk.tracing.manual import track_llm_call, LLMMessage, LLMUsage
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
```

Install choices:
- `traceloop-sdk` for the core runtime
- `traceloop-sdk[datasets]` when you need `Datasets.from_dataframe()` / pandas-backed dataset helpers

## Tracing bootstrap

### `Traceloop.init`

```python
Traceloop.init(
    app_name: str = sys.argv[0],
    api_endpoint: str = "https://api.traceloop.com",
    api_key: Optional[str] = None,
    enabled: bool = True,
    headers: Dict[str, str] = {},
    disable_batch=False,
    telemetry_enabled: bool = True,
    exporter: Optional[SpanExporter] = None,
    metrics_exporter: MetricExporter = None,
    metrics_headers: Dict[str, str] = None,
    logging_exporter: LogExporter = None,
    logging_headers: Dict[str, str] = None,
    processor: Optional[Union[SpanProcessor, List[SpanProcessor]]] = None,
    propagator: TextMapPropagator = None,
    sampler: Optional[Sampler] = None,
    traceloop_sync_enabled: bool = False,
    should_enrich_metrics: bool = True,
    resource_attributes: dict = {},
    instruments: Optional[Set[Instruments]] = None,
    block_instruments: Optional[Set[Instruments]] = None,
    image_uploader: Optional[ImageUploader] = None,
    span_postprocess_callback: Optional[Callable[[ReadableSpan], None]] = None,
    endpoint_is_traceloop: Optional[bool] = False,
    use_attributes: Optional[bool] = None,
    use_legacy_attributes: Optional[bool] = None,
) -> Optional[Client]
```

Key behavior:
- `enabled=False` disables tracing entirely.
- `TRACELOOP_BASE_URL`, `TRACELOOP_API_KEY`, `TRACELOOP_HEADERS`, `TRACELOOP_METRICS_ENDPOINT`, `TRACELOOP_METRICS_HEADERS`, `TRACELOOP_LOGGING_ENDPOINT`, and `TRACELOOP_LOGGING_HEADERS` override the matching arguments.
- `headers` and `resource_attributes` use mutable `{}` defaults in the signature; pass your own dicts if you intend to mutate them later.
- `use_attributes` defaults to `True` when omitted.
- `use_legacy_attributes` is a deprecated alias for `use_attributes`; passing both raises `TypeError`.
- If both `exporter` and `processor` are provided, the exporter is ignored and a warning is emitted.
- If no custom exporter/processor is provided and the endpoint is the Traceloop cloud path, the method may return a `Client` singleton; otherwise it returns `None`.

Endpoint schemes for `api_endpoint`:
- `http://` / `https://` → OTLP HTTP exporter, appended with `/v1/traces` if needed
- `grpc://` → insecure OTLP gRPC exporter
- `grpcs://` → secure OTLP gRPC exporter
- no scheme → insecure OTLP gRPC exporter for backward compatibility

### `Traceloop.get_default_span_processor`

```python
Traceloop.get_default_span_processor(
    disable_batch: bool = False,
    api_endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    exporter: Optional[SpanExporter] = None,
) -> SpanProcessor
```

Notes:
- `disable_batch=True` forces `SimpleSpanProcessor`; otherwise `BatchSpanProcessor` is used unless notebook detection forces simple mode.
- The returned processor is marked with `_traceloop_processor = True` and already has the Traceloop span-on-start hook attached.
- Use this when you want a default Traceloop processor plus one or more custom processors in the `processor=[...]` list.

### `Traceloop.get`

```python
Traceloop.get() -> Client
```

Notes:
- Returns the shared client singleton.
- Raises if `Traceloop.init()` has not created the client.
- Use `Client(...)` directly if you need multiple client instances.

### Association and prompt helpers

```python
Traceloop.set_association_properties(properties: dict) -> None
Traceloop.set_prompt(template: str, variables: dict, version: int)
```

Notes:
- `set_association_properties` writes association metadata into the current context and current workflow/task span when one is active.
- `set_prompt` is the prompt-tracing helper used by the workflow tests; it attaches prompt template metadata to the current LLM span.
- `Traceloop.get().associations.set([...])` is the object-oriented association helper; see below.

## Decorators

### Workflow/task/agent/tool/conversation

```python
workflow(name: Optional[str] = None, version: Optional[int] = None, method_name: Optional[str] = None, tlp_span_kind=WORKFLOW)

task(name: Optional[str] = None, version: Optional[int] = None, method_name: Optional[str] = None, tlp_span_kind=TASK)

agent(name: Optional[str] = None, version: Optional[int] = None, method_name: Optional[str] = None)

tool(name: Optional[str] = None, version: Optional[int] = None, method_name: Optional[str] = None)

conversation(conversation_id: str)
```

Behavior notes:
- `workflow` and `task` work on sync functions, async functions, generators, and async generators.
- `agent` is the `workflow` specialization with span kind `agent`.
- `tool` is the `task` specialization with span kind `tool`.
- Class decoration uses `method_name=...` to wrap a named method.
- Entity spans are named `entity_name.kind`, for example `offline_workflow.workflow`.
- `conversation` scopes a conversation ID to all spans created inside the decorated call.

Deprecated async aliases still exist in source (`@atask`, `@aworkflow`, `@aagent`, `@atool`), but the current preferred path is the sync decorator family above.

### Guardrail decorator

```python
guardrail(*guards, input_mapper=None, on_failure=None, name="")
```

Notes:
- Wraps the `Guardrails` class API.
- Supports sync and async wrapped functions.
- Use it when you want guard execution to be attached directly to a callable instead of manually constructing a `Guardrails` object.

## Manual LLM spans

### `track_llm_call` and models

```python
track_llm_call(vendor: str, type: str)

LLMMessage(*, role: str, content: str) -> None
LLMUsage(*, prompt_tokens: int, completion_tokens: int, total_tokens: int, cache_creation_input_tokens: Optional[int] = None, cache_read_input_tokens: Optional[int] = None) -> None
```

The context manager yields an `LLMSpan` with:
- `report_request(model: str, messages: list[LLMMessage])`
- `report_response(model: str, completions: list[str])`
- `report_usage(usage: LLMUsage)`

Use manual spans when you want no-network reporting but still need `gen_ai.*` request/response/usage attributes.

## Client surfaces

### `Client`

```python
Client(api_key: str, app_name: str = sys.argv[0], api_endpoint: str = "https://api.traceloop.com")
```

The client exposes:
- `user_feedback`
- `datasets`
- `experiment`
- `associations`

Caveats:
- `api_key` is required and cannot be blank.
- `Traceloop.get()` returns the singleton client only after `Traceloop.init()` has created it.
- `Client` is the right path when you need multiple API clients with different endpoints or keys.

### `UserFeedback`

```python
Client.user_feedback.create(annotation_task: str, entity_id: str, tags: Dict[str, Any]) -> None
```

Notes:
- `annotation_task`, `entity_id`, and `tags` are required.
- Intended for Traceloop annotation/user-feedback flows.

### `Datasets`

Public helpers:
- `get_all()`
- `get_by_slug(slug)`
- `create(dataset_request)`
- `override(slug, override_request)`
- `delete_by_slug(slug)`
- `from_csv(file_path, slug, name=None, description=None)`
- `from_dataframe(df, slug, name=None, description=None)`
- `get_version_csv(slug, version)`
- `get_version_jsonl(slug, version)`

Notes:
- `from_dataframe` requires the `datasets` extra / pandas.
- `create` and `override` support attachment objects.

### `Dataset`

Public helpers:
- `publish()`
- `add_rows(rows)`
- `add_column(slug, name, col_type)`

### `Experiment`

Constructor:

```python
Experiment(http_client, async_http_client, experiment_slug)
```

Public helpers:
- `run(...)`
- `run_in_github(...)`

Notes:
- `run` is async.
- `run_in_github` only works in GitHub Actions pull_request context.
- `TRACELOOP_EXP_SLUG` seeds the default experiment slug.

### `Guardrails`

Constructor:

```python
Guardrails(*guards, on_failure="raise", name="", run_all=False, parallel=True)
```

Builder helpers:
- `parallel()`
- `sequential()`
- `run_all()`
- `fail_fast()`
- `raise_on_failure()`
- `log_on_failure()`
- `ignore_on_failure()`
- `on_failure(handler)`
- `named(name)`

Execution helpers:
- `run(func_to_guard, *args, input_mapper=None, **kwargs)`
- `validate(guard_inputs, on_failure=None)`

### Prompt registry helper

```python
get_prompt(key, **args)
PromptRegistryClient.render_prompt(key, version=None, version_name=None, version_hash=None, variables={})
```

Notes:
- Prompt rendering is client-side and Jinja2-based.
- The prompt registry must already contain the requested prompt.

### Association helpers

```python
AssociationProperty.CUSTOMER_ID
AssociationProperty.USER_ID
AssociationProperty.SESSION_ID
Associations.set([(AssociationProperty.USER_ID, "user-123")])
```

Notes:
- `Associations.set()` is a convenience wrapper that forwards to `Traceloop.set_association_properties()`.

## Environment toggles

| Helper | Environment variable | Default | Effect |
| --- | --- | --- | --- |
| `is_tracing_enabled()` | `TRACELOOP_TRACING_ENABLED` | `true` | Gates tracing bootstrap |
| `is_content_tracing_enabled()` | `TRACELOOP_TRACE_CONTENT` | `true` | Gates decorated inputs/outputs and content-bearing span attributes |
| `is_metrics_enabled()` | `TRACELOOP_METRICS_ENABLED` | `true` | Gates metrics export |
| `is_logging_enabled()` | `TRACELOOP_LOGGING_ENABLED` | `false` | Gates log export |

Other useful init-time variables:
- `TRACELOOP_HEADERS`
- `TRACELOOP_METRICS_HEADERS`
- `TRACELOOP_LOGGING_HEADERS`
- `TRACELOOP_SUPPRESS_WARNINGS`
- `TRACELOOP_PROMPT_MANAGER_MAX_RETRIES`
- `TRACELOOP_PROMPT_MANAGER_POLLING_INTERVAL`

## What to hand off elsewhere

- Exact GenAI/span-attribute values and semantic-convention migrations belong in `../../semantic-conventions/SKILL.md`.
- Provider/vector/framework wrapper internals and `Instruments` category routing belong in `../../instrumentations/SKILL.md`.
- Nx/uv commands and VCR policy belong in `../../repo-development/SKILL.md`.
