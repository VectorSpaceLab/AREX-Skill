---
name: tracing-and-instrumentation
description: "Emit, inspect, adapt, and troubleshoot Agent Lightning spans,
  rewards, operation traces, OpenTelemetry/AgentOps tracers, and token-ID
  signals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tracing and instrumentation

Use this sub-skill when a task is about spans, rewards, trace collection, adapters, OpenTelemetry/AgentOps/Weave tracer choices, or missing token/logprob signals.

## Route by task

| Request | Read/run |
| --- | --- |
| Emit rewards, messages, objects, exceptions, or operation spans | [references/tracing-workflows.md](references/tracing-workflows.md) |
| Inspect final reward or convert traces for algorithms | [references/api-reference.md](references/api-reference.md) |
| Debug no spans, no active tracer, missing reward, disconnected spans, token IDs | [references/troubleshooting.md](references/troubleshooting.md) |
| Run a local no-service trace smoke | `python scripts/local_trace_smoke.py` |
| Start stores/proxies/metrics services | route to [../cli-and-services/SKILL.md](../cli-and-services/SKILL.md) |

## Key rules

- `OtelTracer` is the minimal local tracer for explicit OpenTelemetry and emitter tests.
- `AgentOpsTracer` is the default trainer tracer and instruments many LLM/agent frameworks locally.
- Emitters require an active tracer unless `propagate=False` is used for offline local span creation.
- Agent Lightning reward spans are annotation spans; use `find_final_reward` for the last reward value.
- Token IDs are optional signals. VERL/vLLM-style training may require token IDs from a compatible serving path; do not claim they exist unless the trace shows them.

## Minimal local pattern

```python
import agentlightning as agl

tracer = agl.OtelTracer()
store = agl.InMemoryLightningStore()
rollout = await store.start_rollout(input={"origin": "debug"})
with tracer.lifespan(store):
    async with tracer.trace_context(
        "debug-trace",
        store=store,
        rollout_id=rollout.rollout_id,
        attempt_id=rollout.attempt.attempt_id,
    ):
        agl.emit_message("hello")
        agl.emit_reward(1.0)
spans = await store.query_spans(rollout.rollout_id)
assert agl.find_final_reward(spans) == 1.0
```

The bundled `scripts/local_trace_smoke.py` runs this with extra operation, tag, link, and object assertions.

## Boundary

This sub-skill owns spans and adapters. It does not own agent function signatures, store status transitions, or service startup. Route those to [agent-authoring](../agent-authoring/SKILL.md), [runner-store-training](../runner-store-training/SKILL.md), and [cli-and-services](../cli-and-services/SKILL.md).
