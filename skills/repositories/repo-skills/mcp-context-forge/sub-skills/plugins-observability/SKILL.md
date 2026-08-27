---
name: plugins-observability
description: "Use and develop ContextForge cpex plugins, plugin bindings,
  internal observability, OpenTelemetry, Prometheus metrics, log search, and
  SIEM diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Plugins and Observability

Use this sub-skill for ContextForge plugin development/operation and runtime
observability: native/external cpex plugins, hook modes, plugin bindings,
internal traces, OpenTelemetry, Prometheus metrics, log search, and SIEM.

## Route here for

- writing or reviewing a native Python plugin or external MCP plugin.
- configuring `plugins/config.yaml`, plugin hook lists, modes, priorities, or
  conditions.
- binding plugin policies to tools or A2A agents.
- debugging plugin violations, hook ordering, timeout/error behavior, or plugin
  parity between Python and Rust MCP paths.
- enabling internal database-backed observability, OpenTelemetry, Prometheus,
  structured logs, log search, or SIEM export.

## Reroute

- HTTP auth hook identity/security policy: [`../auth-rbac-security/SKILL.md`](../auth-rbac-security/SKILL.md).
- MCP transport and Rust mode semantics: [`../mcp-transports-federation/SKILL.md`](../mcp-transports-federation/SKILL.md).
- Base environment flags or deployment lanes: [`../runtime-configuration/SKILL.md`](../runtime-configuration/SKILL.md).
- Full repo validation target choice: [`../development-validation/SKILL.md`](../development-validation/SKILL.md).

## Read first

- [`references/plugin-framework.md`](references/plugin-framework.md) for hook, mode, condition, binding, and external plugin rules.
- [`references/observability-logging.md`](references/observability-logging.md) for internal observability, OTEL, Prometheus, logs, and SIEM.
- [`references/troubleshooting.md`](references/troubleshooting.md) for plugin and tracing symptoms.
- [`scripts/plugin_config_lint.py`](scripts/plugin_config_lint.py) for a safe YAML summary/lint helper.

## Plugin operating checklist

1. Confirm `PLUGINS_ENABLED=true` and the intended config file path.
2. Classify plugin type: native Python class path or `kind: external` MCP
   server.
3. Verify hook names and payload direction: prompt/resource/tool pre/post hooks,
   or HTTP auth/middleware hooks.
4. Choose a mode deliberately:
   - `enforce`: block on violations or errors.
   - `enforce_ignore_error`: block violations but ignore technical plugin errors.
   - `permissive`: log violations/errors and continue.
   - `disabled`: load but never execute.
5. Order by priority; lower numbers run earlier.
6. Use conditions to target server/tool/user/content slices without assuming a
   pure OR model.
7. Run the bundled config linter before deeper runtime tests.

## Observability operating checklist

1. Decide which system is active: internal observability, OpenTelemetry, and/or
   Prometheus.
2. For internal observability, check DB-backed trace/span/event tables and Admin
   UI routes.
3. For OpenTelemetry, check exporter type, endpoint, service name/version, and
   backend reachability.
4. For Prometheus, check endpoint enablement and scrape token permissions.
5. For plugin observability, confirm hook-level metrics and violation metadata
   are emitted without leaking payload secrets.
6. Remember observability writes use independent best-effort sessions; do not
   expect main-request rollback behavior.

## Safe helpers

Summarize a plugin config without importing plugin code:

```bash
python scripts/plugin_config_lint.py --config plugins/config.yaml
python scripts/plugin_config_lint.py --config plugins/config.yaml --json
```

The helper only reads YAML and reports structural issues. It does not start MCP
servers, execute plugin hooks, contact external URLs, or mutate state.

## Source script policy

- Use the bundled config linter for structural checks.
- Treat plugin parity E2E scripts and live-gateway tests as validation
  candidates, not runtime dependencies.
- Do not copy plugin package internals into this skill; keep reusable API and
  configuration rules in references.
- External plugins that require credentials or remote services must be tested
  only after the user supplies endpoint and credential context.

## Output style

When answering plugin/observability questions, identify the active feature flag,
config file or exporter, hook/metric surface, expected safe observation, and
next validation command separately. Avoid recommending a live E2E stack when a
config lint or help-level check is enough.
