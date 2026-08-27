"""No-network smoke for Traceloop decorator tracing.

This smoke initializes Traceloop with an in-memory exporter, exercises the
workflow/agent/task/tool/decorator stack, and checks that span names and core
entity attributes are populated without calling any provider API.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from opentelemetry.semconv._incubating.attributes import (
    gen_ai_attributes as GenAIAttributes,
)
from opentelemetry.semconv_ai import SpanAttributes
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import agent, conversation, task, tool, workflow
from traceloop.sdk.tracing.tracing import TracerWrapper


def reset_traceloop_singleton() -> None:
    if hasattr(TracerWrapper, "instance"):
        del TracerWrapper.instance


def init_exporter() -> InMemorySpanExporter:
    reset_traceloop_singleton()
    exporter = InMemorySpanExporter()
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        Traceloop.init(
            app_name="sdk-and-tracing-offline-smoke",
            disable_batch=True,
            exporter=exporter,
            instruments=set(),
            resource_attributes={"scenario": "sdk-and-tracing-offline-smoke"},
        )
    return exporter


@tool(name="offline_lookup")
def offline_lookup(subject: str) -> str:
    return f"lookup:{subject}"


@task(name="offline_task", version=2)
def build_reply(prompt: str) -> dict[str, Any]:
    lookup = offline_lookup(prompt)
    return {"prompt": prompt, "lookup": lookup}


@agent(name="offline_agent", method_name="generate")
class OfflineAgent:
    def generate(self, prompt: str) -> dict[str, Any]:
        return build_reply(prompt)


@conversation("conv-offline-001")
@workflow(name="offline_workflow", version=1)
def run_flow() -> dict[str, Any]:
    Traceloop.set_association_properties({"user_id": "user-123"})
    return OfflineAgent().generate("otel")


def main() -> None:
    exporter = init_exporter()
    result = run_flow()
    spans = list(exporter.get_finished_spans())

    expected_names = [
        "offline_lookup.tool",
        "offline_task.task",
        "offline_agent.agent",
        "offline_workflow.workflow",
    ]
    actual_names = [span.name for span in spans]
    assert actual_names == expected_names, actual_names
    assert result == {"prompt": "otel", "lookup": "lookup:otel"}

    association_key = f"{SpanAttributes.TRACELOOP_ASSOCIATION_PROPERTIES}.user_id"

    tool_span, task_span, agent_span, workflow_span = spans
    assert workflow_span.parent is None
    assert agent_span.parent.span_id == workflow_span.context.span_id
    assert task_span.parent.span_id == agent_span.context.span_id
    assert tool_span.parent.span_id == task_span.context.span_id

    for span in spans:
        assert span.attributes[GenAIAttributes.GEN_AI_CONVERSATION_ID] == "conv-offline-001"
        assert span.attributes[association_key] == "user-123"
        assert span.attributes[SpanAttributes.TRACELOOP_WORKFLOW_NAME] == "offline_workflow"

    assert tool_span.attributes[SpanAttributes.TRACELOOP_SPAN_KIND] == "tool"
    assert tool_span.attributes[GenAIAttributes.GEN_AI_TOOL_NAME] == "offline_lookup"

    assert task_span.attributes[SpanAttributes.TRACELOOP_SPAN_KIND] == "task"
    assert task_span.attributes[SpanAttributes.TRACELOOP_ENTITY_NAME] == "offline_task"
    assert task_span.attributes[SpanAttributes.TRACELOOP_ENTITY_VERSION] == 2
    assert json.loads(task_span.attributes[SpanAttributes.TRACELOOP_ENTITY_INPUT]) == {
        "args": ["otel"],
        "kwargs": {},
    }
    assert json.loads(task_span.attributes[SpanAttributes.TRACELOOP_ENTITY_OUTPUT]) == {
        "prompt": "otel",
        "lookup": "lookup:otel",
    }

    assert agent_span.attributes[SpanAttributes.TRACELOOP_SPAN_KIND] == "agent"
    assert agent_span.attributes[SpanAttributes.TRACELOOP_ENTITY_NAME] == "offline_agent"

    assert workflow_span.attributes[SpanAttributes.TRACELOOP_SPAN_KIND] == "workflow"
    assert workflow_span.attributes[SpanAttributes.TRACELOOP_ENTITY_NAME] == "offline_workflow"
    assert workflow_span.attributes[SpanAttributes.TRACELOOP_ENTITY_VERSION] == 1

    print(
        json.dumps(
            {
                "result": result,
                "span_names": actual_names,
                "conversation_id": workflow_span.attributes[
                    GenAIAttributes.GEN_AI_CONVERSATION_ID
                ],
                "association_user_id": workflow_span.attributes[association_key],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
