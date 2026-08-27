# Agent Workflows

This reference covers the actively maintained `langchain` v1 package. It focuses on practical edits and validation for `init_chat_model`, `create_agent`, structured output, tools, embeddings initialization, and agent runtime customization.

## Package and Source Orientation

- Distribution: `langchain`.
- Source root in the monorepo: `libs/langchain_v1/langchain`.
- Python requirement in sampled metadata: `>=3.10.0,<4.0.0`.
- Core runtime dependencies in sampled metadata: `langchain-core`, `langgraph`, and `pydantic`.
- Optional provider extras include `openai`, `anthropic`, `azure-ai`, `google-vertexai`, `google-genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `groq`, `aws`, `baseten`, `deepseek`, `xai`, and `perplexity`.
- Development uses package-local `pyproject.toml` and `uv.lock` under `libs/langchain_v1`; there is no root `pyproject.toml` for the monorepo.

Use these public import paths for v1 work:

```python
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.tools import tool, BaseTool, ToolRuntime, InjectedState, InjectedStore
from langchain.embeddings import init_embeddings, Embeddings
```

Route implementation details from `langchain_core` to the core-primitives sub-skill. Route concrete provider classes and provider-specific kwargs to the integrations sub-skill.

## `init_chat_model` Workflow

`init_chat_model` initializes chat models through a unified interface. It supports:

- Fixed model: pass a model string and receive a `BaseChatModel` instance.
- Configurable model: omit the model or pass `configurable_fields` to choose model/provider at runtime through runnable config.
- Provider-prefixed model strings such as `openai:gpt-5.5`.
- Best-effort provider inference from known model-name prefixes when `model_provider` is omitted.

Typical edit checklist:

1. Start in `langchain/chat_models/base.py` and inspect `_BUILTIN_PROVIDERS`, `_attempt_infer_model_provider`, overloads, and the `init_chat_model` docstring.
2. If adding a provider route, update the provider mapping in sorted order and check import module path, class name, and creator callable.
3. Add or adjust unit tests in `tests/unit_tests/chat_models/test_chat_models.py`; tests assert provider inference, missing dependency errors, configurable behavior, and sorted provider mappings.
4. Do not instantiate network clients in tests unless existing tests already mock credentials and provider packages.

Expected failure signals:

- Unknown provider raises `ValueError` naming supported providers.
- Missing provider package raises `ImportError` explaining the required integration package.
- Passing a model object instead of a string raises `TypeError`.
- Configurable models expose runnable methods immediately but defer non-configurable model methods until runtime configuration provides a concrete model.

Validation commands from `libs/langchain_v1` when `uv` is available:

```bash
uv run --group test pytest tests/unit_tests/chat_models/test_chat_models.py
```

Skip this command if `uv` is unavailable or required optional provider packages are not installed. In that case, use the bundled import smoke script for a lighter check.

## `create_agent` Workflow

`create_agent` builds a compiled LangGraph-backed agent with tools, middleware, structured output, custom state, runtime context, persistence, interrupts, and debug logging.

Important parameters visible in the public factory include:

- `model`: a model string or chat model instance.
- `tools`: a sequence of `BaseTool`, callables decorated with `tool`, dict tools, or nested agents transformed into tools.
- `system_prompt`: optional instructions converted into system message behavior.
- `middleware`: ordered middleware instances.
- `response_format`: structured output strategy, schema, or JSON schema dict.
- `state_schema`: custom `AgentState` extension, commonly used with middleware-owned fields.
- `context_schema`: typed runtime context for `Runtime` and middleware access.
- `checkpointer` and `store`: persistence and cross-run storage hooks from LangGraph.
- `interrupt_before` and `interrupt_after`: node interrupt controls for review flows.
- `debug`: verbose graph execution diagnostics.
- `name`: agent name, used by subagent and metadata flows.
- `cache` and `middleware` runtime config factories are also supported by factory internals.

Typical edit checklist:

1. Start in `langchain/agents/factory.py` for public overloads, parameter docs, graph construction, structured output setup, middleware composition, and validation errors.
2. Check `tests/unit_tests/agents/test_response_format.py`, `test_response_format_integration.py`, `test_create_agent_tool_validation.py`, `test_state_schema.py`, `test_system_message.py`, `test_agent_streaming.py`, and middleware tests for expected behavior.
3. Use fake chat models from tests for local validation; do not require live provider calls.
4. When changing agent state or middleware behavior, validate both sync and async paths if hooks or tools support both.
5. Preserve public function signatures; new public parameters should be keyword-only and documented.

Validation commands from `libs/langchain_v1`:

```bash
uv run --group test pytest tests/unit_tests/agents/test_response_format.py tests/unit_tests/agents/test_create_agent_tool_validation.py tests/unit_tests/agents/test_state_schema.py
```

## Structured Output Workflow

Structured output is configured through `response_format` and implemented in `langchain/agents/structured_output.py` plus factory integration.

Supported schema forms include:

- Pydantic `BaseModel` subclasses.
- Dataclasses.
- `TypedDict` classes.
- JSON schema dictionaries.
- `ToolStrategy`, including error-handling behavior.
- `ProviderStrategy`, for provider-native structured output when supported.
- `AutoStrategy`, when the factory chooses between provider-native and tool-based approaches.

Expected output state:

- Successful parsing stores the parsed result under `structured_response`.
- Tool-based structured output may add tool messages as part of the agent message sequence.
- Multiple structured output tool calls raise `MultipleStructuredOutputsError` unless handled by the configured strategy.
- Schema parse failures raise or feed back `StructuredOutputValidationError` depending on `ToolStrategy.handle_errors`.

Typical edit checklist:

1. Keep schema parsing support aligned across Pydantic, dataclass, TypedDict, and raw JSON schema tests.
2. If changing error behavior, update tests for retries, multiple outputs, and invalid tool arguments.
3. Preserve structured output through middleware wrapping: middleware that overrides model requests should not drop `response_format` unless intentionally changing behavior.
4. For provider-native output decisions, check model profile and fallback pattern logic in the factory; avoid hardcoding unsupported provider claims.

Targeted validation:

```bash
uv run --group test pytest tests/unit_tests/agents/test_response_format.py tests/unit_tests/agents/test_response_format_integration.py
```

## Tools Workflow

`langchain.tools` re-exports public tool primitives from `langchain_core.tools` and v1 runtime injection helpers.

Public v1 exports include:

- `BaseTool`
- `ToolException`
- `tool`
- `InjectedToolArg`
- `InjectedToolCallId`
- `InjectedState`
- `InjectedStore`
- `ToolRuntime`

Tool validation tests show that agent tool invocation errors should report LLM-controllable argument problems without leaking injected state, store, runtime objects, or secret values.

Typical edit checklist:

1. For import/export changes, update `langchain/tools/__init__.py` and `tests/unit_tests/tools/test_imports.py`.
2. For validation or injected runtime behavior, inspect `langchain/tools/tool_node.py` and agent tests around injected state/runtime.
3. Use `@tool` docstrings and typed signatures to define tool schemas; avoid ambiguous or untyped new public examples.
4. Verify tool errors preserve safety: no injected state names, secret values, store internals, or runtime internals should appear in LLM-facing validation messages.

Targeted validation:

```bash
uv run --group test pytest tests/unit_tests/tools/test_imports.py tests/unit_tests/agents/test_create_agent_tool_validation.py tests/unit_tests/agents/test_injected_runtime_create_agent.py
```

## Embeddings Initialization Workflow

`langchain.embeddings` exposes `Embeddings` and `init_embeddings`. The v1 tests cover provider-prefixed model strings, explicit provider plus model, and provider validation.

Expected model string behavior:

- `openai:text-embedding-3-small` parses to provider `openai` and model `text-embedding-3-small`.
- Models that themselves contain colons are valid when the provider prefix is clear, such as `openai:ft:text-embedding-3-small`.
- Bare embedding model names require an explicit provider.
- Invalid or empty providers/models raise `ValueError` and list supported providers.

Typical edit checklist:

1. Start in `langchain/embeddings/base.py` for provider mapping and parse/inference helpers.
2. Keep supported provider mappings sorted and package module names underscore-based, lowercase, and `langchain_`-prefixed.
3. Add tests in `tests/unit_tests/embeddings/test_base.py` and import tests in `tests/unit_tests/embeddings/test_imports.py`.
4. Do not require live embedding API calls for unit tests.

Targeted validation:

```bash
uv run --group test pytest tests/unit_tests/embeddings/test_base.py tests/unit_tests/embeddings/test_imports.py
```

## Provider Initialization Routes

Chat model provider routing is split into two concerns:

- `langchain` v1 owns the unified `init_chat_model` route table and provider inference.
- Partner packages own concrete provider classes, credentials, request parameters, and API behavior.

When debugging provider resolution:

1. Check whether the model string uses a provider prefix such as `openai:gpt-5.5`; prefer prefixed form for predictable routing.
2. Check whether `model_provider` is set explicitly when the model name prefix is ambiguous.
3. Check whether the corresponding integration package is installed through the package manager used by the project.
4. Check whether the provider requires credentials or network access before attempting invocation.
5. For bare model names, compare against inference tests before adding or changing inference rules.

Do not convert source error messages that mention `pip install` into monorepo development instructions. In this repository, use `uv` for environment operations.

## Runtime Customization Workflow

Agent runtime customization often touches multiple surfaces:

- `state_schema` for graph state fields available to tools and middleware.
- `context_schema` for typed runtime context.
- Middleware hooks for before/after model, before/after agent, model call wrapping, and tool call wrapping.
- `checkpointer` for checkpointed runs and interrupts.
- `store` for persistent tool/runtime access.
- `interrupt_before` and `interrupt_after` for review points.
- `debug=True` for graph execution traces.

Practical checklist:

1. Define state additions in a `TypedDict` extending `AgentState` or through middleware state schema.
2. Use `InputAgentState` for input payloads when extra fields must be accepted at invocation time.
3. Use `ToolRuntime`, `InjectedState`, and `InjectedStore` for tool access to runtime data instead of exposing internal values in LLM-controllable schemas.
4. In middleware, use `request.override(...)` instead of direct assignment to `ModelRequest` fields.
5. Validate both state update behavior and message reducers when middleware returns `ExtendedModelResponse` or LangGraph `Command` objects.

## Skip Conditions

Skip live model, embedding, shell, file-search, and provider-tool-search execution when any of these are true:

- Required provider package is not installed.
- API credentials or local model server are unavailable.
- The test would access network, filesystem outside a reviewed temporary directory, shell commands, or user data.
- `uv` is unavailable in the host environment.
- The target behavior can be validated with fake models, import checks, or unit tests instead.
