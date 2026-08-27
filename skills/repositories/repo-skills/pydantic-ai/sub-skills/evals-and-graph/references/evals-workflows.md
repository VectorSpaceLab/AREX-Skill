# Evals Workflows

Use `pydantic_evals` to measure task quality over named cases and aggregate results across runs. It complements unit tests: unit tests protect deterministic contracts, while evals compare behavior across realistic examples, probabilistic outputs, regressions, and model/application changes.

## Core Objects

- `Case(inputs=..., expected_output=..., metadata=..., evaluators=...)` describes one scenario. `inputs` is passed to the task function; `expected_output` and `metadata` are optional but should be present when evaluators need ground truth or case-specific knobs.
- `Dataset(name=..., cases=[...], evaluators=[...], report_evaluators=[...])` groups cases and shared evaluators. Parameterize it as `Dataset[InputsT, OutputT, MetadataT]` when serializing, loading, or relying on type checking.
- `Evaluator.evaluate(ctx)` runs per case after the task returns. `ctx` exposes `name`, `inputs`, `metadata`, `expected_output`, `output`, `duration`, `metrics`, `attributes`, and `span_tree`.
- `ReportEvaluator.evaluate(ctx)` runs once after all cases and can add analyses such as confusion matrices or precision/recall curves to the report.
- `EvaluationReport` contains successful `cases`, `failures`, `averages()`, optional `case_groups()` for repeated cases, and display/serialization helpers.

## Minimal Deterministic Dataset

```python
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected, IsInstance


def normalize(text: str) -> str:
    return ' '.join(text.casefold().split())


dataset = Dataset[str, str, Any](
    name='normalization',
    cases=[
        Case(name='spacing', inputs='  Hello   WORLD ', expected_output='hello world'),
        Case(name='unicode', inputs='CAFÉ', expected_output='café'),
    ],
    evaluators=[IsInstance(type_name='str'), EqualsExpected()],
)

report = dataset.evaluate_sync(normalize, progress=False, max_concurrency=1)
averages = report.averages()
assert averages is not None
assert averages.assertions == 1.0
```

Start with deterministic evaluators (`EqualsExpected`, `Contains`, `IsInstance`, `MaxDuration`, or custom Python evaluators) before adding LLM judges. This makes regressions cheaper to localize and avoids confusing model variance with application bugs.

## Custom Evaluators

Subclass `Evaluator` and implement `evaluate()` as sync or async. Return one of:

- `bool`, finite `float`, `int`, or `str`
- `EvaluationReason(value=..., reason=...)`
- `dict[str, scalar | EvaluationReason]` when one evaluator emits multiple named results

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class MentionsRequiredTerms(Evaluator[str, str, dict[str, list[str]]]):
    def evaluate(self, ctx: EvaluatorContext[str, str, dict[str, list[str]]]) -> dict[str, EvaluationReason]:
        required = (ctx.metadata or {}).get('required_terms', [])
        output = ctx.output.casefold()
        return {
            f'mentions_{term}': EvaluationReason(
                value=term.casefold() in output,
                reason=None if term.casefold() in output else f'missing {term!r}',
            )
            for term in required
        }

    def get_evaluator_version(self) -> str | None:
        return 'v1'
```

Override `get_default_evaluation_name()` for a custom single-result name. Override `get_evaluator_version()` when scores from old evaluator logic should remain distinguishable in reports or online sinks.

## Report Evaluators

Use report evaluators for experiment-level analysis that needs all cases together:

- `ConfusionMatrixEvaluator(predicted_from=..., expected_from=...)` for classification labels.
- `PrecisionRecallEvaluator(score_from=..., score_key=..., positive_from=..., positive_key=...)` for threshold curves from scores plus boolean truth.
- `ROCAUCEvaluator` and `KolmogorovSmirnovEvaluator` for score-distribution analysis.
- Custom `ReportEvaluator` subclasses for domain-specific tables or scalar summaries.

Case-level evaluator results are grouped by type: numeric scores in `case.scores`, strings in `case.labels`, and booleans in `case.assertions`. Report evaluators that read `scores`, `labels`, or `assertions` need stable result names.

## Running Experiments

`Dataset.evaluate()` is async; `Dataset.evaluate_sync()` wraps it for synchronous callers. Important keyword arguments:

- `name`: experiment name shown in reports and traces.
- `task_name`: override the task function name.
- `metadata`: experiment-level metadata.
- `max_concurrency`: `None` runs all cases concurrently; `1` is best for debugging and deterministic local checks; bounded values protect rate limits and resource pools.
- `progress`: set `False` in tests and smoke scripts to avoid noisy terminal output.
- `retry_task` and `retry_evaluators`: Tenacity-style retry configs for transient failures.
- `repeat`: run each case multiple times; inspect `report.case_groups()` for per-case aggregates.
- `lifecycle`: a `CaseLifecycle` subclass for per-case setup, context enrichment, and teardown.

Prefer keyword arguments for everything after `task`; positional `name`, `max_concurrency`, `progress`, `retry_task`, and `retry_evaluators` are deprecated.

## Retries and Flakiness

Use retries for transient errors, not for deterministic assertion failures:

```python
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

report = dataset.evaluate_sync(
    task=my_task,
    progress=False,
    max_concurrency=3,
    retry_task={
        'stop': stop_after_attempt(3),
        'wait': wait_exponential(multiplier=0.2, max=2),
        'retry': retry_if_exception_type(TimeoutError),
        'reraise': True,
    },
    retry_evaluators={'stop': stop_after_attempt(2)},
)
```

For LLM-as-judge workflows, keep `max_concurrency` low, pin or route the judge model intentionally, store the judge rubric near the dataset, and use `repeat` when variability matters. Route model-string and optional provider setup to `../models-and-providers/SKILL.md`.

## Lifecycle, Metrics, and Attributes

Use `CaseLifecycle` when each case needs setup/teardown or enriched evaluator context. Use `set_eval_attribute()` and `increment_eval_metric()` inside the task to make application data visible to evaluators and reports.

```python
from pydantic_evals import CaseLifecycle
from pydantic_evals.evaluators import EvaluatorContext


class AddOutputLength(CaseLifecycle[str, str, dict]):
    async def prepare_context(self, ctx: EvaluatorContext[str, str, dict]) -> EvaluatorContext[str, str, dict]:
        ctx.metrics['output_length'] = len(ctx.output)
        return ctx


report = dataset.evaluate_sync(my_task, lifecycle=AddOutputLength, progress=False)
```

Use `ctx.span_tree` only when OpenTelemetry tracing is available. Accessing it can raise a span-recording error if tracing dependencies or providers are incompatible.

## Dataset Serialization

Use YAML for human-edited datasets and JSON for programmatic exchange. `Dataset.to_file()` writes the dataset plus a JSON schema by default, enabling editor validation.

```python
dataset.to_file('quality_cases.yaml')
loaded = Dataset[str, str, dict].from_file(
    'quality_cases.yaml',
    custom_evaluator_types=[MentionsRequiredTerms],
)
```

When using custom evaluator or report evaluator classes in serialized datasets, pass `custom_evaluator_types` and `custom_report_evaluator_types` to both `to_file()` and `from_file()` so schemas and deserialization understand them. Use `schema_path=None` only when the extra schema file is unwanted.

## Evaluating Agents

Wrap an agent call as the task and keep agent setup in `../agent-core/SKILL.md`:

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance

agent = Agent(TestModel(custom_output_text='Paris'), instructions='Answer briefly.')

def answer(question: str) -> str:
    return agent.run_sync(question).output

agent_dataset = Dataset[str, str, dict](
    name='agent_capitals',
    cases=[Case(name='france', inputs='Capital of France?', expected_output='Paris')],
    evaluators=[IsInstance(type_name='str')],
)

report = agent_dataset.evaluate_sync(answer, progress=False, max_concurrency=1)
```

For real provider evals, separate three concerns: agent behavior in `agent-core`, judge/model selection in `models-and-providers`, and eval dataset/report design here.

## Logfire Integration

`pydantic-evals` can emit OpenTelemetry spans and Logfire-compatible eval summaries. Keep Logfire optional:

```python
try:
    import logfire
except ImportError:
    logfire = None

if logfire is not None:
    logfire.configure(send_to_logfire='if-token-present')
    logfire.instrument_pydantic_ai()
```

Configure tracing before running evals and before code you want instrumented. `send_to_logfire='if-token-present'` is safe for shared scripts because it avoids requiring credentials. For local no-network smoke checks, skip Logfire entirely.
