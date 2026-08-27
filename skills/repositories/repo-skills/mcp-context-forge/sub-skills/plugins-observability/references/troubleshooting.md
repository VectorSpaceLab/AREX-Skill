# Plugins and Observability Troubleshooting

## Plugin config exists but nothing happens

Likely causes:

- `PLUGINS_ENABLED=false` or wrong `PLUGINS_CONFIG_FILE`.
- plugin mode is `disabled`.
- conditions do not match the current request.
- hook name is wrong for the payload surface.
- plugin binding targets a different tool/team/A2A agent.

Recovery:

1. Run `scripts/plugin_config_lint.py --config <file>`.
2. Confirm the gateway was restarted or dynamic config reload path applied.
3. Check plugin list/API/UI for loaded state.
4. Use a minimal request that matches conditions and hook family.
5. Switch to `permissive` before `enforce` when proving a new policy.

## Enforce mode blocks too much

Likely causes:

- plugin returns `continue_processing=False` for broad inputs.
- condition scope is too broad.
- violation code or match rule catches sanitized/test payloads.
- multiple same-priority plugins interact unexpectedly.

Recovery:

1. Reproduce with one plugin enabled.
2. Narrow `conditions` by server/tool/user/content signals.
3. Inspect structured violation details but avoid logging full sensitive
   payloads.
4. Add tests for both violating and non-violating inputs.
5. Consider `enforce_ignore_error` only when technical errors should not block,
   not as a way to ignore true violations.

## External plugin unreachable

Likely causes:

- wrong MCP protocol or URL.
- server lacks required plugin tools.
- TLS/auth config missing.
- network policy, DNS, or container service name mismatch.
- timeout too short for the external policy service.

Recovery:

1. Test the external MCP server independently with a read-only tool list.
2. Confirm required hook tool names and payload schemas.
3. Verify TLS/headers/secrets through deployment secret management.
4. Keep mode `permissive` until reachability and violation handling are proven.

## Missing internal traces

Likely causes:

- `OBSERVABILITY_ENABLED=false`.
- sample rate or trace filters exclude the request.
- request path not instrumented.
- database write failed best-effort but request still succeeded.
- retention cleanup removed older traces.

Recovery:

1. Check feature flag and Admin UI/API route availability.
2. Use a request that should produce a tool/prompt/resource trace.
3. Inspect logs for observability write errors.
4. Confirm database pool is sized for tracing load.
5. Query by correlation ID or time range.

## Missing OpenTelemetry spans

Likely causes:

- OTEL disabled or exporter set to none.
- wrong OTLP endpoint, protocol, TLS, or collector path.
- collector rejects service attributes or auth.
- backend sampling drops spans.

Recovery:

1. Check `OTEL_ENABLE_OBSERVABILITY`, exporter, endpoint, and service name.
2. Test against a local collector if available.
3. Compare ContextForge logs/correlation IDs with collector logs.
4. Do not enable verbose payload logging with secrets to debug tracing.

## Prometheus scrape fails

Likely causes:

- metrics endpoint disabled.
- scrape token missing/expired or lacks metrics permission.
- reverse proxy strips Authorization header.
- handler exclude pattern hides expected route labels.

Recovery:

1. Confirm metrics feature flag and endpoint route.
2. Generate or refresh a metrics bearer token.
3. Check Prometheus scrape config includes the Authorization header.
4. Keep custom labels low-cardinality.

## Log/SIEM issues

- If logs are present but SIEM export is missing, check destination config and
  URL allowlist first.
- If security events lack correlation, preserve correlation ID middleware and
  structured logger fields.
- If support bundles expose sensitive material, treat that as a security bug and
  redact at the source helper.
