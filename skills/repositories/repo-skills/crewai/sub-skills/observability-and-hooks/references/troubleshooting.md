# Observability and Hooks Troubleshooting

Use this matrix for CrewAI tracing, telemetry, provider integrations, hooks, event listeners, output logs, task output storage, and fingerprints.

## Duplicate Traces or Duplicate Hook Effects

Symptoms:

- A single kickoff appears more than once in a dashboard.
- A hook logs the same LLM/tool call multiple times.
- A notebook/test run keeps accumulating hook behavior after re-running cells.

Likely causes:

- Global hook decorators registered again on module reload.
- Multiple `@CrewBase` instances registered their bound hook methods.
- Event listeners were instantiated repeatedly and each instance registered handlers.
- A Flow owns a trace batch and nested Crews/Flows emit events inside it, which can look like multiple related executions rather than separate top-level runs.
- Multiple observability SDKs are active at once, such as CrewAI built-in tracing plus OpenLIT plus Datadog.

Fixes:

- Inspect hook counts with `get_before_llm_call_hooks()`, `get_after_llm_call_hooks()`, `get_before_tool_call_hooks()`, and `get_after_tool_call_hooks()`.
- In tests/notebooks, call `clear_all_global_hooks()` before or after each scenario.
- Instantiate event listeners once at process startup; avoid instantiating them in a function that runs before every kickoff.
- For provider duplication, disable one layer at a time: built-in tracing (`tracing=False`), anonymous telemetry (`OTEL_SDK_DISABLED=true`), or third-party SDK init.
- Keep hook registration in import-stable modules, not inside frequently called request handlers.

## Missing CrewAI Built-In Traces

Symptoms:

- No Crew/Flow trace appears in CrewAI hosted trace UI.
- Console suggests tracing is disabled.
- Tests show no trace listener handlers.

Checks:

- If using explicit object config, confirm `Crew(..., tracing=True)` or `Flow(..., tracing=True)`.
- If using env config, confirm `CREWAI_TRACING_ENABLED=true` or `1` in the process before Crew/Flow construction.
- Confirm the code actually reaches `kickoff()`; static construction does not produce execution traces.
- Confirm the trace destination is authenticated/configured when using hosted CrewAI traces.
- Use [check_tracing_config.py](../scripts/check_tracing_config.py) to inspect relevant env vars and package availability without sending traces.

Fixes:

- Prefer explicit `tracing=True` for one run you are debugging.
- If `tracing=False` is set on the Crew/Flow, remove it or set it to `True`; it overrides env enablement.
- If the code constructs Crew/Flow objects before env vars are loaded from `.env`, load env vars earlier.
- For first-run consent behavior, do not rely on interactive prompts in non-interactive jobs; set explicit tracing config.

## Tracing Env vs Crew/Flow Override Confusion

Observed behavior:

- `CREWAI_TRACING_ENABLED=false` does not stop traces from `Crew(tracing=True)`.
- `CREWAI_TRACING_ENABLED=true` does not enable a run with `Crew(tracing=False)`.

Reason:

CrewAI's tracing enablement priority is explicit object override first, then env var, then stored user consent.

Fix:

- For a single guaranteed traced run: `Crew(..., tracing=True)` or `Flow(..., tracing=True)`.
- For a single guaranteed non-traced run: `Crew(..., tracing=False)` or `Flow(..., tracing=False)`.
- For project-wide default: use `CREWAI_TRACING_ENABLED=true` only when Crew/Flow code leaves `tracing=None`.

## Anonymous Telemetry Still Initializes

Symptoms:

- OpenTelemetry tracer provider is initialized unexpectedly.
- Network/security tooling reports a telemetry endpoint attempt.
- CrewAI tracing is disabled but anonymous telemetry still appears active.

Reason:

Built-in tracing and anonymous telemetry are related observability features but controlled by different switches.

Fixes:

- Disable anonymous telemetry with `OTEL_SDK_DISABLED=true`, `CREWAI_DISABLE_TELEMETRY=true`, or `CREWAI_DISABLE_TRACKING=true` before importing/constructing CrewAI runtime objects.
- Disable CrewAI execution tracing separately with `Crew(tracing=False)` / `Flow(tracing=False)` or by not enabling `CREWAI_TRACING_ENABLED`.
- Avoid `share_crew=True` unless fuller telemetry content is intended.

## OTLP Endpoint or Protocol Mismatch

Symptoms:

- OpenLIT, Phoenix, Braintrust, or another OTLP provider receives no spans.
- Exporter logs HTTP 404/415/connection refused.
- Local collector works for one SDK but not another.

Common causes:

- OTLP HTTP endpoint points to a gRPC port (`4317`) or OTLP gRPC endpoint points to an HTTP port (`4318`).
- Endpoint lacks `/v1/traces` when the exporter expects a full path, or includes `/v1/traces` when the SDK expects a base collector URL.
- SDK initialized after CrewAI/LLM clients were constructed, so auto-instrumentation missed them.
- `OTEL_SDK_DISABLED=true` disables SDK behavior.

Fixes:

- Match provider docs exactly for `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_PROTOCOL`.
- Try a local collector health check separately before running CrewAI.
- Initialize provider SDKs before importing or constructing CrewAI objects when the integration requires it.
- Run the safe config checker and verify `opentelemetry-*` package availability.

## Datadog LLM Observability Missing Traces

Symptoms:

- `ddtrace-run python app.py` completes, but no CrewAI traces appear in Datadog.

Checks:

- `DD_LLMOBS_ENABLED=true`.
- `DD_LLMOBS_ML_APP` is set to the app name being filtered in the Datadog UI.
- `DD_API_KEY` and `DD_SITE` match the account/region.
- `DD_LLMOBS_AGENTLESS_ENABLED=true` when using agentless mode.
- The application is actually launched via `ddtrace-run` or an equivalent auto-instrumentation entry point.

Fix:

- Keep `DD_APM_TRACING_ENABLED=false` only if using LLM Observability without APM, as intended by Datadog examples.
- Do not change CrewAI hook code until Datadog env and launch mode are verified.

## Callback or Hook Signature Mismatch

Symptoms:

- Hook raises a `TypeError`.
- Hook silently does nothing because it was never registered.
- LLM/tool call is blocked unexpectedly.

Expected signatures:

```python
def before_kickoff_hook(inputs: dict) -> dict: ...
def after_kickoff_hook(result): ...
def before_llm_hook(context) -> bool | None: ...
def after_llm_hook(context) -> str | None: ...
def before_tool_hook(context) -> bool | None: ...
def after_tool_hook(context) -> str | None: ...
def event_handler(source, event): ...
```

Fixes:

- For `@CrewBase` methods, include `self` plus the expected argument.
- For event listeners, implement `setup_listeners(self, crewai_event_bus)` and instantiate the listener before kickoff.
- For LLM message mutation, modify `context.messages` in place; do not assign a new list.
- For tool input mutation, modify `context.tool_input` in place; do not assign a new dict.
- For after hooks, return `None` when keeping the original output.

## Hooks Override or Interfere With Each Other

Symptoms:

- Later hooks do not see expected messages/tool inputs.
- A response appears over-redacted or repeatedly modified.
- Tool inputs contain debug keys that break validation.

Reasons:

- Hooks execute in registration order.
- After hooks can chain modifications by returning replacement strings.
- Before hooks mutate shared message/input objects in place.
- Global hooks apply to all agents/crews unless filtered.

Fixes:

- Add `agents=[...]` filters to LLM hooks and `tools=[...]` / `agents=[...]` filters to tool hooks.
- Avoid adding non-schema keys to `context.tool_input` unless the tool accepts them.
- Use local variables or external metrics storage instead of stuffing observability markers into tool inputs.
- Keep sanitizers idempotent: repeated execution should not keep changing already-redacted content.
- Clear global hooks between independent tests or notebook experiments.

## Human Approval Hook Blocks Automation

Symptoms:

- Job hangs waiting for input.
- CI or background worker never completes.

Cause:

`context.request_human_input(...)` is interactive and pauses live console updates until input is received.

Fixes:

- Use approval hooks only in interactive development.
- For CI, replace with deterministic allow/deny logic from config.
- For dangerous tools, return `False` by policy rather than prompting.

## Event Listener Not Firing

Symptoms:

- Custom listener code never logs events.
- Handler works in one script but not in another.

Checks:

- The listener class inherits from `BaseEventListener`.
- `setup_listeners` registers handlers with `@crewai_event_bus.on(EventClass)`.
- An instance is created before the Crew/Flow kickoff.
- The listener instance remains reachable for the process lifetime.
- The event class imported is the one emitted by the current CrewAI version.

Fixes:

- Instantiate listeners at module startup or app initialization.
- Avoid defining listeners inside short-lived functions unless the object is stored.
- If events are async/background, wait for event handlers before asserting in tests.

## Output Log File Missing or Wrong Format

Symptoms:

- No `logs.txt` file appears.
- A log path without extension writes a `.txt` file unexpectedly.
- JSON logs are not valid append-only JSON lines.

Expected behavior:

- `output_log_file=True` writes `logs.txt` in the current working directory.
- `output_log_file="name"` writes `name.txt`.
- `output_log_file="name.txt"` writes text lines.
- `output_log_file="name.json"` writes a JSON array and rewrites it as entries are appended.
- `output_log_file=False` or `None` writes nothing.

Fixes:

- Use an explicit filename ending in `.json` or `.txt`.
- Check the process working directory.
- Ensure the output directory exists and is writable before kickoff.
- Treat output logs as sensitive and redact/secure them if task outputs may contain secrets.

## Latest Task Outputs or Replay Data Missing

Symptoms:

- Latest task ids are unavailable.
- Replay cannot find a task id.
- Data is from a different run than expected.

Likely causes:

- No successful `crew.kickoff()` completed before replay/listing.
- Only the latest kickoff is supported; a later run replaced records.
- `kickoff_for_each` resets or only leaves the most recent relevant task-output state.
- The local SQLite storage location differs by environment/user.

Fixes:

- Run or verify a completed kickoff before requesting replay data.
- Do not treat latest task-output storage as multi-run history.
- Use [cli-and-projects](../../cli-and-projects/SKILL.md) for exact CLI commands to list latest task outputs or replay a task.

## Fingerprint Changes After Config Edits

Symptoms:

- A component fingerprint changed after recreating an Agent, Task, or Crew.
- Two components unexpectedly share a fingerprint.
- Fingerprint metadata changed but UUID did not.

Expected behavior:

- Default components get new random fingerprints when newly constructed.
- Mutating an existing component's goal/description/etc. does not change its current fingerprint UUID.
- `Fingerprint.generate(seed="...")` or `SecurityConfig(fingerprint="...")` produces stable UUIDs for the same seed.
- Sharing the same `SecurityConfig` instance shares the same fingerprint object across components.
- Fingerprint metadata is mutable and does not affect deterministic UUID generation.

Fixes:

- For stable identity across process restarts, use deterministic seed strings.
- Do not share a `SecurityConfig` instance unless shared identity is intended.
- Do not put secrets, tokens, raw prompts, or large/private user data into fingerprint metadata.
- If metadata edits cause audit confusion, include a metadata `version` field and log when it changes.

## Hosted Provider Credentials and Privacy

Symptoms:

- Provider SDK initializes but traces are rejected.
- User is unsure whether data leaves the machine.

Fixes:

- Classify the provider as credential-bound and ask before running any trace-emitting workload.
- Use a minimal synthetic crew with non-sensitive inputs when validating integration wiring.
- Confirm whether provider captures prompts, responses, tool results, task outputs, or only metadata.
- Never print real API keys, dashboard URLs containing tokens, or raw trace payloads with secrets.

## Quick Triage Order

1. Run [check_tracing_config.py](../scripts/check_tracing_config.py) for safe env/package inventory.
2. Identify the active observability layers: built-in tracing, anonymous telemetry, output logs, task output storage, third-party SDKs, hooks, and event listeners.
3. Resolve tracing enablement priority: object override, env var, stored consent.
4. Check hook/listener duplication and cleanup needs.
5. Check provider credentials, init order, and OTLP endpoint/protocol.
6. Inspect local output logs and latest task-output state only after a successful kickoff.
7. Confirm fingerprint identity strategy: random per construction vs deterministic seed vs shared `SecurityConfig`.
