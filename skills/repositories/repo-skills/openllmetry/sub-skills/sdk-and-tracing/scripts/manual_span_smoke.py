#!/usr/bin/env python3
"""No-network smoke for manual Traceloop LLM span reporting.

This helper adapts the repository's credentialed manual logging example into a
safe local check. It initializes Traceloop with an in-memory exporter, reports a
synthetic LLM request/response/usage through ``track_llm_call``, and asserts the
expected span attributes without calling a provider API.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes as GenAIAttributes
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from opentelemetry.semconv_ai import SpanAttributes
from traceloop.sdk import Traceloop
from traceloop.sdk.tracing.manual import LLMMessage, LLMUsage, track_llm_call
from traceloop.sdk.tracing.tracing import TracerWrapper


def reset_traceloop_singleton() -> None:
    if hasattr(TracerWrapper, "instance"):
        del TracerWrapper.instance


def main() -> None:
    reset_traceloop_singleton()
    exporter = InMemorySpanExporter()
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        Traceloop.init(
            app_name="manual-span-smoke",
            disable_batch=True,
            exporter=exporter,
            instruments=set(),
        )

    with track_llm_call(vendor="openai", type="chat") as span:
        span.report_request(
            model="gpt-4o-mini",
            messages=[LLMMessage(role="user", content="Explain OpenTelemetry in one sentence.")],
        )
        span.report_response(
            model="gpt-4o-mini-2024-07-18",
            completions=["OpenTelemetry standardizes traces, metrics, and logs."],
        )
        span.report_usage(LLMUsage(prompt_tokens=8, completion_tokens=7, total_tokens=15))

    spans = list(exporter.get_finished_spans())
    assert len(spans) == 1, [s.name for s in spans]
    llm_span = spans[0]
    attrs = llm_span.attributes

    assert llm_span.name == "openai.chat"
    assert attrs[GenAIAttributes.GEN_AI_SYSTEM] == "openai"
    assert attrs[SpanAttributes.LLM_REQUEST_TYPE] == "chat"
    assert attrs[GenAIAttributes.GEN_AI_REQUEST_MODEL] == "gpt-4o-mini"
    assert attrs[GenAIAttributes.GEN_AI_RESPONSE_MODEL] == "gpt-4o-mini-2024-07-18"
    assert attrs[GenAIAttributes.GEN_AI_USAGE_INPUT_TOKENS] == 8
    assert attrs[GenAIAttributes.GEN_AI_USAGE_OUTPUT_TOKENS] == 7
    assert attrs[SpanAttributes.LLM_USAGE_TOTAL_TOKENS] == 15
    assert attrs[f"{GenAIAttributes.GEN_AI_PROMPT}.0.role"] == "user"
    assert attrs[f"{GenAIAttributes.GEN_AI_COMPLETION}.0.role"] == "assistant"

    print(
        json.dumps(
            {
                "span_name": llm_span.name,
                "request_model": attrs[GenAIAttributes.GEN_AI_REQUEST_MODEL],
                "response_model": attrs[GenAIAttributes.GEN_AI_RESPONSE_MODEL],
                "total_tokens": attrs[SpanAttributes.LLM_USAGE_TOTAL_TOKENS],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
