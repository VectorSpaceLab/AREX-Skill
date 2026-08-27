# Tracing troubleshooting

## `No active tracer found`

**Symptom**

```text
RuntimeError: No active tracer found. Cannot emit ... span.
```

**Cause**

Emitter helpers send spans through the active tracer. No tracer context is active in the current process.

**Fix**

Use a tracer lifespan and trace context:

```python
with tracer.lifespan(store):
    async with tracer.trace_context("name", store=store, rollout_id=rid, attempt_id=aid):
        agl.emit_reward(1.0)
```

For offline unit tests that should not export spans, pass `propagate=False`.

## Empty spans after a rollout

**Possible causes**

- The agent returned `None` without emitting spans.
- The tracer was not attached to `LitAgentRunner`.
- The LLM/framework instrumentation was not installed or not supported.
- The store queried the wrong rollout or attempt.

**Fix**

1. Query the exact `rollout.rollout_id` returned by the runner.
2. Use `OtelTracer` and explicit emitters for a small reproducer.
3. Run `python scripts/local_trace_smoke.py` to prove local trace plumbing.
4. If framework auto-instrumentation is needed, switch to `AgentOpsTracer` and inspect raw spans.

## Final reward is `None`

**Possible causes**

- No reward span exists.
- A multi-dimensional reward was emitted without a valid primary dimension.
- The reward path failed before emitting.
- The adapter is using a different reward-matching policy than expected.

**Fix**

- For simple agents, return a `float`.
- For explicit emitters, call `emit_reward` after the final decision.
- Inspect `find_reward_spans(spans)` and `find_final_reward(spans)`.
- In advanced triplet conversion, configure `TracerTraceToTriplet` match policies deliberately.

## Operation span did not capture input/output

**Possible causes**

- `operation` was used without entering the context.
- `set_input` or `set_output` was called after the context exited.
- Inputs were not JSON-serializable after flattening/sanitization.

**Fix**

Use the context manager pattern:

```python
with agl.operation(name="tool-call") as op:
    op.set_input(query="...")
    result = run_tool()
    op.set_output(result)
```

## Missing token IDs in LLM traces

**Symptom**

Triplets or proxy spans contain prompt/response text but token ID arrays are empty or absent.

**Cause**

The serving backend does not return token IDs, the proxy did not request them, or spans came from a non-proxy OpenAI-compatible endpoint.

**Fix**

1. Confirm the task truly needs token IDs; prompt optimization may not.
2. Use a backend known to support token IDs, such as compatible vLLM versions.
3. Route service setup to `cli-and-services` and inspect LLM proxy spans for `raw_gen_ai_request`, `prompt_token_ids`, or provider token fields.
4. If token IDs are unavailable, document retokenization as a fallback and warn about drift.

## AgentOps or framework instrumentation conflict

**Symptom**

Duplicate spans, disconnected span hierarchy, or instrumentation warnings.

**Cause**

Multiple frameworks or tracing libraries can create overlapping OpenTelemetry spans.

**Fix**

- Start with `OtelTracer` plus explicit emitters to isolate Agent Lightning behavior.
- If using `AgentOpsTracer`, keep instrumentation setup consistent across all runner processes.
- Use `TracerTraceToTriplet(repair_hierarchy=True)` when hierarchy repair is appropriate.
- Do not mix experimental Weave tracing with other auto-instrumentation unless the environment was validated.

## OTLP/store identifier mismatch

**Symptom**

Spans reach a server but are not attached to the expected rollout/attempt.

**Cause**

OTLP resource attributes or proxy path headers are missing rollout ID, attempt ID, or sequence ID.

**Fix**

- Ensure the tracer context receives `rollout_id` and `attempt_id`.
- For `LLMProxy`, use attempt-specific paths or `ProxyLLM.get_base_url(rollout_id, attempt_id)`.
- Confirm the store advertises `capabilities["otlp_traces"]` before relying on OTLP ingestion.
