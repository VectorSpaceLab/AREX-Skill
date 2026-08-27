# Troubleshooting

This reference collects the semantic-convention failures that are easiest to misread.

## Quick diagnosis table

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `gen_ai.provider.name` is missing and `gen_ai.system` still appears | Legacy provider naming path is still active | Use the current upstream provider-name constant and remove deprecated system emission on new spans. |
| `gen_ai.input.messages` / `gen_ai.output.messages` are missing | Content tracing is disabled or the wrapper is in an attribute-suppressed path | Check the content gate and the provider's own semconv behavior. |
| `gen_ai.response.finish_reasons` disappears when content tracing is off | Finish reasons were gated together with prompt/output content | Keep finish reasons on the span; they are response metadata, not content. |
| JSON parsing fails for message payloads | The message schema is wrong | Verify the payload is a JSON array of message objects with `role` and `parts`. |
| `gen_ai.tool.definitions` is present in one provider but missing in another | Provider wrappers do not all gate tools the same way | Compare against that provider's semconv tests; do not assume one universal gate. |
| `SpanAttributes.LLM_*` works but the span value looks wrong | The alias is intentionally retained, but the string value may be old or already modern | Check the alias category before replacing it. |
| Imported upstream GenAI constants are unavailable | OTel semantic-conventions version drift | Align the installed `opentelemetry-semantic-conventions` package with the repo's expected API. |

## Version drift

The local compatibility layer depends on upstream OpenTelemetry GenAI symbols.
If the upstream package changes, you may see one of these patterns:

- Import failure for `opentelemetry.semconv._incubating.attributes.gen_ai_attributes`
- Missing `GEN_AI_PROVIDER_NAME`, `GEN_AI_INPUT_MESSAGES`, or `GEN_AI_RESPONSE_FINISH_REASONS`
- Enum member name drift in `GenAiSystemValues` or `GenAiOperationNameValues`

### Recovery approach

1. Re-run the bundled checker to see which symbol drifted.
2. Compare the installed upstream constants with the reference tables in `references/semantic-attributes.md`.
3. Update the generated skill references if the repo intentionally moved to a newer upstream semantic-conventions release.

## Deprecated `gen_ai.system`

`gen_ai.system` is the old provider/system field.
The new canonical field on spans is `gen_ai.provider.name`.

### Common confusion

- `gen_ai.system` may still exist in compatibility aliases or older tests.
- Provider-semconv assertions should prefer `gen_ai.provider.name`.
- Do not compare against the pretty class name. Compare against the normalized provider value.

## Content tracing and event mode

Content tracing is controlled by a provider-specific gate, usually `TRACELOOP_TRACE_CONTENT`, and sometimes by an override context value. Event mode is separate.

### Rules of thumb

- Message bodies belong in `gen_ai.input.messages` and `gen_ai.output.messages` only when content tracing is allowed.
- Some providers still keep metadata such as finish reasons even when content bodies are suppressed.
- Some wrappers emit events instead of span attributes when they are configured for event mode.
- `use_attributes` and the deprecated `use_legacy_attributes` switch between the attribute path and the legacy/event path in provider wrappers that support both.

### Tool-definition nuance

`gen_ai.tool.definitions` is not gated identically across every provider implementation. If one provider keeps tools while prompts are off, that can be intentional. Treat provider semconv tests as the source of truth.

## JSON message schema mistakes

The upstream message fields are structured JSON, not ad hoc strings.

### Input messages

A valid input message should look like:

```json
[
  {
    "role": "user",
    "parts": [
      {"type": "text", "content": "Hello"}
    ]
  }
]
```

### Output messages

A valid output message usually includes `finish_reason` and a `parts` array:

```json
[
  {
    "role": "assistant",
    "parts": [
      {"type": "text", "content": "Hi"}
    ],
    "finish_reason": "stop"
  }
]
```

### Allowed part types to remember

- `text`
- `tool_call`
- `tool_call_response`
- `blob`
- `uri`
- `reasoning`

If a provider emits a different structure, the semconv layer will usually fail downstream JSON assertions even if the raw span is technically present.

## Finish-reason placement

There are two related locations for finish information:

1. `gen_ai.response.finish_reasons` on the span.
2. Per-message `finish_reason` inside `gen_ai.output.messages`.

The span-level field is metadata and should survive content gating. The per-message field belongs to the output JSON payload and should still be populated when the payload itself is emitted.

### Why this matters

A span can legitimately suppress `gen_ai.output.messages` while still needing `gen_ai.response.finish_reasons` for observability. If both disappear, the wrapper is over-gating metadata.

## Legacy alias confusion

The compatibility layer keeps several alias families alive. The two most common mistakes are:

- Replacing every `LLM_*` name blindly, even when the alias already points at a modern `gen_ai.*` value.
- Keeping a compatibility alias in new code after the canonical `GEN_AI_*` name is available.

### Safe rule

Check the alias category before changing code:

- Old name + old value → migrate to the new `GEN_AI_*` name.
- Old name + modern value → migrate the Python name if you are touching the code path, but know that the payload is already in the modern namespace.
- New name + vendor-qualified old value → keep the new name; the vendor namespace is intentional.

## Bundled checker

Use `scripts/check_semconv_constants.py` when you want a quick no-network check that the installed semantic-convention layer still matches the expected values.

- `--json` prints a machine-readable report.
- A non-zero exit status means at least one imported constant or enum drifted.
