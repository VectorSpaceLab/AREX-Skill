# Custom checks and registration

Use custom checks when built-ins or `from_fn` are not enough. Keep one-off logic
as `from_fn`; make a registered `Check` subclass when the check must be reused,
serialized, shared across suites, or deserialized later.

## Choose the right extension point

| Need | Use | Serialization stance |
| --- | --- | --- |
| Short local predicate over a trace | `from_fn(...)` / `FnCheck` | Not portable: the callable field is excluded from dumps. |
| Reusable deterministic assertion | `@Check.register("kind")` subclass of `Check` | Portable after the module defining the class is imported. |
| Reusable LLM-scored assertion | Subclass `BaseLLMCheck` and register it | Portable after imports; requires generator setup when run. |
| Custom interaction generation | `@InteractionSpec.register("kind")` or `@InputGenerator.register("kind")` | Import before deserializing scenarios that contain it. |

## Minimal deterministic custom check

```python
from typing import Any

from giskard.checks import Check, CheckResult, Trace
from giskard.checks.core.extraction import JSONPathStr, NoMatch, resolve
from pydantic import Field


@Check.register("contains_required_fields")
class ContainsRequiredFields(Check[Any, Any, Trace[Any, Any]]):
    """Pass when a dict at `key` contains every configured field."""

    key: JSONPathStr = Field(default="trace.last.outputs")
    required: list[str] = Field(default_factory=list)

    async def run(self, trace: Trace[Any, Any]) -> CheckResult:
        value = resolve(trace, self.key)
        if isinstance(value, NoMatch):
            return CheckResult.error(
                message=f"No value found for key {self.key!r}.",
                details={"key": self.key, "value": value},
            )
        if not isinstance(value, dict):
            return CheckResult.error(
                message=f"Value at {self.key!r} must be a dict, got {type(value).__name__}.",
                details={"key": self.key, "value": value},
            )

        missing = [field for field in self.required if field not in value]
        if missing:
            return CheckResult.failure(
                message=f"Missing required fields: {missing}",
                details={"missing": missing, "value": value},
            )
        return CheckResult.success(
            message="All required fields are present.",
            details={"required": self.required},
        )
```

Usage:

```python
from giskard.checks import Scenario

scenario = (
    Scenario("schema_shape")
    .interact("question", {"answer": "Paris", "confidence": 0.9})
    .check(ContainsRequiredFields(required=["answer", "confidence"]))
)
```

## JSONPath field typing rules

Every `Check` field named `key` or ending in `_key` must be typed as one of:

```python
from giskard.checks.core.extraction import JSONPathStr
from pydantic.experimental.missing_sentinel import MISSING

key: JSONPathStr
optional_key: JSONPathStr | None = None
fallback_key: JSONPathStr | MISSING = MISSING
```

Why this matters:

- `JSONPathStr` validates syntax at model construction.
- Paths must start with `trace.`.
- Wrongly typing a field as plain `str` removes validation and breaks the
  package's JSONPath-field contract.
- Use `MISSING`, not `None`, when omitted means “fall back to another input”.
  Keep `None` for cases where explicit `None` is a real value to check.

Use the extraction helpers consistently:

```python
from pydantic.experimental.missing_sentinel import MISSING
from giskard.checks.core.extraction import JSONPathStr, provided_or_resolve, resolve

# Actual value must always come from the trace.
actual = resolve(trace, self.key)

# Inline expected value wins; otherwise resolve expected_value_key.
expected = provided_or_resolve(
    trace,
    key=self.expected_value_key,
    value=self.expected_value,
)
```

When `resolve(...)` returns `NoMatch`, return `CheckResult.error(...)`. Use
`CheckResult.failure(...)` only after the assertion could be evaluated and did
not hold.

## Registration and serialization

`@Check.register("kind")` attaches a discriminator used in `model_dump()` and
`model_validate(...)`.

```python
payload = ContainsRequiredFields(required=["answer"]).model_dump()
assert payload["kind"] == "contains_required_fields"

# Import the module that defines ContainsRequiredFields before this call.
restored = Check.model_validate(payload)
```

Rules:

1. Pick a unique snake_case kind string.
2. Decorate the class definition with `@Check.register("kind")`.
3. Import the module defining the class before deserializing any payload that
   uses that kind.
4. Avoid duplicate kind strings; registration fails when the same base already
   knows that kind.
5. Keep custom classes importable from stable module paths in your project or
   package.

## Test placement and coverage

Place tests with the code that owns the custom check. For a project-local check,
put tests in that project's normal test area and import the custom-check module
in test setup before deserialization assertions. For package contributions,
mirror the package's existing organization: deterministic checks with built-in
check tests, LLM judges with judge tests, and generators with generator tests.

Cover at least:

- Passing assertion.
- Failing assertion.
- Missing JSONPath (`NoMatch`) returns `error` with the key in the message.
- Wrong extracted type returns `error`.
- Serialization round-trip via `model_dump()` and `Check.model_validate(...)`.
- Invalid JSONPath rejected at model construction for each `key` / `*_key`.
- For LLM checks, mocked generator pass/fail behavior plus validation of the
  structured output model.

## Custom LLM check outline

```python
from typing import Any

from giskard.agents import TemplateReference
from giskard.checks import BaseLLMCheck, Check, CheckResult, Trace
from pydantic import BaseModel, Field


class ScoreResult(BaseModel):
    score: float = Field(ge=0, le=1)
    passed: bool
    reason: str = Field(min_length=1)


@Check.register("scored_helpfulness")
class ScoredHelpfulness(BaseLLMCheck[Any, Any, Trace[Any, Any]]):
    threshold: float = 0.8

    @property
    def output_type(self) -> type[BaseModel]:
        return ScoreResult

    def get_prompt(self) -> TemplateReference | str:
        return (
            "Score helpfulness from 0 to 1 for the last answer.\n"
            "Question: {{ trace.last.inputs }}\n"
            "Answer: {{ trace.last.outputs }}"
        )

    async def _handle_output(
        self,
        output_value: ScoreResult,
        template_inputs: dict[str, Any],
        trace: Trace[Any, Any],
    ) -> CheckResult:
        details = {"score": output_value.score, "reason": output_value.reason}
        if output_value.score >= self.threshold and output_value.passed:
            return CheckResult.success(message=output_value.reason, details=details)
        return CheckResult.failure(message=output_value.reason, details=details)
```

LLM checks still need an explicit `generator=` or a configured default generator
at run time. They should return actionable `CheckResult` messages and structured
`details` so suite and JUnit reports remain useful.
