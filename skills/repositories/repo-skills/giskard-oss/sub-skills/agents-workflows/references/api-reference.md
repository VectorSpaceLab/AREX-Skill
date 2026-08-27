# giskard.agents API reference

## Purpose

Use this reference for public `giskard.agents` classes, constructors, async
methods, and ownership rules. Examples and recipes live in
[workflows.md](workflows.md); failures live in
[troubleshooting.md](troubleshooting.md).

The package requires Python 3.12+. Import the public namespace as:

```python
import giskard.agents as agents
```

## Architectural ownership

| Layer | Owns | Must not own |
| --- | --- | --- |
| `ChatWorkflow` / `Chat` | Message ordering, template rendering, tool execution loop, structured-output validation, error policy. | Provider SDK imports, API keys, wire-format translation. |
| `Tool` / `@tool` | Function schema extraction, argument coercion, context injection, execution, output serialization to `str`, optional error catching. | Provider calls or provider-specific message formats. |
| `BaseGenerator` subclasses | Completion calls, provider/wire serialization and deserialization, middleware pipeline. | User workflow state or tool business logic. |
| `giskard.llm` provider layer | Provider aliases, SDKs, credentials, native completions/embeddings/responses. | Eval scenario semantics or workflow business logic. |

Provider configuration and credential checks belong in
[llm-providers](../../llm-providers/SKILL.md). Evaluation scenarios and checks
belong in [checks-evals](../../checks-evals/SKILL.md).

## Public root exports

`giskard.agents` exports these core names:

| Name | Use |
| --- | --- |
| `Generator` | Default chat generator alias to `GiskardLLMGenerator`; construct with `Generator(model="provider/model")`. |
| `BaseGenerator` | Abstract/provider-adapter base. Subclass it for no-provider tests or new provider adapters. |
| `ChatWorkflow` | Provider-agnostic async workflow for messages, templates, tools, structured outputs, and error handling. |
| `TemplateReference` | Workflow step that loads a template file through a `PromptsManager`. |
| `Chat` | Result object with messages, context, `last`, `transcript`, `output`, `failed`, and `error`. |
| `Tool`, `tool` | Tool model and decorator. |
| `MessageTemplate` | Inline Jinja2 message template. |
| `set_prompts_path`, `set_default_prompts_path`, `add_prompts_path`, `remove_prompts_path`, `get_prompts_manager` | Global prompt-path manager helpers. |
| `RunContext` | Per-run state available to tools and to the returned chat. |
| `ErrorPolicy`, `WorkflowError`, `ModelRefusalError`, `Error`, `StepType` | Workflow error and step model types. |
| `BaseEmbeddingModel`, `EmbeddingModel` | Async embedding wrapper and default embedding model alias. |

## Generator API

Verified constructor and helper surface:

```python
agents.Generator(
    *,
    model: str,
    params=GenerationParams(),
    retry_policy=RetryPolicy(),
    rate_limiter=None,
    middlewares=[],
)
```

`Generator` is the public alias for `GiskardLLMGenerator`, which delegates to
`giskard.llm.acompletion`. The model string usually follows `provider/model`
syntax, for example `openai/gpt-4o-mini` or `google/gemini-...`; see
[llm-providers](../../llm-providers/SKILL.md) for provider support and setup.

Important methods and data types:

| API | Notes |
| --- | --- |
| `BaseGenerator.complete(messages, params=None, metadata=None)` | Async completion over `ChatMessage` objects or message dicts. Builds the retry/rate-limit/custom middleware chain then calls `_call_model`. |
| `BaseGenerator.batch_complete(messages, params=None, metadata=None)` | Runs multiple completion requests concurrently. |
| `BaseGenerator.chat(message, role="user", as_template=False)` | Creates a new `ChatWorkflow` with an initial message. Plain strings are literal unless `as_template=True`. |
| `BaseGenerator.template(template_name)` | Creates a new `ChatWorkflow` starting from a file template reference. |
| `BaseGenerator.with_params(**kwargs)` | Returns a copy with updated `GenerationParams`; scalar fields replace previous values and tools merge at completion time. |
| `BaseGenerator.with_retries(max_attempts, base_delay=None, max_delay=None)` | Returns a copy with a `RetryPolicy`. |
| `BaseGenerator.with_rate_limiter(rate_limiter_or_id)` | Returns a copy using a `BaseRateLimiter` instance or a registered limiter id. |
| `GenerationParams(temperature=1.0, max_tokens=None, response_format=None, tools=[], timeout=None)` | Per-generator or per-call completion parameters. `response_format` is set from workflow structured output. |

### Adding a generator backend

Subclass `BaseGenerator` and implement only `_call_model(messages, params,
metadata=None)`. That method receives internal `ChatMessage` and `Tool` objects
and returns a `CompletionResponse`. If the generator must be serializable through
Giskard's discriminated model registry, decorate the class with
`@BaseGenerator.register("stable_kind")`.

Do not import provider SDKs, call provider APIs, or transform provider wire
formats from `ChatWorkflow`, `Chat`, or `Tool` code.

## ChatWorkflow API

Verified constructor shape:

```python
agents.ChatWorkflow(
    *,
    generator,
    messages=[],
    tools={},
    inputs={},
    output_model=None,
    output_model_strict=True,
    output_model_num_retries=2,
    prompt_manager=...,  # defaults to global prompts manager
    context=agents.RunContext(),
    error_policy=agents.ErrorPolicy.RAISE,
)
```

Main workflow methods:

| API | Notes |
| --- | --- |
| `.chat(message, role="user", as_template=False)` | Adds a literal message, message dict/object, or inline `MessageTemplate`. Roles: `user`, `assistant`, `system`, `developer`. |
| `.template(template_name)` | Adds a `TemplateReference` resolved at run time by the workflow's prompt manager. |
| `.with_tools(*tools)` | Adds `Tool` objects keyed by name. |
| `.with_output(OutputModel, strict=True, num_retries=2)` | Adds Pydantic structured-output instructions and validation. Strict mode retries invalid JSON/schema responses before failing. |
| `.with_inputs(**kwargs)` | Adds template variables and stores them in `chat.context.inputs`. |
| `.with_context(run_context)` | Seeds per-run tool state. The workflow deep-copies context for each run. |
| `.on_error(ErrorPolicy.RAISE | RETURN | SKIP)` | Controls whether workflow failures raise, return failed chats, or skip failed chats in multi-run APIs. |
| `.steps(max_steps=None)` | Async context manager yielding `WorkflowStep` items (`COMPLETION` or `TOOL_RESULT`). |
| `.run(max_steps=None)` | Runs one chat and returns `Chat`. |
| `.run_many(n, max_steps=None)` | Runs `n` chats concurrently. |
| `.run_batch(inputs, max_steps=None)` | Runs one chat per input dictionary. |
| `.stream_many(n, max_steps=None)` / `.stream_batch(inputs, max_steps=None)` | Async iterators that yield chats as they complete. |

`Chat` exposes:

| Property/method | Notes |
| --- | --- |
| `chat.messages` | Full internal message list. |
| `chat.last` | Last message. |
| `chat.transcript` | Newline-joined transcript. |
| `chat.output` | Parses `chat.last.text` into the configured Pydantic output model. Raises if no output model or the last message is not assistant JSON. |
| `chat.failed` / `chat.error` | Failure marker and serializable error when error policy returned a failed chat. |
| `chat.context` | The final `RunContext`, including `.inputs` and tool-written `.data`. |

## Prompt templates

| API | Notes |
| --- | --- |
| `MessageTemplate(role, content_template).render(**kwargs)` | Renders trusted inline Jinja2 into one `ChatMessage`. Plain `.chat("...")` text is not templated unless `as_template=True`. |
| `TemplateReference(template_name)` | Workflow placeholder for file-backed prompts. |
| `set_default_prompts_path(path)` / deprecated `set_prompts_path(path)` | Set the default prompt directory. |
| `add_prompts_path(path, namespace)` | Register an additional prompt directory. Namespaces are addressed as `namespace::template_name`. Duplicate namespace names with different paths raise `ValueError`. |
| `remove_prompts_path(namespace)` | Removes a namespace or raises if it is absent. |
| `{% message role %}...{% endmessage %}` | File-template block syntax for multi-message prompts. If a template has message blocks, non-whitespace outside blocks is invalid. |
| `fence` Jinja filter | Escapes `&`, `<`, and `>` after Giskard's prompt finalization. Use it when embedding untrusted model/user text between delimiter markers. |

Templates use Jinja2 `StrictUndefined`; missing variables fail instead of
rendering silently. Template names are passed to the Jinja loader. Use exact file
names relative to the registered prompt path, and use `namespace::name` for
namespaced paths.

## Tools and run context

Verified constructor/decorator surface:

```python
agents.Tool(
    *,
    name: str,
    description: str,
    parameters_schema: dict = {},
    fn: Callable,
    catch=None,
    run_context_param=None,
)
agents.tool(_func=None, *, catch=<default_error_catcher>)
```

| API | Notes |
| --- | --- |
| `@agents.tool` | Converts a function or method into a `Tool`. Parameters need type annotations; the docstring becomes the description and may provide parameter descriptions. |
| `@agents.tool(catch=None)` | Disables `Tool.run` error catching so exceptions propagate to the workflow error policy. |
| `Tool.run(arguments, ctx=None)` | Validates/coerces arguments through a generated Pydantic model, injects `RunContext` when a parameter is annotated as `RunContext`, runs sync or async functions, and returns a `str`. |
| Direct `tool_obj(...)` call | Calls the original function behavior without `Tool.run` serialization or catching. |
| `RunContext.set/get/has/clear` | Mutable per-run storage; `context.inputs` contains workflow inputs. |

`Tool.run` serialization facts:

- Strings return unchanged.
- Non-string primitive/list/dict outputs are JSON encoded.
- Pydantic models, datetimes, UUIDs, and lists of Pydantic models use Pydantic
  `TypeAdapter(...).dump_python(mode="json")` before JSON encoding.
- Nested Pydantic model inputs, optional models, and lists of models are coerced
  from dictionaries before the function receives them.
- By default, caught exceptions become a serializable `Error` string such as
  `ERROR: City not found`.

## Retry, rate-limit, and middleware API

| API | Notes |
| --- | --- |
| `RetryPolicy(max_attempts=3, base_delay=1.0, max_delay=None)` | Exponential-backoff policy used by retry middleware. |
| `RetryMiddleware(retry_policy=...)` | Retries all errors unless a subclass overrides `_should_retry`. |
| `GiskardLLMRetryMiddleware` | Uses `giskard.llm.should_retry` for provider-aware retry eligibility. |
| `RateLimiterMiddleware(rate_limiter=...)` | Wraps completion calls in `rate_limiter.throttle()`. |
| `CompletionMiddleware` | Base for custom middleware; implement `call(messages, params, metadata, next_fn)`. |
| `MinIntervalRateLimiter(min_interval=..., max_concurrent=None)` | Core limiter that enforces minimum time between request starts and optional concurrency. |
| `MinIntervalRateLimiter.from_rpm(rpm, max_concurrent=None, id=None)` | Convenience constructor; `rpm` must be positive. Instances with the same id and config share state. |

Generator middleware order is automatic: retry wraps rate limiter, which wraps
custom middlewares, which wraps `_call_model`.

## LiteLLM and embeddings

| API | Notes |
| --- | --- |
| `from giskard.agents.generators import LiteLLMGenerator` | Optional generator backend. Import/instantiation requires `giskard-agents[litellm]` or `giskard[litellm]`; missing extra raises an install-hint `ImportError`. |
| `LiteLLMGenerator(model="...")` | Calls `litellm.acompletion`, serializes Giskard messages/tools to OpenAI-like wire objects, and normalizes Pydantic response schema names. |
| `LiteLLMRetryMiddleware` | Defers retry eligibility to LiteLLM's status-code retry helper. |
| `EmbeddingModel(model="google/gemini-embedding-001", params=EmbeddingParams())` | Public alias for `LitellmEmbeddingModel`; calls `giskard.llm.aembedding` and returns NumPy arrays. Requires a configured embedding-capable provider. |
| `BaseEmbeddingModel.embed(texts, params=None, max_batch_size=None, max_total_chars=None)` | Batches text locally then calls `_embed` per batch. |
| `BaseEmbeddingModel.batched_embeddings(...)` | Deterministically groups texts by batch size and total character limit, truncating a single over-long text to the character limit. |
| `EmbeddingParams(dimensions=1536)` | Embedding call parameters. Defaults can be overridden per model or per call. |

Embedding batching defaults can be controlled with public environment variables
`GISKARD_AGENTS_DEFAULT_MAX_BATCH_SIZE` and
`GISKARD_AGENTS_DEFAULT_MAX_TOTAL_CHARS`.
