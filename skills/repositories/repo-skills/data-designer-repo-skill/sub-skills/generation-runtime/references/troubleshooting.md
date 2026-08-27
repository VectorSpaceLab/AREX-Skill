# Troubleshooting

Use this reference when runtime generation fails, looks silent, or behaves differently from the configuration you expected.

## 1) `validate()` works, but `check_models()` or `create()` fails

Likely cause:

- `validate()` only checks configuration shape and compilation.
- `check_models()` actually probes model aliases and MCP tool aliases.
- `create()` also runs the full runtime stack, so it can fail later even if validation passed.

What to do:

- If the config is sampler-only, the fact that `check_models()` is a no-op is normal.
- If the config is model-backed, inspect the model aliases and tool aliases first.
- If you only need a structure check, stop at `validate()`.

## 2) Missing API keys or default providers

Likely cause:

- You relied on default providers, but the configured API keys are absent.
- The default provider list is only useful when its providers are actually configured.

What to do:

- For model-backed runs, set explicit `model_providers` or configure the expected env vars.
- For a local sampler-only smoke run, still pass one inert `ModelProvider` object so the registry can be created, even if no model aliases will be used.
- If the constructor warns that every default provider is missing keys, treat that as a setup issue, not a DataDesigner bug.

## 3) No usable model aliases

Likely cause:

- The config only uses samplers, processors, or other non-model columns.
- Or the model aliases are present but never referenced by the compiled config.

What to do:

- Use `validate()` and `preview()`; both are appropriate for a sampler-only configuration.
- `check_models()` should short-circuit when no model or tool aliases are referenced.
- The bundled sampler smoke script uses this path intentionally.

## 4) Transient provider or model failures

Symptoms:

- rate-limit errors
- connection hiccups
- temporary provider failures
- request-admission timeouts
- early shutdown after a run starts producing too many errors

What to do:

- Increase `max_attempts` on `check_models()` when the failure is transient.
- Tune `retry_backoff_seconds` if the provider needs a longer pause between probes.
- If `create()` raises `DataDesignerEarlyShutdownError`, the run shut down before any records completed.
- If some records did complete, the run may surface a generic `DataDesignerGenerationError` instead of the early-shutdown subtype.

## 5) Model health checks are missing or should be bypassed temporarily

What to do:

- Confirm that `check_models()` is being called on the right builder.
- Verify that the referenced aliases are actually model aliases or tool aliases.
- For support triage only, `DATA_DESIGNER_SKIP_MODEL_HEALTH_CHECKS=1` disables model health probes.

## 6) MCP tool aliases are absent

Likely cause:

- A model-generated column references `tool_alias`, but no MCP registry was configured.
- The configured MCP provider exists, but the expected tool name is not exposed by that server.

What to do:

- Use `list_mcp_tool_names(provider_name)` to confirm the provider handshake and discover the available tool names.
- If no MCP provider is configured, remove `tool_alias` or add the appropriate provider configuration.
- Remember that `validate()` does not guarantee MCP reachability.

## 7) Resume incompatibility

Symptoms:

- `ResumeMode.ALWAYS` refuses to continue
- `ResumeMode.IF_POSSIBLE` starts fresh unexpectedly
- the workflow says a stage is not reusable

What to do:

- Confirm `buffer_size` did not change.
- Confirm `preserve_dropped_columns` did not change.
- Confirm the config fingerprint still matches.
- For workflows, confirm the stage fingerprint, stage name, and selected output are unchanged.
- If the stored metadata is corrupt or missing required fields, rebuild from scratch instead of trying to force a resume.

## 8) Early shutdown after a partially successful run

Likely cause:

- the scheduler tripped the early-shutdown gate because the non-retryable error rate exceeded the threshold

What to do:

- Read the warnings above the failure for the actual root cause.
- Check whether any records were salvaged before shutdown.
- If you are triaging a flaky provider, consider increasing retries or disabling early shutdown for the investigation run.

## 9) Export problems

Symptoms:

- unsupported extension
- missing batch files
- parquet schema mismatch
- export path not found

What to do:

- Make sure the output directory already exists.
- Use a supported format: `jsonl`, `csv`, or `parquet`.
- If the dataset is complete but export still fails, inspect the batch files under `parquet-files/`.
- For parquet export, remember that schemas are unified permissively but still need to be compatible enough to cast.

## 10) `push_to_hub()` caveats

Symptoms:

- token/auth failures
- network failures
- workflow results reject the upload

What to do:

- Verify Hugging Face credentials before calling `push_to_hub()`.
- Use `export()` instead if you only need a local artifact.
- For workflow results, `push_to_hub()` only works when the final selected output is the raw final-stage dataset.
- If you selected a processor output or callback output, export that selected output or push the stage result directly.

## 11) TTY vs non-TTY logging differences

Symptoms:

- no progress panel
- only a few log lines appear
- output looks different in CI than in a local terminal

What to do:

- Set `display_tui=False` for CI and other non-interactive contexts.
- Remember that the throughput panel only renders when a TTY is present.
- `preview()` always uses log output; it does not render the throughput panel.
- If the run looks quiet, check whether stdout/stderr are attached to a terminal.

## 12) Log message to recognize

A healthy run usually starts by logging the chosen Jinja rendering engine.

If you see that line but no progress panel, the run is probably in a non-TTY context and has fallen back to logging as expected.
