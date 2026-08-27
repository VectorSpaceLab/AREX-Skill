# Troubleshooting Agents and Middleware

Use this guide when LangChain v1 agent, middleware, model initialization, tool, structured output, or embedding work fails.

## Provider Package Missing for `init_chat_model`

Symptoms:

- `ImportError` while calling `init_chat_model(...)`.
- Error names an integration package such as `langchain-openai`, `langchain-anthropic`, `langchain-groq`, or another provider package.
- A provider-prefixed string like `openai:gpt-5.5` parses correctly but cannot instantiate the model class.

Likely cause:

- `langchain` v1 routes to provider packages but does not install every provider implementation by default.
- The selected provider extra or partner package is missing from the environment.

Resolution workflow:

1. Confirm the model string. Prefer `provider:model-name`, such as `openai:gpt-5.5`, over bare model names.
2. If the provider is ambiguous, pass `model_provider="..."` explicitly.
3. Confirm the optional provider package is installed in the active environment.
4. In this monorepo, use `uv` for environment operations from the package directory; do not use `pip`, `poetry`, or `conda` directly.
5. If editing provider routing, update v1 route tests rather than making live API calls.

Safe validation:

```bash
uv run --group test pytest tests/unit_tests/chat_models/test_chat_models.py
```

Skip if `uv` or optional provider packages are unavailable. Use the bundled smoke script for import-only checks.

## Provider Resolution with Missing Extras

Use this workflow for the synthetic case "debug `init_chat_model` provider resolution when package extras are missing":

1. Reproduce with an import-only or instantiation-only check, not a network invocation.
2. Inspect the provider key that `init_chat_model` should use:
   - prefixed model string: `openai:gpt-5.5` should route to provider `openai`;
   - explicit provider: `init_chat_model("gpt-5.5", model_provider="openai")`;
   - inferred provider: compare the model prefix with unit tests before changing inference rules.
3. If the provider key is unsupported, expect `ValueError` listing supported providers.
4. If the provider key is supported but the package is missing, expect `ImportError` naming the package.
5. If the package is installed but credentials are missing, instantiation may succeed while invocation fails; do not treat that as a routing bug.
6. Route provider class, credential, or API parameter debugging to integrations.

## Credentials or Network Unavailable

Symptoms:

- Authentication errors, missing API key errors, HTTP failures, local server connection errors, rate limits, or timeouts.
- Tests pass with fake models but live invocation fails.

Resolution workflow:

1. Determine whether the task requires live provider behavior. Many agent and structured-output tests can use fake models.
2. Confirm the provider package is installed separately from credentials.
3. Confirm credentials are set only if the user approved live calls.
4. Do not print API keys, local config paths, or environment dumps.
5. Skip or mark live tests as requiring credentials/network if not available.

Safe alternatives:

- Use fake chat models from unit tests for `create_agent`, tool calling, streaming, and structured output behavior.
- Use the smoke script for public imports.
- Use provider package import checks without invoking `.invoke()`.

## Tool Schema Errors

Symptoms:

- Tool validation errors mention wrong argument names, missing required fields, or wrong types.
- Agent returns a tool message with `status == "error"`.
- A tool using injected state/store/runtime fails with confusing schema output.

Likely causes:

- The tool function signature or `@tool` docstring does not match the model's tool call.
- Required arguments are missing or typed incorrectly.
- Injected arguments were accidentally made LLM-controllable.

Resolution workflow:

1. Check whether the tool is a `BaseTool`, `@tool`-decorated callable, valid tool dict, or nested agent converted to a tool.
2. Keep LLM-controllable arguments typed and documented.
3. Use `InjectedState`, `InjectedStore`, and `ToolRuntime` for system-supplied values.
4. Verify validation errors do not leak injected state names, secret values, store internals, or runtime internals.
5. Add unit tests with fake tool-calling models for both valid and invalid tool calls.

Targeted tests:

```bash
uv run --group test pytest tests/unit_tests/agents/test_create_agent_tool_validation.py tests/unit_tests/agents/test_injected_runtime_create_agent.py
```

## Structured Output Validation Errors

Symptoms:

- `StructuredOutputValidationError`.
- `MultipleStructuredOutputsError`.
- `structured_response` missing from the final state.
- Tool name mismatch for an anonymous JSON schema.

Likely causes:

- Model emitted invalid arguments for the schema.
- Model emitted multiple structured-output tool calls when only one is expected.
- Middleware dropped or replaced `response_format` while overriding a model request.
- The chosen strategy does not match provider capabilities.

Resolution workflow:

1. Identify schema type: Pydantic, dataclass, TypedDict, JSON schema, `ToolStrategy`, `ProviderStrategy`, or auto strategy.
2. For tool-based structured output, check the tool name and schema title/name.
3. For provider-native structured output, confirm the model/provider is expected to support the strategy.
4. Check `ToolStrategy.handle_errors`; it controls whether validation errors are retried, converted to feedback, or raised.
5. Inspect middleware that wraps model calls and ensure it preserves `request.response_format`.
6. Add tests asserting both the parsed `structured_response` and the message sequence when tools are involved.

Targeted tests:

```bash
uv run --group test pytest tests/unit_tests/agents/test_response_format.py tests/unit_tests/agents/test_response_format_integration.py
```

## Middleware Ordering Mistakes

Symptoms:

- Retry/fallback does not catch the intended failure.
- Model or tool limits are bypassed.
- PII redaction happens after an unsafe tool/provider call.
- Structured output disappears after a middleware override.
- Dynamic tools are added but cannot be executed.

Likely causes:

- Middleware list order does not match intended wrapper order.
- A middleware mutates `ModelRequest` directly instead of using `request.override(...)`.
- A middleware changes `request.tools` without registering or executing dynamic tools.
- State updates conflict because reducers or command behavior were misunderstood.

Resolution workflow:

1. Treat the first middleware in the list as the outer wrapper for model/tool calls.
2. Move safety middleware such as PII redaction before external calls that should not receive raw content.
3. Use `request.override(...)` to preserve unchanged request fields.
4. If adding tools dynamically, also implement `wrap_tool_call` or register tools up front.
5. Add focused sync and async tests for the exact order-sensitive behavior.

## State and Context Mistakes

Symptoms:

- Extra invocation fields are rejected.
- Middleware cannot see expected state fields.
- Runtime context is `None` or untyped.
- Tool errors expose state-like arguments.

Resolution workflow:

1. Use `AgentState` extensions for persistent state fields.
2. Use `InputAgentState` for invocation payloads with additional input fields.
3. Use `context_schema` for runtime context passed through `Runtime`.
4. Use injected tool annotations for state/store/runtime access.
5. Validate with state schema and injected runtime tests.

## Human-in-the-Loop Safety Concerns

Symptoms:

- Agent continues without waiting for approval.
- Resume behavior fails after a review decision.
- Human decision content leaks sensitive values.

Resolution workflow:

1. Confirm `HumanInTheLoopMiddleware` is configured for the intended actions/tools.
2. Use checkpointer-backed execution when interrupts must be resumed.
3. Confirm `interrupt_before` and `interrupt_after` align with the target nodes.
4. Keep approval, edit, reject, and respond decisions explicit and auditable.
5. Do not bypass HITL in unattended examples when tools have side effects.

## Shell Tool Safety Concerns

Symptoms:

- Shell tool can run host commands unexpectedly.
- Output contains secrets.
- Resources are not cleaned up after shell sessions.

Resolution workflow:

1. Prefer sandboxed execution policy when possible.
2. Require explicit approval for host execution, destructive commands, network access, or user data access.
3. Configure redaction rules for secrets in commands and outputs.
4. Use synthetic temporary directories for tests.
5. Do not include shell execution in default import smoke checks.

## File Search Safety Concerns

Symptoms:

- File search reads outside the intended root.
- Include patterns match too broadly or unexpectedly.
- User data appears in model context without review.

Resolution workflow:

1. Set a narrow search root.
2. Validate include patterns before exposing them to an agent.
3. Reject traversal and symlink escape patterns.
4. Use synthetic files in a temporary directory for tests.
5. Combine with PII/redaction middleware if file contents may include sensitive data.

## Confusing v1 vs Classic Import Paths

Symptoms:

- User imports from classic chains or agents while editing `libs/langchain_v1`.
- Tests reference `langchain-classic` behavior instead of v1 agent behavior.
- A fix changes old `libs/langchain` code when the issue is in active v1 package.

Resolution workflow:

1. Confirm package path: active v1 source is `libs/langchain_v1/langchain`.
2. Use v1 imports such as `langchain.chat_models`, `langchain.agents`, `langchain.agents.middleware`, `langchain.tools`, and `langchain.embeddings`.
3. Do not use classic chains or legacy agent APIs as evidence for v1 behavior.
4. Route classic import and migration questions to the sibling classic skill.
5. Route low-level abstractions from `langchain_core` to core-primitives.

## Smoke Script Failures

The bundled `scripts/agent_import_smoke.py` is intentionally import-only.

If it fails:

1. Confirm `langchain` is installed in the active Python environment.
2. Confirm the environment is using the intended checkout or installed package version.
3. Treat missing public exports as a packaging or API-surface issue.
4. Do not infer provider/network behavior from this script; it does not instantiate providers or call external services.
