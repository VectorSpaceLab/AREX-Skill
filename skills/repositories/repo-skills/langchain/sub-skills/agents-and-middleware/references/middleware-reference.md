# Middleware Reference

LangChain v1 agents accept ordered middleware instances through `create_agent(..., middleware=[...])`. Middleware can inspect or modify agent state, runtime context, model requests, model responses, and tool calls.

## Public Middleware Surface

The public middleware entrypoint exports these families from `langchain.agents.middleware`:

- Base and state types: `AgentMiddleware`, `AgentState`, `InputAgentState`, `OutputAgentState`, `ModelRequest`, `ModelResponse`, `ExtendedModelResponse`, `ToolCallRequest`, and `Runtime`.
- Hook decorators: `before_agent`, `after_agent`, `before_model`, `after_model`, `dynamic_prompt`, `wrap_model_call`, `wrap_tool_call`, and `hook_config`.
- Context editing: `ContextEditingMiddleware` and `ClearToolUsesEdit`.
- File search: `FilesystemFileSearchMiddleware`.
- Human-in-the-loop: `HumanInTheLoopMiddleware` and `InterruptOnConfig`.
- Model limits and resilience: `ModelCallLimitMiddleware`, `ModelFallbackMiddleware`, and `ModelRetryMiddleware`.
- PII handling: `PIIMiddleware` and `PIIDetectionError`.
- Provider tool search: `ProviderToolSearchMiddleware`.
- Shell tool: `ShellToolMiddleware`, `HostExecutionPolicy`, `DockerExecutionPolicy`, `CodexSandboxExecutionPolicy`, and `RedactionRule`.
- Summarization: `SummarizationMiddleware` and `TriggerClause`.
- Todo planning: `TodoListMiddleware`.
- Tool limits and resilience: `ToolCallLimitMiddleware`, `ToolRetryMiddleware`, `LLMToolEmulator`, and `LLMToolSelectorMiddleware`.

Use these exports before importing implementation modules directly. Direct implementation imports are appropriate only when editing or testing the middleware itself.

## Hook and Composition Model

Common hook points:

- `before_agent`: run before the agent graph starts processing.
- `after_agent`: run after the agent finishes.
- `before_model`: inspect or update state before a model call.
- `after_model`: inspect or update state after a model call.
- `dynamic_prompt`: build runtime system instructions.
- `wrap_model_call`: wrap the model invocation; useful for retry, fallback, request mutation, or response interception.
- `wrap_tool_call`: wrap tool execution; useful for retries, guardrails, dynamic tool handling, and error shaping.

Important composition rules:

- Middleware order matters. The first middleware in the list wraps later middleware for model/tool call wrappers.
- Inner middleware results are normalized to `ModelResponse`; `ExtendedModelResponse` can carry additional `Command` state updates.
- `ModelRequest` follows an immutable update pattern. Use `request.override(...)` for changes to model, messages, system message, tools, `response_format`, state, tool choice, or model settings.
- Direct assignment to `ModelRequest` fields is deprecated and may warn.
- Middleware that changes tools during `wrap_model_call` must ensure tools are registered at agent creation or handle dynamic execution in `wrap_tool_call`; otherwise the factory can report unknown dynamic tools.
- Middleware with async behavior should implement and test async hooks as well as sync hooks when both paths are expected.

## State and Runtime Patterns

Use state and context intentionally:

- Extend `AgentState` with a `TypedDict` when middleware or tools need persistent graph state fields.
- Use `InputAgentState` when invocation payloads include fields beyond messages.
- Use `context_schema` for runtime context rather than placing request-scoped metadata in message content.
- Use `ToolRuntime`, `InjectedState`, and `InjectedStore` for tool access to state, runtime, and storage without making those fields LLM-controllable.
- Avoid leaking injected state values in validation messages; existing tests assert this behavior.

When middleware emits additional state updates:

- `ModelResponse` contains model result messages and optional `structured_response`.
- `ExtendedModelResponse` wraps a `ModelResponse` and optionally includes a LangGraph `Command`.
- Commands returned from `wrap_model_call` are applied after the model node; message reducers add messages rather than replacing them.
- Certain command features such as `goto`, `resume`, or graph-targeted commands are not supported from `wrap_model_call` and should use supported jump/state fields instead.

## Middleware Families

### Retry and Fallback

Use when a model or tool call can fail transiently and the behavior should be contained at the agent layer.

- `ModelRetryMiddleware` wraps model calls with retry behavior.
- `ToolRetryMiddleware` wraps tool calls with retry behavior.
- Shared retry helpers validate retry parameters, decide retryable exceptions, and calculate delays.
- `ModelFallbackMiddleware` switches to fallback models when primary model calls fail.

Checklist:

1. Keep retry conditions explicit; avoid catching all failures when validation errors should surface.
2. Preserve `response_format`, `tools`, and `model_settings` when overriding a request for retry or fallback.
3. Add tests for exhausted retries, non-retryable exceptions, and structured output preservation if changing behavior.
4. Do not run live provider retry tests without credentials and explicit network permission.

### Human-in-the-Loop

Use `HumanInTheLoopMiddleware` when tool actions require review, approval, editing, rejection, or direct human response.

Checklist:

1. Configure interrupt behavior for the relevant tool/action names.
2. Validate graph interrupt behavior with a checkpointer if resuming after review.
3. Treat HITL as a safety boundary; do not bypass review in examples or tests.
4. Avoid storing sensitive approval data in messages unless required by the workflow.

### Summarization and Context Editing

Use summarization and context editing when conversation state or tool traces grow too large.

- `SummarizationMiddleware` can summarize conversation context according to trigger clauses and model/token accounting.
- `ContextEditingMiddleware` and `ClearToolUsesEdit` can modify context, including clearing historical tool-use context.

Checklist:

1. Confirm token-count behavior uses the active model or a safe approximate counter.
2. Preserve messages needed for structured output, tool call resolution, or auditability.
3. Test edge cases around empty histories, tool-use messages, and repeated summarization.

### Tool and Model Limits

Use limits to stop runaway loops or unexpected costs.

- `ModelCallLimitMiddleware` tracks model call counts and can raise a limit exceeded error.
- `ToolCallLimitMiddleware` tracks tool calls, including per-tool and total limits.

Checklist for the synthetic case "limit model calls while preserving structured output and tool execution":

1. Place model call limit middleware so it observes every model call in the agent loop.
2. Keep the user's `response_format` intact when any middleware overrides the model request.
3. Ensure tool calls still execute before the model limit is reached; if the limit is reached, return or raise a clear final signal.
4. Add a unit test using a fake tool-calling model with at least one real tool call followed by structured output parsing.
5. Assert both `structured_response` and expected tool messages when under the limit, and assert the limit error/final message when over the limit.

### PII and Redaction

Use `PIIMiddleware` to detect, redact, mask, hash, or block sensitive strings before they reach unsafe boundaries.

Evidence-backed detector categories include email, credit card, IP address, MAC address, and URL detection, plus configurable detector resolution.

Checklist:

1. Decide whether the workflow should block, redact, mask, or hash sensitive values.
2. Apply redaction before shell, file search, external tools, or provider calls that should not receive raw PII.
3. Include tests for false positives and non-sensitive content.
4. Treat `PIIDetectionError` as a user-visible policy failure, not a transient provider error.

### File Search

Use `FilesystemFileSearchMiddleware` for agent-accessible file search within controlled roots.

Safety checklist:

1. Scope the root directory narrowly.
2. Validate include patterns; middleware contains helpers for include pattern expansion and root containment.
3. Reject or sanitize traversal attempts.
4. Do not expose arbitrary user filesystem access in unattended tests.
5. Prefer temporary directories and synthetic files for validation.

### Shell Tool

Use `ShellToolMiddleware` only when shell execution is explicitly desired and safe. Execution policy classes include host, Docker, and Codex sandbox policies.

Safety checklist:

1. Prefer sandboxed execution policies over host execution.
2. Require explicit user approval for host shell use, destructive commands, network access, or credential-bearing environments.
3. Configure redaction rules for secrets and sensitive output.
4. Avoid using shell middleware in import smoke checks or default unit tests.
5. Validate cleanup behavior for shell sessions and resources when changing execution internals.

### Todo Planning

Use `TodoListMiddleware` when an agent should maintain a planning state through a `write_todos` tool.

Checklist:

1. Ensure todo state is part of the agent state schema.
2. Test tool call and state update behavior with fake models.
3. Keep todo content user-visible and avoid storing hidden credentials or system-only data.

### Provider Tool Search

Use `ProviderToolSearchMiddleware` when provider-native server-side tool search behavior should be coordinated with LangChain tools.

Checklist:

1. Determine provider from model params, model name, or class name only when evidence supports it.
2. Defer only tools intended for provider-side execution.
3. Keep regular LangChain tools executable by the local tool node.
4. Route provider-specific implementation questions to integrations.

### Tool Selection and Emulation

- `LLMToolSelectorMiddleware` lets an LLM select relevant tools before execution.
- `LLMToolEmulator` can emulate tools with a model when appropriate.

Checklist:

1. Ensure selected tools remain registered and executable.
2. Avoid emulation for tools with irreversible side effects or strict security requirements.
3. Add tests for selection output parsing and empty/no-tool cases.

## Validation Matrix

Use targeted tests instead of broad suites while iterating:

```bash
uv run --group test pytest tests/unit_tests/agents/middleware tests/unit_tests/agents/middleware_typing
uv run --group test pytest tests/unit_tests/agents/test_create_agent_tool_validation.py tests/unit_tests/agents/test_response_format.py
```

Skip middleware tests that require Docker, shell access, external services, Redis/Postgres, or provider credentials unless the environment and user permission are available. Classify those as native verification candidates rather than routine unit checks.

## Common Review Questions

- Does middleware preserve `response_format`, tools, model settings, and runtime context when overriding requests?
- Does middleware order produce the intended outer/inner wrapper behavior?
- Are state fields typed and merged through the graph reducers expected by `AgentState`?
- Are injected state/store/runtime values excluded from LLM-controlled schemas and error messages?
- Are shell/file-search/HITL workflows gated by explicit safety decisions?
- Are provider-specific assumptions delegated to the integration package instead of hardcoded in v1 agent code?
