# Troubleshooting and recovery

Start with the smallest side-effect-free reproduction. Force all exporters,
webhooks, file sinks, content capture, credentials, and model calls off; then
separate installation, activation, registration, lifecycle, metadata, and
export failures.

## First response sequence

1. Record the installed Mellea version and run:

   ```bash
   uv run python scripts/check_telemetry_install.py --json
   ```

2. Decide which boundary is required: base, hooks, or full telemetry. Do not
   install the telemetry extra merely to use a custom component.
3. Confirm relevant flags were set before the first Mellea import or logger
   initialization.
4. Reproduce with a typed payload, precomputed thunk, fake backend, or in-memory
   provider. Do not begin with a live collector or inference endpoint.
5. Verify teardown: scope exit/unregister, manager shutdown, background-task
   drain, signal-provider shutdown, and no in-flight span entry.

## Installation and optional dependencies

### Registration raises an ImportError mentioning ContextForge

`mellea.plugins` is intentionally importable without `cpex`, but registration,
payload construction, `modify()`, and `block()` require the hooks extra:

```bash
uv add 'mellea[hooks]'
uv run python scripts/check_telemetry_install.py --require hooks
```

If hooks are not part of the intended feature, remove registration rather than
catching the error and pretending the gate or observer is active. A custom
component does not require hooks.

### Telemetry imports but status is disabled

`is_tracing_enabled()` or `is_metrics_enabled()` is true only when the relevant
OpenTelemetry packages were importable and its umbrella flag was true during
module initialization. Install only when required:

```bash
uv add 'mellea[telemetry]'
```

Then launch a fresh process with flags set before import. Reloading one module
inside a long-running process can retain one-shot OpenTelemetry globals,
registered plugins, cached instruments, and in-flight state; use a fresh
subprocess for diagnosis.

### Pricing is unexpectedly active or absent

Pricing is optional, uses LiteLLM's price registry, and matters only when
metrics are enabled and usage exists. It auto-enables when LiteLLM is installed
unless `MELLEA_PRICING_ENABLED=false`. If explicitly enabled without LiteLLM,
it warns and disables. Unknown or private model ids legitimately produce no
cost metric.

## Registration, naming, and scope

### Duplicate registration warning or `ValueError`

Registered names are keys:

- standalone hooks use module plus qualified function name;
- each `Plugin` method uses `plugin-name.hook-value`;
- framework plugins use their configured name.

Likely causes are import-time registration plus application setup, entering the
same global diagnostic twice, repeated telemetry initialization after manager
shutdown, or two plugin classes sharing a name.

Recovery:

1. Assign registration to one application setup owner.
2. Give each maintained plugin a stable unique name.
3. Prefer a context scope for diagnostics/tests.
4. Unregister or shut down in `finally`.
5. In tests that intentionally rebuild telemetry, reset both the manager and
   the signal module's registration guard in the controlled fixture. Filter
   only the exact expected duplicate warning; never suppress the category
   globally.

Do not catch every duplicate and continue in production: that can leave an
older plugin instance active with stale state.

### Plugin fires outside the intended session

The registry is process-global. A `session_id` tracks names for later cleanup;
it is not a proven per-dispatch filter in 0.8.0.dev0. Two concurrently active
sessions can therefore see the same registered hook unless the handler filters
by payload metadata.

Use a bounded `plugin_scope` when operations do not overlap, inspect
`session_id`/`request_id` inside a tenant-sensitive handler, or isolate sessions
by process. Treat `start_session(..., plugins=[...])` as session-owned teardown,
not tenant isolation.

### Session plugin misses `session_pre_init`

Plugins supplied to `start_session(..., plugins=[...])` are registered after
backend construction and after `session_pre_init`, then can observe
`session_post_init` and later lifecycle events. A pre-init transform must be
registered before the `start_session` call and removed afterward.

### Plugin remains after normal or exceptional work

Confirm the owning session reaches `cleanup()` or exits its context manager.
For direct registration, call `unregister()` in `finally`. Do not reuse the same
plugin or `PluginSet` instance in nested/concurrent context managers; create a
new instance per active scope.

## Hook dispatch, order, and policy

### A hook never runs

Check, in order:

1. it is declared with `async def`;
2. `@hook` uses the exact `HookType`/wire value;
3. `cpex` is installed and registration completed;
4. registration occurred before the lifecycle point;
5. that code path actually fires that family (batch versus context generation,
   stream orchestration versus generation chunk event, completion versus error);
6. the lazy `ModelOutputThunk` was fully consumed when waiting for a generation
   completion hook;
7. a preceding sequential or concurrent enforcement hook did not block later
   phases.

The manager's `has_plugins(hook_type)` check distinguishes no manager/no
subscriber from a subscribed lifecycle. Do not use private manager internals in
application code to force dispatch.

### Ordering is wrong

Mode phase comes before priority:

```text
sequential -> transform -> audit -> concurrent -> fire-and-forget
```

A transform at priority 99 still runs before an audit at priority 1. Within one
mode, lower priorities run first. Equal priorities are unspecified. A
`PluginSet` priority overrides nested method/function priorities when non-null.
Use distinct numbers in the same mode for a real dependency.

### `modify()` has no effect

Both gates must pass:

- mode is `SEQUENTIAL` or `TRANSFORM`;
- field is writable for that specific hook.

Audit, concurrent, and fire-and-forget updates are discarded. Unlisted hooks
are observe-only. Return the `PluginResult`; do not only create it. Use a copied
mapping/list instead of mutating nested payload content in place, and assert the
payload returned by dispatch.

### A block does not stop work

`SEQUENTIAL` and `CONCURRENT` can enforce blocks in this version.
`TRANSFORM`, `AUDIT`, and `FIRE_AND_FORGET` cannot. Use sequential mode when a
policy must stop later phases deterministically, include a machine-readable
code, and catch `PluginViolationError` at the application boundary.

### Fire-and-forget assertion is flaky

The application result may return before the observer completes. In tests,
enable background-result collection before the call, drain after the call, and
discard stale tasks before crossing event loops. Do not make built-in metrics
blocking merely to stabilize a test.

## Tracing failures

### Span is absent

Confirm tracing was enabled before import, OpenTelemetry and hooks are present,
and the relevant tracing plugin registered. Then confirm the start hook fired
with a non-empty correlation id. A completion hook cannot produce a full span
without a start.

Session startup/lifetime spans are direct synchronous instrumentation; action,
generation, stream, tool, sampling, and validation spans are paired hook
plugins. Diagnose the correct owner.

### Span remains in flight

Match the exact id between open and close:

- `generation_id`, `action_id`, `streaming_id`, `tool_invocation_id`,
  `sampling_id`, or `validation_id`.

Close success, exception, cancellation, validation-failure, and budget-exhausted
paths as appropriate. Pop the in-flight entry before/while ending so a duplicate
terminal event is harmless. Add shutdown cleanup for abandoned spans.

A custom backend that returns a precomputed thunk can fire generation pre-call
without the normal lazy completion hook. Return an uncomputed thunk or own a
real paired completion boundary; do not synthesize a post event without the
actual result lifecycle.

### Spans are flat on Python 3.11

Hook dispatch can run through a task wrapper whose copied `ContextVar` state
does not propagate an attached OpenTelemetry context back to the caller. Mellea
therefore disables that attachment path on Python 3.11 and still emits valid,
possibly root-level spans. Verify names, attributes, ids, error status, and
closure. Require hierarchy shape only on a runtime where context attachment is
supported.

### Content appears despite tracing content being off

Check built-in debug plugins and ordinary logging. Generation debug hooks can
log prompt/response previews, and validation/sampling debug hooks can log
requirement descriptions or reasons. `MELLEA_TRACES_CONTENT=false` gates
selected span attributes, not Python log messages. Unregister diagnostics or
raise their logger level, then review console, file, webhook, and OTLP-log
handlers.

## Metrics and generation metadata

### Token metrics are missing

Inspect the fully materialized thunk:

```python
usage = result.generation.usage
model = result.generation.model
provider = result.generation.provider
```

`usage=None` is correct when the provider gave no defensible usage. Otherwise
require `prompt_tokens`, `completion_tokens`, and `total_tokens`. For streaming,
consume to completion before expecting final usage. Fix provider
post-processing rather than adding manual calls to token metric helpers.

For a raw batch, distinguish aggregate usage returned by the backend from
per-thunk usage. Do not split aggregate counts by output count unless provider
evidence supports that allocation.

### Duration exists but TTFB does not

TTFB is streaming-only and is recorded when the first chunk arrives. Confirm
streaming was requested, a chunk was consumed, and `ttfb_ms` is not `None`.
The inter-chunk histogram is additionally gated by
`MELLEA_GENERATION_CHUNK_EVENTS=true`; its first chunk intentionally has no
interval.

### Metrics plugin saw a payload but records are absent

Built-in metric handlers are fire-and-forget. Drain background tasks in tests.
In an application, verify metrics were enabled before import and that at least
one reader is configured. A meter provider without a reader may accept records
that cannot be exported.

### Cardinality or sensitive-label problem

Do not use prompts, responses, tool arguments, exception messages, request/user
ids, or free-form reasons as custom metric labels. Keep model, provider, route,
status, strategy, and requirement class names bounded. In 0.8.0.dev0 the
built-in deterministic requirement-failure metric can include its reason; make
custom deterministic reasons categorical when those metrics will be exported.

## Exporters and logging

### OTLP exporter does not send

For each signal verify all three conditions:

1. umbrella signal and exporter flag are true before initialization;
2. a signal-specific or general endpoint exists;
3. the endpoint accepts OTLP gRPC and its TLS/auth settings match.

A warning-free constructor is not end-to-end proof. Export batches may flush
later; application/deployment teardown owns provider shutdown. Collector health,
network policy, credentials, and service operation belong to `serving-and-cli`.

### Prometheus metrics do not have an HTTP endpoint

Mellea registers a reader with the default Prometheus registry; it does not
start a server. The serving application must expose and secure the scrape
endpoint. Do not start a listener from a library import or unit test.

### Logs are silent or stale after an environment change

`MelleaLogger` configures handlers once on first access. Set logging variables
before that call or rebuild the logger only in a controlled test fixture/fresh
process. Check `MELLEA_LOGS_ENABLED`, level, console switch, handler filters,
and root propagation.

`get_otlp_log_handler()` also initializes once and returns `None` when disabled,
missing OpenTelemetry, or missing an endpoint. If it returns a handler, attach
it only once to the intended logger.

### Duplicate log records

Likely causes are multiple manual handler attachments, repeated logger
configuration, or propagation to a root logger. Assign handler configuration to
one owner, inspect handler identity/count, and avoid calling the configuration
function repeatedly without clearing old handlers in test-only setup.

### Webhook rejected or unexpectedly active

A webhook must use HTTPS and have a hostname. The actual insecure-development
override is `MELLEA_LOGGER_INSECURE_HTTP_ALLOWED`; never enable it in
production. Since the handler is created at first logger setup, removing the
environment variable afterward does not remove an existing handler. Rebuild in
a fresh process and review retention/content before enabling the sink.

## Extension and import failures

### Custom component parsing fails

Test in this order:

1. `parts()` returns only valid Mellea span values;
2. `format_for_llm()` returns the exact string or `TemplateRepresentation`;
3. the template variable names match `args` and resources are packaged;
4. `_parse()` returns the declared `Component[S]` type for a known precomputed
   thunk;
5. public `parse()` wraps malformed output as `ComponentParseError`.

Keep parsing pure. A network, file, registry, or telemetry failure inside
`_parse()` obscures the model-output contract.

### Template works editable but not installed

The extension did not ship its prompt resource or lookup order/class name is
wrong. Build/install the package in an isolated layout, inspect included
resources, and test both successful lookup and the expected missing-template
error. Do not point runtime code back at a development checkout.

### Instrumentation introduces an import cycle

Move payload imports under `TYPE_CHECKING`, import telemetry helpers inside hook
bodies or activation functions, and keep core protocols independent of
optional integrations. Registration and exporter setup belong in the
application entry point. Confirm with a clean subprocess import while every
signal and sink is forced off.

### API changed after a Mellea upgrade

Re-run the bundled checker with the expected version and inspect installed
public signatures. Recheck:

- `HookType`/`PluginMode`, writable policies, and registration semantics;
- hook payload field names and lifecycle ids;
- `GenerationMetadata` fields and lazy thunk completion;
- `Component`, `TemplateRepresentation`, and `Backend` signatures;
- telemetry initialization timing, flags, and exporter protocol.

Do not patch private registry/provider state until current public behavior is
confirmed. Pin the supported Mellea range or add explicit public
feature-detection with tests for each supported version.

## Contribution recovery checklist

Before declaring recovery complete:

- reproduce without a live model, collector, webhook, or credentials;
- add a regression assertion for the specific lifecycle and teardown path;
- run formatting, lint, type checking, and fast non-qualitative tests with
  `uv`;
- add typed Google-style public docs for new behavior and exceptions;
- run the API documentation quality gate for new public exports or library
  `raise` paths;
- state what remains unverified: optional dependency, Python version, backend,
  stream cancellation, exporter/collector, or deployment.
