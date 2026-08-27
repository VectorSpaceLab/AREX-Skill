# Tracing & Observability Workflows

Use these patterns as self-contained guidance for future agents. They avoid calls to original repository examples and do not require trace export unless the application explicitly supplies credentials.

## Enable or Disable Tracing

Tracing is enabled by default. For one run, keep the decision local to `RunConfig`:

```python
from agents import RunConfig, Runner

result = await Runner.run(
    agent,
    "Summarize the incident.",
    run_config=RunConfig(
        workflow_name="incident-summary",
        group_id="ticket-123",
        tracing_disabled=False,
    ),
)
```

Disable one run when exporting spans would be inappropriate:

```python
await Runner.run(
    agent,
    "Handle private input.",
    run_config=RunConfig(tracing_disabled=True),
)
```

Disable process-wide tracing only at application startup or in tightly scoped tests:

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)
```

Environment-based disabling must be set before first tracing provider use:

```bash
export OPENAI_AGENTS_DISABLE_TRACING=1
```

## Exclude Sensitive Trace Payloads

Use `trace_include_sensitive_data=False` when model inputs/outputs or tool inputs/outputs can contain secrets, regulated data, or customer content:

```python
from agents import RunConfig, Runner

run_config = RunConfig(
    workflow_name="support-triage",
    group_id="case-8721",
    trace_include_sensitive_data=False,
    trace_metadata={"component": "triage", "env": "prod"},
)

result = await Runner.run(agent, user_message, run_config=run_config)
```

Hardening checklist:

- Keep `trace_metadata` free of raw user text, API keys, tenant secrets, and local paths.
- Keep `OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1` and `OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1` unless debugging in a safe sandbox.
- Redact exception messages and traceback logging separately; trace redaction does not rewrite exception chains.
- Ensure custom processors do not copy sensitive payloads into their own logs, metrics, or side-channel exports.

## Group Multiple Runs in One Trace

Wrap related `Runner.run` calls in `trace()` when they should appear as one workflow:

```python
from agents import Runner, trace

with trace(
    workflow_name="research-workflow",
    group_id="thread-abc",
    metadata={"source": "web-ui"},
):
    first = await Runner.run(planner_agent, "Plan the research.")
    final = await Runner.run(writer_agent, f"Write from plan: {first.final_output}")
```

Prefer the context-manager form over manual `start()` and `finish()` calls. If a trace is already active, creating a second trace logs a warning and is usually a design mistake.

## Use a Per-Run Trace Export Key

When model calls use one key or provider but trace export should use an OpenAI trace key, configure the provider/model separately and pass the tracing key only at the tracing layer:

```python
from agents import RunConfig, Runner

run_config = RunConfig(
    workflow_name="third-party-model-workflow",
    tracing={"api_key": tracing_key},
)

await Runner.run(agent, "Hello", run_config=run_config)
```

Do not log `tracing_key`, include it in metadata, or persist it in application state. Route provider key/client setup to [../../models-providers/SKILL.md](../../models-providers/SKILL.md).

## Add a Local-Only Custom Processor

Use `set_trace_processors()` for a smoke test that proves traces/spans are produced without exporting externally:

```python
from agents import TracingProcessor, custom_span, set_trace_processors, trace

class CountingProcessor(TracingProcessor):
    def __init__(self) -> None:
        self.trace_starts = 0
        self.trace_ends = 0
        self.span_starts = 0
        self.span_ends = 0

    def on_trace_start(self, trace) -> None:
        self.trace_starts += 1

    def on_trace_end(self, trace) -> None:
        self.trace_ends += 1

    def on_span_start(self, span) -> None:
        self.span_starts += 1

    def on_span_end(self, span) -> None:
        self.span_ends += 1

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass

processor = CountingProcessor()
set_trace_processors([processor])

with trace("local-smoke", group_id="demo"):
    with custom_span("local-step", {"safe": True}):
        pass

assert processor.trace_starts == 1
assert processor.trace_ends == 1
assert processor.span_starts == 1
assert processor.span_ends == 1
```

Use `add_trace_processor()` instead when production should keep the default OpenAI exporter and also feed a secondary processor. Use `set_trace_processors([])` only in tests or local tools where external export is intentionally disabled.

## Flush Short-Lived Jobs

The default batch processor exports periodically in a background thread and flushes at process exit. For short-lived jobs, serverless handlers, queue workers, or background tasks that need immediate visibility, call `flush_traces()` after the trace context exits:

```python
from agents import Runner, flush_traces, trace

try:
    with trace("queue-job", group_id=job_id):
        result = Runner.run_sync(agent, payload)
finally:
    flush_traces()
```

Do not call `flush_traces()` while the trace context is still open if you need a complete trace payload.

## Collect Usage

Read usage from the run context after a run:

```python
result = await Runner.run(agent, "What's the weather in Tokyo?")
usage = result.context_wrapper.usage

summary = {
    "requests": usage.requests,
    "input_tokens": usage.input_tokens,
    "output_tokens": usage.output_tokens,
    "total_tokens": usage.total_tokens,
    "per_request": [
        {
            "input_tokens": request.input_tokens,
            "output_tokens": request.output_tokens,
            "total_tokens": request.total_tokens,
        }
        for request in usage.request_usage_entries
    ],
}
```

For streamed third-party adapter calls, set `ModelSettings(include_usage=True)` if the upstream provider only emits usage in dedicated stream chunks. Validate adapter behavior under [../../models-providers/SKILL.md](../../models-providers/SKILL.md).

## Add Usage Logging Safely

Log aggregate counts, not prompts or tool payloads:

```python
import logging
from typing import Any

from agents import Agent, RunContextWrapper, RunHooks

logger = logging.getLogger("myapp.agent_usage")

class UsageHooks(RunHooks):
    async def on_agent_end(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        output: Any,
    ) -> None:
        usage = context.usage
        logger.info(
            "agent=%s requests=%s input_tokens=%s output_tokens=%s total_tokens=%s",
            agent.name,
            usage.requests,
            usage.input_tokens,
            usage.output_tokens,
            usage.total_tokens,
        )
```

Avoid logging `output`, raw prompts, tool arguments, or trace metadata values unless a separate redaction policy is in place.

## Generate a Visualization

Use the optional visualization extension to inspect agent topology:

```python
from agents.extensions.visualization import draw_graph

graph = draw_graph(triage_agent)
print(graph.source)  # DOT string, no rendering required.
```

Render a PNG when the Python `graphviz` package and system Graphviz executable are installed:

```python
draw_graph(triage_agent, filename="agent_graph")
```

For CI or headless environments, inspect `graph.source` rather than opening a viewer. If the import fails, install the optional visualization dependency and system Graphviz package appropriate for the target environment.

## Safe Config Check

Run the bundled helper before diagnosing local tracing issues:

```bash
python scripts/check_tracing_config.py --json
```

The helper imports tracing APIs, evaluates relevant env/config flags, checks optional Graphviz availability, and can run a local-only custom processor smoke test without exporting traces or making API calls.
