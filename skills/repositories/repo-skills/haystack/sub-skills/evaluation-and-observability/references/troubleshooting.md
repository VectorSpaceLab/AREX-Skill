# Evaluation and Observability Troubleshooting

## Install and import failures

### `ModuleNotFoundError: No module named 'haystack'`

Checks:

```python
import haystack
print(haystack.__version__)
```

Fixes:

- Install the public distribution package `haystack-ai` in the active Python environment.
- In the Haystack repository checkout, use the repository’s Hatch-managed commands instead of calling bare `python` or `pip` directly.
- Ensure the package version supports the APIs used by this skill; this skill targets Haystack 2.31-style APIs.

### Evaluator import fails

Use public component imports first:

```python
from haystack.components.evaluators import DocumentNDCGEvaluator, AnswerExactMatchEvaluator
from haystack.evaluation import EvaluationRunResult
```

If a specific evaluator is unavailable, check the installed Haystack version and optional integration packages. Ragas, DeepEval, tracing connectors, and provider-specific generators may live in separate integrations.

## Optional dependency failures

### `EvaluationRunResult(...).aggregated_report(output_format="df")` fails

Cause: dataframe output requires `pandas`.

Fixes:

- Use `output_format="json"` for dependency-free reports.
- Use `output_format="csv", csv_file="..."` for portable file output.
- Install `pandas` only if dataframe output is required.

### `SASEvaluator` fails during import, warm-up, or execution

Likely causes:

- Missing model/runtime dependencies.
- Model download blocked in the environment.
- CPU/GPU/backend mismatch.

Fixes:

- Prefer `AnswerExactMatchEvaluator` for deterministic smoke tests.
- Run a one-sample warm-up before a large evaluation job.
- Pin/cache model dependencies in production rather than downloading during CI.

## Credential and backend failures

### LLM evaluator raises provider authentication errors

Symptoms: missing API key, unauthorized request, provider-specific HTTP errors, or JSON parsing failures.

Fixes:

- Set the credential expected by the configured chat generator before constructing the evaluator.
- For default LLM evaluators, provide the default provider credential or pass a custom `chat_generator`.
- Configure the generator for JSON output. For OpenAI chat generators, include generation kwargs such as `{"response_format": {"type": "json_object"}}` when building custom generator objects.
- Use `raise_on_failure=False` for batch jobs so individual failures become `None` results and warnings.

### OpenTelemetry or Datadog tracing does not appear

Checks:

```python
from haystack import tracing
print(tracing.is_tracing_enabled())
```

Fixes:

- Install the backend SDK/exporter packages required by the chosen tracing backend.
- Configure OpenTelemetry or Datadog before importing/running Haystack if relying on auto-detection.
- Set `HAYSTACK_AUTO_TRACE_ENABLED=true` or call `tracing.enable_tracing(...)` explicitly.
- For local debugging, replace the backend temporarily with `LoggingTracer()` to prove that Haystack spans are emitted.

### Unexpected network tracing backend is enabled

Fixes:

```bash
export HAYSTACK_AUTO_TRACE_ENABLED=false
```

or:

```python
from haystack import tracing
tracing.disable_tracing()
```

Use this in tests and privacy-sensitive deployments.

## API misuse

### `ValueError: The length of ... must be the same`

Cause: evaluator input lists are not aligned by sample.

Fix:

```python
assert len(ground_truth_documents) == len(retrieved_documents)
assert len(ground_truth_answers) == len(predicted_answers)
```

For document evaluators, the outer list is the query/sample dimension and the inner list contains the documents for that sample.

### `DocumentNDCGEvaluator` returns lower scores than expected

Likely causes:

- Ground-truth and retrieved `Document` IDs do not match.
- Ground-truth documents mix scored and unscored values in the same sample.
- Retrieved list order differs from expected ranking.

Fixes:

- Provide stable `id` values for both ground-truth and retrieved documents or reuse the same `Document` objects when constructing toy tests.
- If using graded relevance, set `score` on every ground-truth document in the sample.
- Inspect `individual_scores` to identify which query has the ranking issue.

### `DocumentRecallEvaluator` misses expected documents

Likely causes:

- Comparing on `content` while generated content has whitespace/chunking differences.
- Comparing on `id` while IDs are regenerated between indexing and evaluation.
- Missing nested metadata key when using `document_comparison_field="meta.<key>"`.

Fixes:

- Use stable metadata such as `document_comparison_field="meta.source_id"` when content and IDs are unstable.
- Normalize source IDs during ingestion.
- Check for warnings about empty or invalid comparison values in multi-hit mode.

### `LLMEvaluator` rejects init parameters

Checks:

- `inputs` must be a list of two-item tuples: `(input_name, list[type])`.
- `outputs` must be a list of strings.
- Every example must be exactly `{"inputs": {...}, "outputs": {...}}` with string keys.
- Runtime input values must be lists and all input lists must have equal length.

## Data and configuration issues

### Exact match score is too strict

Cause: `AnswerExactMatchEvaluator` compares exact strings.

Fixes:

- Normalize case, whitespace, punctuation, and aliases before evaluation.
- Use semantic evaluators when acceptable answers vary naturally.
- Record the normalization function next to the evaluation report so scores are reproducible.

### Aggregated score hides failures

Fixes:

- Always inspect `individual_scores` or `detailed_report(output_format="json")`.
- Sort or filter the detailed report to find samples with score `0`, low NDCG, `None`, or `nan`.
- Keep input columns such as question, expected answer, expected document IDs, and pipeline variant in `EvaluationRunResult.inputs`.

### Comparative reports produce confusing columns

Fixes:

- Use distinct `run_name` values.
- Pass `keep_columns=["question", "expected_answer"]` or another stable set of shared input columns.
- Ensure both runs used the same input sample order.

## Observability workflow issues

### `LoggingTracer` shows operation names but not inputs/outputs

Cause: content tracing is disabled by default.

Fix for local sanitized debugging:

```python
from haystack import tracing
tracing.tracer.is_content_tracing_enabled = True
```

Revert afterward:

```python
tracing.tracer.is_content_tracing_enabled = False
```

Do not enable content tracing in production unless query, document, prompt, and answer payloads are safe to export.

### No debug logs appear with `LoggingTracer`

Fixes:

```python
import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("haystack").setLevel(logging.DEBUG)
```

Then enable tracing:

```python
from haystack import tracing
from haystack.tracing.logging_tracer import LoggingTracer
tracing.enable_tracing(LoggingTracer())
```

### Structured logging is not JSON

Fixes:

```python
import haystack.logging
haystack.logging.configure_logging(use_json=True)
```

or set:

```bash
export HAYSTACK_LOGGING_USE_JSON=true
```

If structlog behavior is unwanted despite installed dependencies, set the environment variable used by Haystack to ignore structlog before startup.

### Telemetry must be disabled

Set before running the app:

```bash
export HAYSTACK_TELEMETRY_ENABLED=False
```

For shell startup files, add the same export line and restart the shell. For Windows, set a user-level `HAYSTACK_TELEMETRY_ENABLED` environment variable to `False`.

### Pipeline debug output contains sensitive content

Fixes:

- Limit `include_outputs_from` to the component being investigated.
- Redact or hash queries, documents, prompts, and generated answers before saving results.
- Prefer aggregate evaluator scores for shared reports, and keep raw debug outputs local.
