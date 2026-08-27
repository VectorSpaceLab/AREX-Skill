#!/usr/bin/env python
"""Deterministic smoke check for Haystack evaluation and local observability APIs."""

from __future__ import annotations

import logging

from haystack import Document, Pipeline, component, tracing
from haystack.components.evaluators import AnswerExactMatchEvaluator, DocumentNDCGEvaluator, DocumentRecallEvaluator
from haystack.evaluation import EvaluationRunResult
from haystack.tracing.logging_tracer import LoggingTracer


@component
class EchoComponent:
    @component.output_types(output=str)
    def run(self, text: str) -> dict[str, str]:
        return {"output": text.upper()}


def main() -> None:
    logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=logging.WARNING)
    logging.getLogger("haystack").setLevel(logging.DEBUG)

    france = Document(content="Paris is the capital of France.", id="france")
    germany = Document(content="Berlin is the capital of Germany.", id="germany")
    italy = Document(content="Rome is the capital of Italy.", id="italy")

    ground_truth_documents = [[france], [germany]]
    retrieved_documents = [[france, italy], [italy]]

    recall = DocumentRecallEvaluator(mode="single_hit", document_comparison_field="id").run(
        ground_truth_documents=ground_truth_documents,
        retrieved_documents=retrieved_documents,
    )
    ndcg = DocumentNDCGEvaluator().run(
        ground_truth_documents=ground_truth_documents,
        retrieved_documents=retrieved_documents,
    )
    exact_match = AnswerExactMatchEvaluator().run(
        ground_truth_answers=["Paris", "Berlin"],
        predicted_answers=["Paris", "Munich"],
    )

    assert recall["individual_scores"] == [1.0, 0.0]
    assert recall["score"] == 0.5
    assert ndcg["individual_scores"] == [1.0, 0]
    assert ndcg["score"] == 0.5
    assert exact_match["individual_scores"] == [1, 0]
    assert exact_match["score"] == 0.5

    run = EvaluationRunResult(
        run_name="smoke",
        inputs={"question": ["Capital of France?", "Capital of Germany?"]},
        results={
            "recall": recall,
            "ndcg": ndcg,
            "exact_match": exact_match,
        },
    )
    aggregated = run.aggregated_report(output_format="json")
    detailed = run.detailed_report(output_format="json")

    assert aggregated == {"metrics": ["recall", "ndcg", "exact_match"], "score": [0.5, 0.5, 0.5]}
    assert detailed["question"] == ["Capital of France?", "Capital of Germany?"]
    assert detailed["recall"] == [1.0, 0.0]

    tracing.enable_tracing(LoggingTracer())
    assert tracing.is_tracing_enabled()

    pipeline = Pipeline()
    pipeline.add_component("echo", EchoComponent())
    pipeline_result = pipeline.run(data={"text": "haystack"})
    assert pipeline_result["echo"]["output"] == "HAYSTACK"

    tracing.disable_tracing()
    tracing.tracer.is_content_tracing_enabled = False

    print("evaluation-and-observability smoke check passed")


if __name__ == "__main__":
    main()
