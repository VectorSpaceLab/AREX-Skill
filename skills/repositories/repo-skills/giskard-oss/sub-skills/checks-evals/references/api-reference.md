# checks-evals API reference

This reference covers the public `giskard.checks` operating surface for building
and running evaluations. Examples assume Python >=3.12 and an installed
`giskard-checks` package or the root `giskard` distribution that includes it.

## Imports

Use top-level public imports:

```python
from giskard.checks import (
    Scenario,
    Suite,
    Interact,
    Interaction,
    InteractionSpec,
    Trace,
    Check,
    CheckResult,
    CheckStatus,
    BaseLLMCheck,
    LLMCheckResult,
    Equals,
    NotEquals,
    LessThan,
    LessThanEquals,
    GreaterThan,
    GreaterEquals,
    StringMatching,
    RegexMatching,
    JsonValid,
    SemanticSimilarity,
    Readability,
    RegoPolicy,
    AllOf,
    AnyOf,
    Not,
    FnCheck,
    from_fn,
    Groundedness,
    Conformity,
    Contradiction,
    AnswerRelevance,
    Toxicity,
    LLMJudge,
    BaseLLMGenerator,
    LLMGenerator,
    UserSimulator,
    DatasetInputGenerator,
    set_default_generator,
    get_default_generator,
)
from giskard.checks.export.junit import to_junit_xml
```

Do not import from a `giskard_checks` namespace. Some deeper helpers, such as
`JSONPathStr`, `NoMatch`, `resolve`, and `provided_or_resolve`, live under
`giskard.checks.core.extraction`; keep those imports in project code only when
writing custom checks.

## Core concepts

| Concept | Purpose | Notes |
| --- | --- | --- |
| `Interaction` | Immutable record of one exchange. | Fields are `inputs`, `outputs`, and optional `metadata`. |
| `Trace` | Immutable ordered history of interactions. | `trace.last` is the most recent interaction or `None`; it is available in Python, Jinja templates, and JSONPath. |
| `Interact` | Runtime instruction for generating interactions. | Supports static values, callables, async callables, and input generators. If `outputs` is omitted, bind a target through `Scenario`, `Suite`, or `run(...)`. `metadata` defaults to an empty mapping. |
| `InteractionSpec` | Registered base for interaction-producing steps. | Import custom subclasses before scenario deserialization. |
| `Check` | Base class for assertions over a `Trace`. | Built-ins and custom checks return `CheckResult`. |
| `Scenario` | Ordered steps of interactions followed by checks. | Use `Scenario("name").interact(...).check(...)`; `run()` is async. |
| `Suite` | Collection of scenarios. | Useful for a shared target, parallel execution, reports, grouping, and JUnit export. |
| `TestCase` | Lower-level wrapper over a trace plus checks. | Usually unnecessary when the fluent `Scenario` API is enough. |

## Scenario and Suite signatures

| API | Signature highlights | Behavior |
| --- | --- | --- |
| `Scenario(name=None, *, steps=[], trace_type=None, annotations={}, target=MISSING, multiple_runs=1, tags=[])` | `name` may be positional. | Executes steps sequentially with a fresh trace for each run. Stops later steps after a failed or errored step. |
| `Scenario.interact(inputs, outputs=MISSING, metadata=None)` | `inputs` can be static, callable, async/generator, or an `InputGenerator`; `outputs` can be static/callable or omitted. | Adds an `Interact` to the current step. If checks already exist in that step, a new step is started. |
| `Scenario.check(check)` / `Scenario.checks(*checks)` | Accepts `Check` instances. | Consecutive checks in one step all run; a failed/errored step skips later steps. |
| `Scenario.with_target(target)` | Target callable receives inputs and may also receive trace depending on signature. | Used when `Interact.outputs` is omitted. |
| `Scenario.run(target=MISSING, return_exception=False, multiple_runs=None)` | Async. | `target` overrides the scenario target. `return_exception=True` turns runtime exceptions into error results instead of raising. |
| `Suite(name, scenarios=[], target=MISSING)` | `name` is required keyword-only. | Append scenarios and optionally bind a shared target. |
| `Suite.run(target=MISSING, return_exception=False, parallel=False, max_concurrency=None, verbose=True)` | Async. | `target` overrides suite and scenario targets. `parallel=True` preserves result order; set `verbose=False` in scripts/CI. |

Target precedence is: `run(target=...)` > `Suite(target=...)` >
`Scenario(target=...)`.

## Trace JSONPath rules

Giskard JSONPath selectors are evaluated against `{"trace": trace.model_dump()}`.

| Rule | Details |
| --- | --- |
| Prefix | Every JSONPath field must start with `trace.`. Invalid prefixes are rejected at model construction for fields typed as `JSONPathStr`. |
| Current turn | Prefer `trace.last.inputs`, `trace.last.outputs`, and `trace.last.metadata.<name>` for current-turn values. |
| Older turns | Use indexed paths such as `trace.interactions[0].outputs` only when the scenario needs a specific historical turn. |
| Missing values | A non-matching scalar path resolves to `NoMatch`; most checks return `CheckStatus.ERROR` with details instead of silently failing. |
| Collections | Wildcards, descendants (`..`), slices, unions, and multi-field selectors resolve to lists. Use comparison `match="any"`, `"all"`, or `"none"` when comparing collections. |
| Defaults | Common defaults are `trace.last.outputs` for answer/output text and `trace.last.metadata.context` for groundedness/contradiction context. |

## Result statuses

| Status | Meaning | Common source |
| --- | --- | --- |
| `pass` | The assertion or aggregate succeeded. | Matching text, equal values, valid JSON, a passing judge verdict. |
| `fail` | The assertion ran and did not hold. | Wrong value, regex not found, invalid JSON text, low score/similarity, or a failing judge verdict. |
| `error` | The check could not evaluate its assertion. | Missing JSONPath, wrong extracted type, unsupported comparison, schema `$ref` issue, target exception captured with `return_exception=True`, provider/generator error. |
| `skip` | The item was deliberately skipped. | Later scenario steps after an earlier fail/error; custom checks may also return `CheckResult.skip(...)`. |

`ScenarioResult` and `SuiteResult` expose convenience properties such as
`passed`, `failed`, `errored`, `skipped`, `passed_count`, `failed_count`,
`errored_count`, `skipped_count`, `pass_rate`, and `failures_and_errors`.

## Deterministic and local built-in checks

| Check | Required / important fields | Defaults and behavior |
| --- | --- | --- |
| `Equals` | `key`, exactly one of `expected_value` or `expected_value_key`; optional `match`. | Normalizes Unicode by default (`normalization_form="NFKC"`). Supports `match="any"`, `"all"`, `"none"` for collection-valued actuals. |
| `NotEquals` | Same field pattern as `Equals`. | Passes when actual and expected are not equal. |
| `LessThan`, `LessThanEquals`, `GreaterThan`, `GreaterEquals` | Same field pattern as `Equals`. | Use Python comparison semantics after normalization. Deprecated aliases `LesserThan` and `LesserThanEquals` may appear in older serialized data. |
| `StringMatching` | Exactly one of `keyword` or `keyword_key`; optional `text` or `text_key`. | `text_key="trace.last.outputs"`, `normalization_form="NFKC"`, `case_sensitive=True`; whitespace is normalized. |
| `RegexMatching` | Exactly one of `pattern` or `pattern_key`; optional `text` or `text_key`. | `text_key="trace.last.outputs"`, `match_timeout_seconds=2.0`; uses the `regex` package. |
| `JsonValid` | Optional `key`, `parse`, and `schema`. | `key="trace.last.outputs"`, `parse=True`. With `parse=True`, extracted value must be a JSON string. With `parse=False`, value must already be JSON-serializable. `schema=` is an alias for the internal schema field. |
| `AllOf` | `checks=[...]`. | Short-circuits on the first non-passing inner check. |
| `AnyOf` | `checks=[...]`. | Short-circuits on the first passing or errored inner check; returns skip if every inner check skipped. |
| `Not` | `check=...`. | Inverts pass/fail only; errors and skips pass through unchanged. |
| `from_fn` / `FnCheck` | Callable receives `trace` and returns `bool` or `CheckResult`, sync or async. | Good for one-off deterministic checks. `fn` is excluded from serialization, so use a registered custom `Check` for portable serialized scenarios. |
| `RegoPolicy` | `policy`, `rule`, optional `key`, `data`. | Requires optional `giskard-checks[regorus]`; the PyPI wheel is `celine-regorus`, imported as `regorus`. |
| `Readability` | Optional `key`, `metric`, `min_score`, `max_score`. | Requires optional `giskard-checks[readability]` (`textstat`); constructs metrics in the check result. |

## LLM judges and LLM-dependent checks

All judge checks inherit a `generator` field. If omitted, they use
`get_default_generator()`, which returns a runtime override from
`set_default_generator(...)` or constructs a provider-backed
`giskard.agents.Generator` from `GISKARD_CHECKS_DEFAULT_MODEL`. The default model
is `openai/gpt-4o-mini`. Provider package extras, API keys, aliases, and retry
behavior are covered in the LLM provider sub-skill.

| Check | Main fields | Default extraction |
| --- | --- | --- |
| `Groundedness` | `answer` or `answer_key`; `context` or `context_key`; optional `generator`. | `answer_key="trace.last.outputs"`, `context_key="trace.last.metadata.context"`. Missing answer/context returns `error` before a judge call. |
| `Contradiction` | Same answer/context pattern as `Groundedness`. | Fails only on clear contradiction with context; omissions/unsupported additions are more permissive than groundedness. |
| `AnswerRelevance` | `question` or `question_key`; `answer` or `answer_key`; optional direct `context`; `include_history=True`. | `question_key="trace.last.inputs"`, `answer_key="trace.last.outputs"`; missing question/answer returns `error` before a judge call. |
| `Conformity` | Required `rule`; optional `generator`. | Supplies the full trace and literal rule to the bundled prompt. |
| `Toxicity` | `output` or `output_key`; optional `categories`; optional `generator`. | `output_key="trace.last.outputs"`; default categories cover common safety toxicity types. |
| `LLMJudge` | Exactly one of `prompt` or `prompt_path`; optional `generator`. | Inline prompts are Jinja-rendered with `trace`; output must parse as `LLMCheckResult` with non-empty `reason` and boolean `passed`. |
| `SemanticSimilarity` | `reference_text` or `reference_text_key`, `actual_answer_key`, `threshold`, optional `embedding_model`. | Uses `GISKARD_CHECKS_DEFAULT_EMBEDDING_MODEL` or default `text-embedding-3-small` when no explicit embedding model is supplied. |

## Input generators

Input generators are used as `Scenario.interact(inputs=<generator>, outputs=...)`.
They produce user-side inputs and can use the evolving trace.

| Generator | Fields | Behavior |
| --- | --- | --- |
| `LLMGenerator` | Exactly one of `prompt` or `prompt_path`; `as_template=False`; `max_steps=3`; `max_retries=2`; optional `generator`. | Produces up to `max_steps` inputs from an LLM. For structured target input types, the LLM output is parsed into that type. |
| `UserSimulator` | Required non-empty `persona`; optional `context`; `max_steps=3`; `max_retries=2`; optional `generator`. | Uses a bundled prompt to simulate a user persona over multiple turns. |
| `DatasetInputGenerator` | Required non-empty `prompt`; optional `generator`. | For string targets, yields the prompt verbatim with no LLM call. For structured input types, uses the LLM only to build a schema template with a `{{prompt}}` placeholder, then injects the real prompt locally. |

## Serialization and export

- `model_dump()` and `model_dump_json()` include a computed `kind` field for
  registered discriminated types.
- `model_validate(...)` and `model_validate_json(...)` require every custom
  `Check`, `InteractionSpec`, `InputGenerator`, or generator class to be
  imported first so its `kind` is registered.
- Pydantic `MISSING` fields are omitted from JSON and restored as `MISSING` on
  round-trip; this is how omitted `outputs`, `expected_value`, and optional
  judge inputs remain distinguishable from explicit `None`.
- `FnCheck.fn` is excluded from serialization; prefer `@Check.register(...)` for
  reusable serialized checks.
- Export suite results with either `suite_result.to_junit_xml(path=None)` or
  `to_junit_xml(suite_result, path=None)`. Passing a path writes the XML file
  and always returns the XML string.
