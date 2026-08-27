# Evaluation and Observability API Reference

## Public imports

```python
from haystack import Document, Pipeline, component, logging, tracing
from haystack.components.evaluators import (
    AnswerExactMatchEvaluator,
    ContextRelevanceEvaluator,
    DocumentMAPEvaluator,
    DocumentMRREvaluator,
    DocumentNDCGEvaluator,
    DocumentRecallEvaluator,
    FaithfulnessEvaluator,
    LLMEvaluator,
    SASEvaluator,
)
from haystack.components.evaluators.document_recall import RecallMode
from haystack.evaluation import EvaluationRunResult
from haystack.tracing import disable_tracing, enable_tracing, is_tracing_enabled, tracer
from haystack.tracing.logging_tracer import LoggingTracer
```

Use `haystack.components.evaluators` for component imports and `haystack.evaluation.EvaluationRunResult` for report aggregation. Observability APIs live under `haystack.tracing`, `haystack.tracing.logging_tracer`, `haystack.logging`, and Python's standard `logging` module.

## Statistical document evaluators

### `DocumentRecallEvaluator`

Constructor:

```python
DocumentRecallEvaluator(
    mode: str | RecallMode = RecallMode.SINGLE_HIT,
    document_comparison_field: str = "content",
)
```

Run inputs and outputs:

```python
result = evaluator.run(
    ground_truth_documents=[[Document(content="Paris", meta={"id": "a"})]],
    retrieved_documents=[[Document(content="Paris", meta={"id": "a"})]],
)
assert result == {"score": 1.0, "individual_scores": [1.0]}
```

- `mode="single_hit"` returns `1.0` if any expected document is retrieved for a query.
- `mode="multi_hit"` returns the fraction of unique expected documents retrieved.
- `document_comparison_field="content"` compares `doc.content`; use `"id"` for stable IDs or `"meta.<key>"` / `"meta.nested.key"` for metadata.
- Inputs must be nested lists with matching outer length.

### `DocumentNDCGEvaluator`

```python
result = DocumentNDCGEvaluator().run(
    ground_truth_documents=[[Document(content="A", score=1.0), Document(content="B", score=0.5)]],
    retrieved_documents=[[Document(content="A"), Document(content="C"), Document(content="B")]],
)
```

- Output keys are `score` and `individual_scores`.
- Uses `Document.id` matching internally; construct ground-truth and retrieved documents so matching content produces the same document identity or reuse the same `Document` instances/IDs.
- Ground-truth relevance can be binary or scored, but do not mix scored and unscored documents within the same ground-truth list.
- `score` is average NDCG across queries; `individual_scores` identify weak samples.

### `DocumentMRREvaluator` and `DocumentMAPEvaluator`

Use these when rank order matters:

```python
from haystack.components.evaluators import DocumentMRREvaluator, DocumentMAPEvaluator

mrr = DocumentMRREvaluator().run(ground_truth_documents=truth, retrieved_documents=retrieved)
map_score = DocumentMAPEvaluator().run(ground_truth_documents=truth, retrieved_documents=retrieved)
```

- MRR rewards placing the first relevant document early.
- MAP rewards retrieving all relevant documents early.
- As with other document evaluators, keep `ground_truth_documents` and `retrieved_documents` aligned by query.

## Answer evaluators

### `AnswerExactMatchEvaluator`

```python
result = AnswerExactMatchEvaluator().run(
    ground_truth_answers=["Berlin", "Paris"],
    predicted_answers=["Berlin", "Lyon"],
)
assert result["individual_scores"] == [1, 0]
assert result["score"] == 0.5
```

- Exact match is deterministic and case/punctuation sensitive.
- Normalize answers yourself before calling if case-folding, whitespace collapse, or punctuation removal is desired.
- `ground_truth_answers` and `predicted_answers` must have the same length.

### `SASEvaluator`

`SASEvaluator` scores semantic answer similarity and may require model downloads or optional ML dependencies. Use it when exact string matching is too strict and offline/model availability is acceptable. Validate installation and warm-up before relying on it in CI.

## LLM evaluators

### `LLMEvaluator`

Constructor shape:

```python
evaluator = LLMEvaluator(
    instructions="Return 1 if the answer is safe, otherwise 0.",
    inputs=[("predicted_answers", list[str])],
    outputs=["score"],
    examples=[
        {"inputs": {"predicted_answers": "A neutral answer."}, "outputs": {"score": 1}},
        {"inputs": {"predicted_answers": "A harmful answer."}, "outputs": {"score": 0}},
    ],
    progress_bar=False,
    raise_on_failure=False,
)
result = evaluator.run(predicted_answers=["A neutral answer."])
```

- If `chat_generator` is omitted, the default is an OpenAI chat generator configured for JSON output and seeded generation; it needs the provider credential expected by that generator.
- For non-OpenAI providers, pass a `chat_generator` that returns JSON text with all requested output keys.
- `inputs` must be tuples of input name and a list type annotation such as `list[str]` or `list[list[str]]`; runtime values must be lists of equal length.
- `raise_on_failure=False` returns `None` entries and logs warnings instead of aborting the whole run.

### `ContextRelevanceEvaluator`

```python
result = ContextRelevanceEvaluator(progress_bar=False).run(
    questions=["Who created Python?"],
    contexts=[["Python was created by Guido van Rossum."]],
)
```

- Inputs are `questions: list[str]` and `contexts: list[list[str]]`.
- Outputs include `score` and `results`; each result contains `relevant_statements` and a binary per-sample `score`.
- Requires an LLM backend unless a compatible `chat_generator` is supplied.

### `FaithfulnessEvaluator`

```python
result = FaithfulnessEvaluator(progress_bar=False).run(
    questions=["Who created Python?"],
    contexts=[["Python was created by Guido van Rossum."]],
    predicted_answers=["Python was created by Guido van Rossum."],
)
```

- Inputs are `questions`, `contexts`, and `predicted_answers`.
- Outputs include `score`, `individual_scores`, and `results` with extracted `statements` and `statement_scores`.
- A low score means generated statements are unsupported by the supplied contexts, not necessarily that the answer is globally false.

## `EvaluationRunResult`

Create report objects from aligned inputs and evaluator outputs:

```python
run = EvaluationRunResult(
    run_name="baseline",
    inputs={"question": ["q1", "q2"]},
    results={
        "recall": {"score": 0.5, "individual_scores": [1.0, 0.0]},
        "exact_match": {"score": 0.5, "individual_scores": [1, 0]},
    },
)

aggregated = run.aggregated_report(output_format="json")
detailed = run.detailed_report(output_format="json")
```

Report methods:

- `aggregated_report(output_format="json" | "csv" | "df", csv_file=None)` returns metric names and aggregate scores.
- `detailed_report(output_format="json" | "csv" | "df", csv_file=None)` returns inputs plus per-sample scores.
- `comparative_detailed_report(other, keep_columns=None, output_format="json", csv_file=None)` compares two runs.

Validation rules:

- `inputs` cannot be empty.
- All input lists must have equal length.
- Every metric result must include `score` and `individual_scores`.
- Every `individual_scores` list must match the input sample count.
- `output_format="df"` requires `pandas`; `output_format="csv"` requires `csv_file`.

## Tracing APIs

Core functions:

```python
from haystack import tracing
from haystack.tracing.logging_tracer import LoggingTracer

tracing.enable_tracing(LoggingTracer())
assert tracing.is_tracing_enabled()
tracing.disable_tracing()
```

Important environment variables:

- `HAYSTACK_AUTO_TRACE_ENABLED=false` disables automatic OpenTelemetry/Datadog detection.
- `HAYSTACK_CONTENT_TRACING_ENABLED=true` allows content tags such as component inputs/outputs to be recorded.

Content tracing can also be toggled in code:

```python
from haystack import tracing

tracing.tracer.is_content_tracing_enabled = True
```

Keep it disabled by default for production or user data unless payloads are sanitized.

## `LoggingTracer`

```python
import logging
from haystack import tracing
from haystack.tracing.logging_tracer import LoggingTracer

logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=logging.WARNING)
logging.getLogger("haystack").setLevel(logging.DEBUG)

tracing.enable_tracing(
    LoggingTracer(
        tags_color_strings={
            "haystack.component.input": "\x1b[1;31m",
            "haystack.component.name": "\x1b[1;34m",
        }
    )
)
```

- Emits DEBUG log records for span operation names and tags.
- Typical operation names include `haystack.pipeline.run` and `haystack.component.run`.
- Common tag names include `haystack.component.name`, `haystack.component.type`, `haystack.component.input`, and `haystack.component.output`.
- Content input/output tags are emitted only when content tracing is enabled.

## Backend tracing

- OpenTelemetry can be auto-detected when an SDK tracer provider is configured before Haystack import, or enabled explicitly with `OpenTelemetryTracer` from `haystack.tracing.opentelemetry`.
- Datadog can be auto-detected when `ddtrace` is installed and enabled, or configured via Haystack Datadog integrations.
- Custom tracing requires implementing the `Tracer` interface with `trace(operation_name, tags=None, parent_span=None)` and `current_span()` plus a `Span` with `set_tag()`.
- Optional backend packages are not part of the minimal `haystack-ai` install; treat missing backend imports as optional dependency issues.

## Logging and telemetry controls

Standard logging:

```python
import logging

logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=logging.WARNING)
logging.getLogger("haystack").setLevel(logging.INFO)
```

Structured logging:

```python
import haystack.logging

haystack.logging.configure_logging(use_json=True)
```

Telemetry opt-out:

```bash
export HAYSTACK_TELEMETRY_ENABLED=False
```

Telemetry events are intended to exclude IP addresses, hostnames, file paths, queries, and document contents, but privacy-sensitive deployments should set `HAYSTACK_TELEMETRY_ENABLED=False` before importing and running Haystack.
