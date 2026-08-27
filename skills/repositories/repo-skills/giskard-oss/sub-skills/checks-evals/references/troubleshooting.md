# checks-evals troubleshooting

Use this guide when a scenario, check, suite, serialization round-trip, or JUnit
export behaves unexpectedly.

## Status semantics

| Status | How to read it | Typical fix |
| --- | --- | --- |
| `pass` | The check or aggregate succeeded. | No action unless the assertion is too weak. |
| `fail` | The assertion ran and found a real mismatch. | Inspect `message` and `details`; adjust the target behavior, expected value, threshold, regex, or rule. |
| `error` | The assertion could not be evaluated. | Fix missing JSONPath, wrong value type, unsupported comparison, provider/generator errors, or exceptions in target/check code. |
| `skip` | Execution was skipped deliberately. | In scenarios, later steps skip after an earlier fail/error. Custom checks may also return skip for unmet preconditions. |

Aggregation priority is error > fail > skip-all > pass. A step with one skipped
check and one passing check is passing; a step where all checks skip is skipped.

## NoMatch or missing JSONPath

Symptoms:

- Check result has `status == "error"` and a message like `No value found for key`.
- `details` contains `NoMatch(key=...)`.
- `Groundedness`, `Contradiction`, or `AnswerRelevance` returns error without
  invoking the judge.

Fixes:

1. Confirm the output shape in `result.final_trace.last`.
2. Use `trace.last.outputs` for scalar string outputs.
3. For structured outputs, use the field path, for example
   `trace.last.outputs.answer` or `trace.last.metadata.context`.
4. Avoid wildcard paths unless the check expects a list. Wildcards,
   descendants, slices, unions, and multi-field selectors resolve to lists.
5. For collection comparisons, use `match="any"`, `match="all"`, or
   `match="none"`.

## Wrong key field typing in a custom check

Symptoms:

- A custom `key` or `*_key` accepts invalid paths such as `last.outputs`.
- Serialization/deserialization behaves inconsistently.
- Package-style tests complain that JSONPath fields do not use `JSONPathStr`.

Fix:

```python
from giskard.checks.core.extraction import JSONPathStr
from pydantic.experimental.missing_sentinel import MISSING

key: JSONPathStr = "trace.last.outputs"
expected_value_key: JSONPathStr | MISSING = MISSING
```

Every field named exactly `key` or ending with `_key` on a `Check` subclass must
use `JSONPathStr`, optionally unioned with `None` or `MISSING`. Do not type these
fields as plain `str`.

## Missing provider or default generator for LLM judges and generators

Symptoms:

- Running `Groundedness`, `Conformity`, `Contradiction`, `AnswerRelevance`,
  `Toxicity`, `LLMJudge`, `LLMGenerator`, structured `DatasetInputGenerator`, or
  `SemanticSimilarity` tries to call a provider and fails.
- Errors mention unavailable provider SDKs, missing API keys, unsupported
  embeddings, authentication, rate limits, or provider bad requests.

Fixes:

1. For no-key environments, use deterministic checks (`Equals`, `StringMatching`,
   `RegexMatching`, `JsonValid`, comparisons) or mocked generators in tests.
2. For live LLM judging, configure a generator explicitly:

   ```python
   from giskard.agents import Generator
   from giskard.checks import Groundedness

   check = Groundedness(generator=Generator(model="openai/gpt-4o-mini"))
   ```

3. Or set a process-wide default:

   ```python
   from giskard.agents import Generator
   from giskard.checks import set_default_generator

   set_default_generator(Generator(model="openai/gpt-4o-mini"))
   ```

4. Ensure the provider package extra and provider environment variables are
   configured for the chosen model. Provider routing details belong in the
   `llm-providers` sub-skill.
5. For `SemanticSimilarity`, configure a working embedding model or avoid that
   check in no-provider runs.
6. For `LLMGenerator` and `UserSimulator`, confirm the default generator can
   produce structured outputs for the requested target type.

## Optional `regorus` dependency for `RegoPolicy`

Symptoms:

- Constructing `RegoPolicy(...)` raises a validation error mentioning
  `giskard-checks[regorus]`.
- Importing `giskard.checks` works, but Rego policy evaluation does not.

Fix:

- Install the optional extra only when Rego policy checks are required:
  `pip install "giskard-checks[regorus]"`.
- The wheel is distributed as `celine-regorus`, but the runtime import name is
  `regorus`.
- Other built-in checks do not require this optional dependency.

## Optional `readability` dependency for `Readability`

Symptoms:

- Constructing or running `Readability(...)` raises a validation error about
  `textstat` or the `readability` extra.
- The check imports successfully but fails when it tries to compute the score.

Fix:

- Install the optional extra only when readability checks are required:
  `pip install "giskard-checks[readability]"`.
- Ensure the chosen `key` resolves to a string.
- Use `min_score`/`max_score` that match the chosen metric's scale.

## Serialization registration failures

Symptoms:

- `Check.model_validate(...)` raises `Kind is not provided`.
- Validation says `Kind <name> is not registered`.
- Registration raises a duplicate-kind error.
- A `FnCheck` round-trip loses its callable.

Fixes:

1. Ensure serialized payloads include `kind` by using `model_dump()` from a
   registered class.
2. Import the module defining each custom registered class before validation.
3. Use one unique snake_case kind per base class.
4. Prefer a registered `Check` subclass for portable scenarios; do not rely on
   `FnCheck` serialization because its `fn` field is excluded.
5. If custom generators or interaction specs are serialized in a scenario,
   import their defining modules before `Scenario.model_validate(...)` too.

## JsonValid surprises

| Symptom | Cause | Fix |
| --- | --- | --- |
| Dict/list output errors with `parse=True`. | `parse=True` expects a serialized JSON string. | Use `JsonValid(parse=False)` for already-parsed JSON values. |
| Plain string such as `value` fails with `parse=True`. | It is not valid JSON text because JSON strings require quotes. | Return `"\"value\""` as JSON text or use `parse=False`. |
| Schema validation fails. | Parsed value does not conform to `schema=...`. | Inspect `result.details["parsed_value"]` and adjust either output or schema. |
| Schema `$ref` errors. | Reference cannot be resolved locally. | Use a self-contained schema without unreachable external references. |

## Suite and JUnit result diagnostics

- Call `suite_result.failures_and_errors` to locate failing/errored scenarios.
- Call `result.print_report()` for a Rich text report in interactive sessions.
- Set `GISKARD_CHECKS_MAX_REPORTED_FAILURES` to limit the number of failures
  printed in large suite reports.
- Use `suite_result.to_junit_xml(path)` or `to_junit_xml(suite_result, path)` for
  CI systems. Failed scenarios become `<failure>`, errored scenarios become
  `<error>`, and skipped scenarios become `<skipped>`.

## Scenario execution and target binding

Symptoms:

- `Interaction outputs are not provided and no target was bound.`
- Suite target appears to override scenario behavior.
- Later steps did not run.

Fixes:

1. If `interact(inputs)` omits `outputs`, bind a target at `Scenario`, `Suite`,
   or `run(...)` level.
2. Remember target precedence: `run(target=...)` > `Suite(target=...)` >
   `Scenario(target=...)`.
3. Later steps skip after an earlier step fails or errors; inspect the first
   non-passing step rather than only the final skipped step.
4. If target exceptions should be captured, run with `return_exception=True`.
5. For `Trace` / `Interaction` debugging, print or inspect `result.final_trace`
   and `trace.last` rather than relying on the rendered report alone.
