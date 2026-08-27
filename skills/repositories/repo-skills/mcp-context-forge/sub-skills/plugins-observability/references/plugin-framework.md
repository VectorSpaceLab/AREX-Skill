# Plugin Framework Reference

## When to read

Read this when adding, configuring, debugging, or testing ContextForge plugins
or plugin bindings.

## Plugin types

| Type | `kind` | Runtime | Use when |
| --- | --- | --- | --- |
| Native plugin | fully qualified Python class path | in-process | low-latency validation, transformation, or policy code that can run with the gateway |
| External plugin | `external` | MCP server over streamable HTTP, STDIO, or SSE | isolation, non-Python implementations, or policy engines/services outside the gateway |

Native plugins subclass the cpex `Plugin` interface. External plugins expose the
required plugin tools over MCP; ContextForge calls them through the configured
transport.

## Hook families

MCP protocol hooks:

- `prompt_pre_fetch` / `prompt_post_fetch`
- `tool_pre_invoke` / `tool_post_invoke`
- `resource_pre_fetch` / `resource_post_fetch`

HTTP/middleware hooks:

- `http_pre_request`
- `http_auth_resolve_user`
- `http_auth_check_permission`
- `http_post_request`

HTTP auth hooks can affect identity and permission decisions; route security
policy questions to the auth/RBAC sub-skill.

## Modes

| Mode | Behavior |
| --- | --- |
| `enforce` | block on plugin violation or technical plugin error |
| `enforce_ignore_error` | block on explicit violation but allow request through on plugin error |
| `permissive` | log violations/errors but continue processing |
| `disabled` | loaded for visibility but not executed |

Use `enforce` for production policy where a plugin failure should stop the
request. Use `permissive` to burn in new plugins and observe false positives.

## Configuration shape

A plugin entry should define:

- `name`: unique display/config name.
- `kind`: native class path or `external`.
- `hooks`: list of hook names.
- `mode`: execution mode.
- `priority`: lower values execute earlier.
- `conditions`: optional targeting rules.
- `config`: plugin-specific parameters.
- `mcp`: required for external plugins.

Global `plugin_settings` can control timeout, error handling, API enablement,
and parallel execution behavior.

## Conditions

Conditions target plugins to specific servers, tenants, users, tools, prompts,
resources, content types, or patterns. Treat condition behavior as a precise
policy surface, not a loose filter. When updating conditions:

1. State which request attributes must match together.
2. Add tests for one matching request and at least one non-matching request.
3. Confirm ordering with priority when multiple plugins can transform the same
   payload.

## Plugin bindings

ContextForge supports tool plugin bindings and A2A-agent plugin bindings. Use
bindings when a plugin policy should attach to one resource family instead of
running globally. Keep binding references stable and check team visibility/RBAC
separately with the auth sub-skill.

## Native plugin skeleton

```python
from cpex.framework import Plugin, PluginContext, PluginViolation
from cpex.framework import ToolPreInvokePayload, ToolPreInvokeResult

class ExampleGuard(Plugin):
    async def tool_pre_invoke(self, payload: ToolPreInvokePayload, context: PluginContext) -> ToolPreInvokeResult:
        if payload.args and payload.args.get("dangerous"):
            return ToolPreInvokeResult(
                continue_processing=False,
                violation=PluginViolation(
                    reason="Dangerous argument",
                    description="Blocked by ExampleGuard",
                    code="DANGEROUS_ARGUMENT",
                    details={"field": "dangerous"},
                ),
            )
        return ToolPreInvokeResult(modified_payload=payload)
```

Keep plugin results structured. Include machine-readable violation codes and
safe details; do not include secrets or full sensitive payloads.

## External plugin checklist

- `kind: external`.
- `mcp` block contains a supported protocol and connection details.
- External server implements configuration and hook tools expected by the
  plugin manager.
- Timeout and error mode match the operational risk.
- TLS/auth material is supplied securely through environment or secret manager.
- Health check or parity test proves the server is reachable before enabling
  `enforce` in production.

## Validation ladder

1. Run `scripts/plugin_config_lint.py` for YAML shape.
2. Unit-test native plugin hook functions with minimal payload/context.
3. Run targeted plugin manager/service tests when editing manager logic.
4. Run plugin parity E2E only when public MCP path or plugin hook integration is
   touched.
5. For external plugins, test connection and required tools before policy mode
   is made blocking.
