# SDK workflows

These recipes are trimmed from the bundled smoke scripts and the repo tests. Use them for no-network tracing, endpoint setup, decorator patterns, manual spans, and the higher-level SDK client surfaces.

## 1) No-network decorator smoke

Use this pattern when you want to prove that workflows, agents, tasks, tools, and association properties are wired correctly without calling any provider API.

```python
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import conversation, workflow, agent, task, tool

exporter = InMemorySpanExporter()
Traceloop.init(
    app_name="demo",
    disable_batch=True,
    exporter=exporter,
    instruments=set(),
)

@tool(name="offline_lookup")
def offline_lookup(subject: str) -> str:
    return f"lookup:{subject}"

@task(name="offline_task", version=2)
def build_reply(prompt: str):
    return {"prompt": prompt, "lookup": offline_lookup(prompt)}

@agent(name="offline_agent", method_name="generate")
class OfflineAgent:
    def generate(self, prompt: str):
        return build_reply(prompt)

@conversation("conv-001")
@workflow(name="offline_workflow", version=1)
def run_flow():
    Traceloop.set_association_properties({"user_id": "user-123"})
    return OfflineAgent().generate("otel")
```

What to check:
- span names are ordered and scoped as `offline_lookup.tool`, `offline_task.task`, `offline_agent.agent`, `offline_workflow.workflow`
- `TRACELOOP_ENTITY_NAME`, `TRACELOOP_ENTITY_VERSION`, and `TRACELOOP_SPAN_KIND` appear on the expected spans
- `TRACELOOP_ENTITY_INPUT` and `TRACELOOP_ENTITY_OUTPUT` are present while `TRACELOOP_TRACE_CONTENT=true`
- conversation ID and association properties propagate to child spans

For a ready-made runnable version, use [`scripts/offline_tracing_smoke.py`](../scripts/offline_tracing_smoke.py).

## 2) Local OTLP or Traceloop endpoint setup

Choose the endpoint by scheme:

```python
from traceloop.sdk import Traceloop

# Local OTLP over HTTP
Traceloop.init(app_name="svc", api_endpoint="http://localhost:4318", disable_batch=True)

# Local OTLP over gRPC
Traceloop.init(app_name="svc", api_endpoint="grpc://localhost:4317", disable_batch=True)

# Traceloop cloud
Traceloop.init(
    app_name="svc",
    api_key="...",
    api_endpoint="https://api.traceloop.com",
)
```

What to check:
- HTTP endpoints are normalized to `/v1/traces`
- gRPC endpoints stay on the host/port pair
- Traceloop cloud initialization returns a client only when no custom exporter/processor is supplied

## 3) Multiple processors and redaction

Use this when you need a Traceloop processor plus your own processor(s).

```python
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from traceloop.sdk import Traceloop

primary = InMemorySpanExporter()
default_processor = Traceloop.get_default_span_processor(disable_batch=True, exporter=primary)
audit_processor = SimpleSpanProcessor(ConsoleSpanExporter())

Traceloop.init(processor=[default_processor, audit_processor])
```

If you also pass `exporter=...`, the exporter is ignored and Traceloop warns you.

For span redaction, keep the default processor path and supply `span_postprocess_callback`:

```python
def redact(span):
    attrs = getattr(span, "_attributes", None)
    if attrs and "gen_ai.input.messages" in attrs:
        attrs["gen_ai.input.messages"] = "REDACTED"

Traceloop.init(exporter=primary, span_postprocess_callback=redact)
```

If you use your own processor list, move redaction into that processor instead.

## 4) Decorator patterns

Function style:

```python
from traceloop.sdk.decorators import workflow, task, tool

@workflow(name="ingest")
def ingest():
    ...

@task(name="summarize")
def summarize(text: str):
    ...

@tool(name="lookup")
def lookup(query: str):
    ...
```

Class/method style:

```python
from traceloop.sdk.decorators import agent

@agent(name="planner", method_name="generate")
class Planner:
    def generate(self, prompt: str):
        return prompt
```

Guidance:
- Use `method_name=` for class decoration.
- `@agent` and `@tool` are just `workflow`/`task` specializations with different span kinds.
- Sync, async, generator, and async-generator callables are all supported.
- `@conversation` should wrap the outer workflow when you want one conversation ID across nested spans.

## 5) Manual LLM spans

Use `track_llm_call` when you want to emit LLM spans without a provider SDK call.

```python
from traceloop.sdk.tracing.manual import LLMMessage, LLMUsage, track_llm_call

with track_llm_call(vendor="openai", type="chat") as span:
    span.report_request(
        model="gpt-4o-mini",
        messages=[LLMMessage(role="user", content="Hello")],
    )
    span.report_response("gpt-4o-mini", ["Hello back"])
    span.report_usage(
        LLMUsage(prompt_tokens=12, completion_tokens=8, total_tokens=20)
    )
```

What to check:
- the span name is `openai.chat`
- `gen_ai.system` and `llm.request.type` are set
- request, response, and token usage attributes land on the same span

For a ready-made runnable version, use [`scripts/manual_span_smoke.py`](../scripts/manual_span_smoke.py).

## 6) Prompt, dataset, experiment, and guardrail surfaces

Prompt tracing context:

```python
from traceloop.sdk import Traceloop

@workflow(name="chat")
def chat():
    Traceloop.set_prompt("Tell me a {thing}", {"thing": "joke"}, 1)
    ...
```

Client surfaces:

```python
client = Traceloop.get()
client.user_feedback.create("annotation-task", "entity-123", {"sentiment": "positive"})
client.datasets.get_all()
client.datasets.from_csv("data.csv", slug="demo")
await client.experiment.run(task_callable, evaluators=["accuracy"])
```

Guardrails:

```python
from traceloop.sdk.guardrail import Guardrails, pii_guard

guard = Guardrails(pii_guard(), name="safe-output").run_all().raise_on_failure()
result = await guard.run(generate_text)
```

What to check:
- client APIs require a valid API key and endpoint
- `Experiment.run` is async
- `run_in_github` only works inside GitHub Actions pull_request jobs
- `from_dataframe` requires the `datasets` extra / pandas

## 7) Privacy and content controls

```python
Traceloop.init(
    app_name="svc",
    exporter=exporter,
    use_attributes=True,
)
```

Guidance:
- `use_attributes=True` keeps prompt/completion data on spans.
- `use_attributes=False` switches to the event path and requires an event logger provider.
- `TRACELOOP_TRACE_CONTENT=false` suppresses decorated entity inputs/outputs.
- If content still appears, check the allow-list or any redaction callback in use.

For attribute names and exact semantic values, jump to `../../semantic-conventions/SKILL.md`.
