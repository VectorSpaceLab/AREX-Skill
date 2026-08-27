# Provider Integration And Runtime Source Rules

Use these rules when editing `nemoguardrails/` in a live source checkout, especially public APIs, providers, server paths, tracing, telemetry, or runtime error handling.

## Architecture anchors

- `Guardrails` is the modern entry point. It delegates to `IORails` for input/output rails through the engine registry when compatible, and falls back to the legacy `LLMRails` event-driven Colang pipeline unless configured to require `IORails`.
- `RailsConfig` is the user-facing configuration model, loaded with `from_path` or `from_content`.
- Colang has 1.0 and 2.x runtimes; keep dispatch and migration behavior compatibility-sensitive.
- LLM access goes through framework/provider abstractions: the default OpenAI-compatible framework or the LangChain framework.
- Built-in rails and optional integrations are lazily imported. The server, action server, request context, tracing, metrics, and telemetry have distinct runtime contracts.

## Public API compatibility

Preserve public APIs unless the task explicitly changes them and the user has maintainer direction for the compatibility risk.

Compatibility-sensitive surfaces include:

- Top-level public imports and `__all__` exports.
- Constructor signatures for `Guardrails`, `LLMRails`, `RailsConfig`, provider classes, and documented integrations.
- Documented sync/async methods such as generation, checks, streaming, event APIs, and server endpoints.
- Config schemas, Pydantic models, validation errors, default model parameters, and shipped config examples.
- Server request/response shapes, OpenAI-compatible fields, and HTTP status/error envelope behavior.
- Colang behavior, action dispatch, tool-call behavior, streaming semantics, tracing spans, metrics, and anonymous usage telemetry.

When deprecating, keep the old path working and emit `warnings.warn(..., DeprecationWarning, stacklevel=...)` from the compatibility path.

## Sync/async parity

- Keep sync and async behavior aligned for `LLMRails`, `Guardrails`, and related public methods.
- Place the core logic in the async method when that is the established pattern.
- Sync wrappers should delegate through `get_or_create_event_loop()` and must raise when called inside a running event loop if the surrounding API already has that contract.
- Test both sync and async surfaces when a shared public behavior changes.

## Optional dependencies and providers

When adding a new optional LLM provider, embedding provider, external rail, or library integration:

1. Keep the third-party dependency optional. Do not import the package at module import time in a way that breaks core imports when the package is absent.
2. Lazily import the third-party package inside `__init__` or the method that needs it. Wrap `ImportError` with a message that names the optional extra or package to install.
3. Add dependencies to an optional extra or relevant dependency group, not the default runtime dependencies, unless the task is explicitly about packaging policy.
4. Read the current `pyproject.toml` and `uv.lock` before patching dependency metadata. Regenerate the lock with project tooling. If the lock cannot be regenerated, stop and report that the dependency state is inconsistent.
5. Keep provider names, constructor signatures, config keys, and registration behavior consistent with sibling providers.
6. Document the provider/engine name, optional extra, expected API keys or environment variables, framework route, supported modes, and known limitations.

For embedding providers, follow the established `EmbeddingModel` pattern: set `engine_name`, implement both `encode()` and `encode_async()`, and register the class with `register_embedding_provider(...)` in the provider registry.

For LLM providers, implement the `LLMModel` protocol and register through the framework/provider abstraction. Prefer the default OpenAI-compatible framework for OpenAI-compatible providers. Use LangChain only when the provider requires LangChain or the task explicitly changes LangChain behavior.

## LLM calls, HTTP, and secret handling

- Route LLM calls through existing framework/model abstractions and helpers such as `llm_call` unless the surrounding code has a more specific established path.
- Avoid ad hoc provider calls that bypass shared parameter handling, tracing, metrics, retries, streaming behavior, or error handling.
- Wrap failures from LLM model and LLM-provider calls in the domain exceptions `LLMCallException` or `LLMClientError` subclasses, preserving the original cause with `from`.
- Do not use the LLM exception hierarchy for non-LLM integrations such as external guardrail, moderation, or scanning APIs unless the established contract requires it.
- Treat HTTP header names as case-insensitive. Only compare header values case-insensitively when a relevant HTTP spec or provider contract says so.
- Never mirror API keys, credentials, bearer tokens, provider secrets, private endpoints, or sensitive request/response content back in response bodies or logs.
- Secrets belong in headers, environment variables, or local configuration paths, not in committed code, tests, docs examples, or snapshots.

## Logging, state, and side effects

- Use `log = logging.getLogger(__name__)`; do not add `print()` in runtime paths.
- Avoid broad filesystem walks, import-time side effects, and global state changes unless the surrounding code already establishes that pattern.
- Reset context variables and framework registries in tests when a code path touches them.
- Preserve non-text model metadata such as reasoning content, usage data, finish reasons, request IDs, and streamed metadata chunks. Do not drop reasoning-only or usage-only chunks just because message content is empty.
- Keep observability signals independently configurable. Tracing, metrics, logs, and anonymous usage telemetry are separate contracts; do not enable, disable, or configure them as a hidden bundle.
- Mark experimental behavior clearly in docs and keep it isolated from stable contracts.

## Testing provider and runtime changes

- Unit tests must not call live LLM or provider services.
- Use `FakeLLMModel` and `TestChat` for deterministic model and rail behavior.
- Use `pytest-httpx` (`httpx_mock`) for provider HTTP requests and external scanning/moderation APIs.
- Set secrets with `monkeypatch`; do not rely on the developer's real environment.
- For config-driven changes, test with real `RailsConfig` loading.
- Assert both success and failure paths, including optional dependency missing, unsupported mode, invalid config, upstream HTTP error, retry/rate-limit behavior where relevant, and secret redaction.
- For metadata/stats propagation, assert the actual propagation targets and reset every context variable the path touches.
- Keep any real-network test explicitly skipped unless the operator and maintainers requested live-provider validation.

## Provider-change checklist

Before handoff for a provider/integration change, verify that the answer covers:

- Optional dependency placement and lazy import behavior.
- Framework route: default OpenAI-compatible path versus LangChain.
- Registration name and constructor/config compatibility.
- Sync/async parity and streaming behavior when applicable.
- Domain exception wrapping and original-cause preservation.
- HTTP header/secret handling and no response/log leakage.
- Deterministic tests using fakes or HTTP mocks.
- Docs updates that state the required extra, environment variables, supported modes, limitations, and no-live validation boundary.
- Focused validation commands from [test-and-validation](test-and-validation.md).
