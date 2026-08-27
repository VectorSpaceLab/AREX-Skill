#!/usr/bin/env python3
"""Offline-safe MLflow tracing smoke probe."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe local MLflow tracing smoke test with manual spans and trace search.",
    )
    parser.add_argument(
        "--experiment-name",
        default="genai-observability-smoke",
        help="Experiment name to create or reuse in the temporary local tracking store.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        import mlflow
    except ModuleNotFoundError as exc:
        if exc.name == "mlflow":
            raise SystemExit(
                "MLflow is not importable. Install MLflow in the active Python environment, "
                "then rerun this smoke script."
            ) from exc
        raise

    tracking_dir = tempfile.TemporaryDirectory(prefix="mlflow-tracing-smoke-")
    tracking_db = Path(tracking_dir.name) / "mlflow.db"
    tracking_uri = f"sqlite:///{tracking_db}"
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(args.experiment_name)

    @mlflow.trace(name="retrieve_context", span_type="RETRIEVER", attributes={"source": "local"})
    def retrieve_context(question: str) -> list[str]:
        return ["MLflow tracing records spans", "GenAI evaluation can score traces"]

    @mlflow.trace(name="rag_answer", span_type="CHAIN", attributes={"app": "smoke"})
    def rag_answer(question: str) -> str:
        docs = retrieve_context(question)
        with mlflow.start_span(name="compose_answer", attributes={"doc_count": len(docs)}) as span:
            span.set_inputs({"question": question, "docs": docs})
            answer = f"MLflow observed {len(docs)} local context documents."
            span.set_outputs(answer)
            return answer

    output = rag_answer("How can I smoke test MLflow tracing?")
    flush = getattr(mlflow, "flush_trace_async_logging", None)
    if callable(flush):
        try:
            flush()
        except TypeError:
            flush(terminate=False)

    trace_id = mlflow.get_last_active_trace_id()
    if trace_id is None:
        raise RuntimeError("No active trace id was recorded")

    try:
        trace = mlflow.get_trace(trace_id, flush=True)
    except TypeError:
        trace = mlflow.get_trace(trace_id)
    if trace is None:
        raise RuntimeError(f"Trace {trace_id} could not be loaded")

    traces = mlflow.search_traces(filter_string="timestamp > 0", max_results=5)
    data = getattr(trace, "data", None)
    spans = getattr(data, "spans", None)
    span_count = len(spans) if spans is not None else None
    if span_count is not None and span_count < 2:
        raise RuntimeError(f"Expected at least 2 spans, found {span_count}")

    print(
        json.dumps(
            {
                "ok": True,
                "tracking_uri": tracking_uri,
                "trace_id": trace_id,
                "output": output,
                "span_count": span_count,
                "search_count": len(traces),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
