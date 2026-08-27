# Troubleshooting

Use these checks when evaluation, logging, tracing, metrics, or telemetry do not behave as expected.

## Evaluation problems

### The Eval UI does not start

- Install the eval extras or at least Streamlit.
- Confirm the `eval ui` command can import Streamlit.
- If the CLI exits with a missing-dependency message, the environment is incomplete rather than broken.

### The judge model is rejected

- Make sure the eval config declares the judge as a `type: llm-judge` model.
- Use either the model name or `engine/model` form expected by the checker.
- Verify that the judge prompt returns exactly two lines: `Reason:` and `Compliance:`.

### Compliance results look stale

- Use `--force` to re-run judged policies even if a result already exists.
- Use `--reset` to clear stored compliance checks before rerunning.
- Use `--disable-llm-cache` if you do not want the judge to reuse cached LLM calls.

### Topical evaluation fails on similarity matching

- `--sim-threshold > 0` requires sentence-transformers.
- If you do not want that dependency, leave the threshold at zero.

## Tracing problems

### No traces appear

- Set `tracing.enabled: true`.
- Configure the host application's `TracerProvider` before constructing rails.
- Use `OpenTelemetry` or `FileSystem` as an adapter.
- For a local trace file, confirm the path is writable.

### OpenTelemetry spans vanish silently

- The SDK provider or exporter is probably missing.
- Try a `ConsoleSpanExporter` first, then swap to your production backend.
- Remember that the library only uses the OpenTelemetry API; the host process owns the SDK.

### Async file tracing fails

- The `FileSystem` adapter's async path needs `aiofiles`.
- If you only need local debugging, keep the sync path or install the missing dependency.

## Metrics problems

### No metrics appear

- Metrics are only emitted by the IORails engine.
- Enable IORails explicitly and set `metrics.enabled: true`.
- Configure a `MeterProvider` before constructing rails.
- Prefer `Guardrails(..., use_iorails=True, require_iorails=True)` when metrics are required.

### Metrics are silently missing

- A missing `MeterProvider` produces a no-op meter with no warning.
- A synchronous `generate()` call also skips metrics emission.
- Use `generate_async()` or `stream_async()` to exercise the metrics path.

### Exporter output looks wrong

- Verify the exporter target is reachable.
- Check that your backend honors OpenTelemetry bucket conventions and `service.name`.
- Start with console export before enabling OTLP or Prometheus.

## Telemetry problems

### Anonymous usage reporting should be off but still appears

- Set the opt-out before importing the library.
- Use one of the documented env vars or the `do_not_track` file.
- Telemetry opt-out does not affect tracing or metrics.

### Telemetry keeps waiting during staging checks

- Maintenance smoke checks depend on network access and may wait for audit and heartbeat indexing.
- Treat those checks as staging-only maintenance, not as a normal user workflow.
- If you are just trying to disable telemetry in a local run, use the opt-out controls instead.

## Offline and recorded safety

- Recorded tests replay cassettes without live network access and are safe for regression checks.
- They do not prove that a live provider or judge model will behave the same way in production.
- For offline verification, use fake models, recorded fixtures, or mocked judge calls rather than a live eval command.
