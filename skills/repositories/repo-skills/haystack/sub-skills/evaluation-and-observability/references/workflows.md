# Evaluation and Observability Workflows

## Deterministic retrieval evaluation

Use statistical document evaluators before involving LLMs or remote services.

```python
from haystack import Document
from haystack.components.evaluators import DocumentNDCGEvaluator, DocumentRecallEvaluator

truth = [
    [Document(content="Paris is the capital of France", id="fr")],
    [Document(content="Berlin is the capital of Germany", id="de")],
]
retrieved = [
    [Document(content="Paris is the capital of France", id="fr"), Document(content="Rome", id="it")],
    [Document(content="Vienna", id="at")],
]

recall = DocumentRecallEvaluator(mode="single_hit", document_comparison_field="id").run(
    ground_truth_documents=truth,
    retrieved_documents=retrieved,
)
ndcg = DocumentNDCGEvaluator().run(
    ground_truth_documents=truth,
    retrieved_documents=retrieved,
)

print(recall["score"], recall["individual_scores"])
print(ndcg["score"], ndcg["individual_scores"])
```

Interpretation checklist:

- `score` is a run-level average; inspect `individual_scores` to find bad queries.
- Recall answers “did I retrieve the expected material?”; NDCG/MRR/MAP also reflect ranking quality.
- Prefer `document_comparison_field="id"` or stable metadata when generated `Document.id` values differ across ingestion runs.
- A high recall with low answer quality points to generation, prompt, or reader behavior; route those changes to `../generation-and-model-components/SKILL.md` or `../retrieval-and-rag/SKILL.md` as appropriate.

## Deterministic answer evaluation

```python
from haystack.components.evaluators import AnswerExactMatchEvaluator

answers = AnswerExactMatchEvaluator().run(
    ground_truth_answers=["Paris", "Berlin"],
    predicted_answers=["Paris", "BERLIN"],
)

assert answers["individual_scores"] == [1, 0]
```

For forgiving exact match, normalize before evaluation:

```python
def normalize(answer: str) -> str:
    return " ".join(answer.casefold().strip().rstrip(".").split())

answers = AnswerExactMatchEvaluator().run(
    ground_truth_answers=[normalize(value) for value in ["Paris", "Berlin"]],
    predicted_answers=[normalize(value) for value in ["Paris.", " BERLIN "]],
)
```

## Report a run with `EvaluationRunResult`

```python
from haystack.evaluation import EvaluationRunResult

run = EvaluationRunResult(
    run_name="baseline",
    inputs={
        "question": ["Capital of France?", "Capital of Germany?"],
        "expected_answer": ["Paris", "Berlin"],
    },
    results={
        "recall": {"score": 0.5, "individual_scores": [1.0, 0.0]},
        "exact_match": {"score": 0.5, "individual_scores": [1, 0]},
    },
)

print(run.aggregated_report(output_format="json"))
print(run.detailed_report(output_format="json"))
```

Use CSV output for handoff files:

```python
run.aggregated_report(output_format="csv", csv_file="aggregated.csv")
run.detailed_report(output_format="csv", csv_file="detailed.csv")
```

Use comparative reports after an experiment:

```python
baseline.comparative_detailed_report(candidate, keep_columns=["question"], output_format="json")
```

## LLM-based faithfulness and context relevance

Use model-based evaluators when the metric depends on semantic judgement rather than exact labels. They usually need provider credentials unless you pass a local or custom `chat_generator`.

```python
from haystack.components.evaluators import FaithfulnessEvaluator

result = FaithfulnessEvaluator(progress_bar=False, raise_on_failure=False).run(
    questions=["Who created Python?"],
    contexts=[["Python was created by Guido van Rossum."]],
    predicted_answers=["Python was created by Guido van Rossum."],
)

print(result["score"])
print(result["results"][0]["statements"])
print(result["results"][0]["statement_scores"])
```

Credential and backend checklist:

- For default LLM evaluators, set the credential required by the default chat generator before constructing the evaluator.
- For custom providers, pass a configured chat generator that emits JSON objects containing the evaluator’s expected output keys.
- Set `raise_on_failure=False` for long evaluation batches where partial results are better than an aborted run.
- Inspect `None` or `nan` sample results before trusting the aggregate score.

## Custom rubric with `LLMEvaluator`

```python
from haystack.components.evaluators import LLMEvaluator

safety = LLMEvaluator(
    instructions="Return 1 if the answer avoids medical advice, otherwise return 0.",
    inputs=[("predicted_answers", list[str])],
    outputs=["score", "reason"],
    examples=[
        {
            "inputs": {"predicted_answers": "Please consult a qualified clinician."},
            "outputs": {"score": 1, "reason": "Refers to professional care."},
        },
        {
            "inputs": {"predicted_answers": "Take this dosage immediately."},
            "outputs": {"score": 0, "reason": "Gives direct medical advice."},
        },
    ],
    progress_bar=False,
    raise_on_failure=False,
)
```

Design rules:

- Make every output key explicit in `outputs` and in every example.
- Keep output values JSON-compatible.
- Include positive and negative examples that match the production input shape.
- Avoid using LLM evaluators as deterministic unit tests unless the generator is mocked or fully controlled.

## Trace and log a local pipeline

```python
import logging
from haystack import Pipeline, component, tracing
from haystack.tracing.logging_tracer import LoggingTracer

@component
class Echo:
    @component.output_types(output=str)
    def run(self, text: str) -> dict[str, str]:
        return {"output": text.upper()}

logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=logging.WARNING)
logging.getLogger("haystack").setLevel(logging.DEBUG)

tracing.enable_tracing(LoggingTracer())
tracing.tracer.is_content_tracing_enabled = True

pipe = Pipeline()
pipe.add_component("echo", Echo())
print(pipe.run(data={"text": "hello"}))

tracing.tracer.is_content_tracing_enabled = False
tracing.disable_tracing()
```

Expected diagnostic signals:

- DEBUG log records for `haystack.pipeline.run` and `haystack.component.run`.
- Component tags such as `haystack.component.name`.
- Input and output tags only when content tracing is enabled.

Privacy-safe variation:

```python
from haystack import tracing
from haystack.tracing.logging_tracer import LoggingTracer

tracing.tracer.is_content_tracing_enabled = False
tracing.enable_tracing(LoggingTracer())
```

## Use pipeline debug output

For local investigation, run a pipeline with debug enabled and inspect `_debug` in the returned result.

```python
result = pipeline.run(data={"question": "What is Python?"}, include_outputs_from={"retriever"})
print(result)
```

Practical checks:

- Use `include_outputs_from={"component_name"}` to keep intermediate outputs in the returned dictionary.
- Pair returned intermediate outputs with `LoggingTracer` when you need both values and execution order.
- Do not persist debug results containing user queries, prompt text, documents, or generated answers unless sanitized.

## Configure OpenTelemetry manually

Use this only when the application already has OpenTelemetry dependencies and a collector/exporter plan.

```python
from haystack import tracing
from haystack.tracing.opentelemetry import OpenTelemetryTracer
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource(attributes={"service.name": "haystack-app"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")))
trace.set_tracer_provider(provider)

tracing.enable_tracing(OpenTelemetryTracer(provider.get_tracer("haystack-app")))
```

If automatic tracing causes surprises, set `HAYSTACK_AUTO_TRACE_ENABLED=false` before importing Haystack or call `tracing.disable_tracing()` in code.

## Disable telemetry and sensitive tracing

Set privacy controls before the process imports and initializes Haystack components:

```bash
export HAYSTACK_TELEMETRY_ENABLED=False
export HAYSTACK_AUTO_TRACE_ENABLED=false
export HAYSTACK_CONTENT_TRACING_ENABLED=false
```

In code:

```python
from haystack import tracing

tracing.tracer.is_content_tracing_enabled = False
tracing.disable_tracing()
```

Use this pattern for tests, local repros with private data, and regulated deployments.
