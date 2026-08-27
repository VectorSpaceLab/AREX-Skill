# GenAI Evaluation

## Evaluation Entry Points

- `mlflow.genai.evaluate(data=..., scorers=[...], predict_fn=..., model_id=...)` evaluates GenAI apps from existing traces, tabular/list data, or on-the-fly predictions.
- Trace-backed evaluation expects a `trace` column or traces returned by `mlflow.search_traces`; scorers can inspect `inputs`, `outputs`, `expectations`, `trace`, or `session` depending on their signature.
- Dataset-backed evaluation commonly uses records with `inputs`, `outputs`, and `expectations`; when `predict_fn` is provided, `inputs` are passed as keyword arguments and outputs/traces are generated during evaluation.
- Multi-turn evaluation can use conversation/session traces or a `ConversationSimulator`; session-level scorers should accept `session` and only compatible expectations.

## Custom Scorers

Use `@mlflow.genai.scorers.scorer` for deterministic checks before adding LLM judges:

```python
from mlflow.genai.scorers import scorer

@scorer(name="mentions_policy", aggregations=["mean"])
def mentions_policy(outputs, expectations=None):
    expected = (expectations or {}).get("keyword", "policy")
    return expected.lower() in str(outputs).lower()
```

- Scorer functions may return bool, int, float, str, feedback objects, or lists of feedback objects.
- Use `pass_if=` for numeric scorers whose pass condition is not a boolean or yes/no value.
- Use trace-aware scorers for tool calls, retrieval spans, latency, token metadata, or prompt linkage.
- Keep scorer names stable because they become evaluation result columns and assessment names.

## Judges And Built-In Scorers

- `mlflow.genai.make_judge(...)` creates LLM-backed judges using instructions with template variables such as `{{ inputs }}`, `{{ outputs }}`, `{{ expectations }}`, `{{ trace }}`, or `{{ conversation }}`.
- LLM judges require provider access; specify model URIs, structured feedback value types, inference parameters, base URLs, or headers only when supported by the selected backend.
- Built-in scorers and third-party scorer integrations may require optional packages or Databricks-managed services. If a scorer fails to import, degrade to a custom deterministic scorer for local validation.
- Databricks scorer registration/scheduling has stricter backend and model-provider requirements than local `evaluate` execution.

## Review Queues And Labeling

- `mlflow.genai.create_labeling_session`, `get_labeling_session(s)`, `delete_labeling_session`, `get_review_app`, and related `Agent`, `LabelingSession`, and `ReviewApp` entities support human review workflows.
- Review app and labeling features commonly require a Databricks workspace and may not work against local SQLite or legacy file tracking stores.
- Keep review queue setup separate from local tracing/evaluation tests; local tests should validate trace creation, search, custom scorers, and prompt/dataset linkage.

## Practical Evaluation Flow

1. Create or search representative traces for the app path under test.
2. Attach expectations or build a dataset with `inputs`/`expectations`.
3. Start with deterministic custom scorers for schema, retrieval, refusal, latency, and exact-match assertions.
4. Add LLM judges only after provider credentials/network access are confirmed.
5. Inspect per-row assessments and aggregate metrics; do not rely only on top-level pass/fail.
6. Preserve prompt version/alias, dataset id, model id, trace tags, and scorer versions in tags or metadata so results are reproducible.
