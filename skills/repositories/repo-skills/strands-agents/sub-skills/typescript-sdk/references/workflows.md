# Workflows

Keep these checks separated: Node-only tests, browser-only tests, provider-credential checks, and example isolation are different workflows.

## 1. Change an agent-facing API

Use this flow when you touch `Agent`, `InvokeArgs`, events, snapshots, or direct tool calls.

1. Update the narrowest source surface first.
2. Keep the public barrel and subpath exports consistent.
3. Preserve named exports and avoid default exports.
4. Update or add unit tests for the exact public behavior.
5. Run `scripts/ts-core-check.sh check`.
6. If the change affects runtime packaging, also run `scripts/ts-core-check.sh package`.

Typical commands:

- `scripts/ts-core-check.sh test`
- `scripts/ts-core-check.sh check`
- `scripts/ts-core-check.sh package`

## 2. Add or update a tool

Use this flow for `tool()`, `FunctionTool`, `ZodTool`, or direct tool execution.

1. Decide whether the tool needs Zod validation or plain JSON Schema.
2. Keep the callback return value JSON-serializable.
3. If the callback can stream, return an async generator and let `FunctionTool` wrap it.
4. Use `ToolContext` for agent state and interrupt access.
5. Keep tool names valid and stable.
6. Cover both the direct callback API and the stream wrapper in tests.

Useful checks:

- Node unit tests for the tool factory
- Browser unit tests only if the tool is browser-safe
- Direct tool-call checks via `agent.tool`

## 3. Add or update a model provider

Use this flow for Bedrock, OpenAI, Anthropic, Google, Vercel, or a new provider.

1. Extend `Model` and keep `updateConfig`, `getConfig`, and `stream` consistent.
2. Keep vendor translation helpers private.
3. Map vendor stop reasons to SDK stop reasons.
4. Map vendor throttling and overflow errors to SDK errors.
5. Preserve the original cause where the provider boundary supports it.
6. Keep Node-only client setup away from browser-safe entry points.
7. Add provider-specific unit tests with mocked SDK clients.

When the provider is browser-sensitive, run the browser bundle check separately from provider credential tests.

## 4. Wire MCP tools

Use this flow when a task involves MCP servers or `McpClient`.

1. Decide whether the client is transport-based or URL-based.
2. Keep `transport` and `url` mutually exclusive.
3. Use `listTools()` before `callTool()` unless the workflow already knows the tool instance.
4. Use prefixes and filters deliberately; name resolution happens on the client side, but server tool names remain authoritative.
5. Keep task-based tool polling conditional on `tasksConfig`.
6. Treat `continueOnError` as a recovery mode, not the default.

## 5. Add hooks, middleware, interventions, or plugins

Use the right layer for the control point you need:

- **Hooks**: event observation and mutation
- **Middleware**: stage-level input/wrap/output interception
- **Interventions**: policy, guide, deny, confirm, or transform decisions
- **Plugins**: bundle reusable behavior and tool registration

Checklist:

- Confirm whether you need a value event or a type-only contract.
- Keep mutable hook fields documented and intentional.
- Use `agent.hooks.addCallback()` only when a single callback is enough.
- Use reverse-order callback semantics only where the API already expects it.

## 6. Use memory, session, or storage

Use this flow when the change is about persistence.

- `MemoryManager`: searchable long-term memory, add/search tools, injection, extraction
- `SessionManager`: snapshots and restore for agents and multi-agent orchestrators
- `Storage`: raw bytes under keys, with optional namespacing

Checklist:

1. Decide whether the data is durable state, recall data, or just raw bytes.
2. Keep storage namespaced by subsystem.
3. Make write sinks explicit.
4. Add or update tests around snapshot persistence and memory tool behavior.

## 7. Use sandbox or browser-specific features

- Use `Sandbox` when code needs command execution or file I/O.
- Use `index.node.ts` or Node-only subpaths for Node defaults.
- Use the browser-safe default path when the code must bundle for the browser.
- Do not let browser-safe guidance depend on Node builtins.

For browser-heavy changes:

- run the browser bundle check
- confirm Playwright/Chromium availability if the test requires it
- keep unsafe demo code clearly isolated in the example that needs it

## 8. Build Graph or Swarm orchestration

Use `Graph` when the topology is dependency-driven.

Use `Swarm` when routing is sequential and agent-driven.

Shared reminders:

- Build the right node type for each agent or nested orchestrator.
- Make timeout and cancellation behavior explicit.
- Preserve resume behavior and session persistence semantics.
- Keep structured-output contracts aligned with the orchestrator style.

## 9. Package and workspace flows

Use root workspace commands when you need a full repository check.

- `scripts/workspace-cli.sh setup`
- `scripts/workspace-cli.sh build`
- `scripts/workspace-cli.sh test`
- `scripts/workspace-cli.sh check`
- `scripts/workspace-cli.sh ci`
- `scripts/workspace-cli.sh example <name>`

Use the example directories as isolated consumer projects. They should not rely on unpublished workspace side effects.
