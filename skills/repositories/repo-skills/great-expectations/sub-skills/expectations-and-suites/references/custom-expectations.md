# Custom Expectations

Use a custom expectation subclass when repeated ad hoc checks have stable business meaning, default parameters, and wording that should travel with the suite. Do not create a custom class just to vary one threshold once; instantiate a built-in expectation with explicit parameters instead.

## Subclass a Built-In Expectation

The lowest-risk customization pattern is to inherit from a built-in class and set defaults as typed class attributes:

```python
import great_expectations as gx

class ExpectValidPassengerCount(gx.expectations.ExpectColumnValuesToBeBetween):
    column: str = "passenger_count"
    min_value: int = 1
    max_value: int = 6
    description: str = "There should be between **1** and **6** passengers."

expectation = ExpectValidPassengerCount()
```

Guidance:

- Use a class name that describes the business rule; GX derives the snake_case `expectation_type` from the class name.
- Keep default fields aligned with the base expectation's declared parameters.
- Keep `description` accurate if callers override defaults; if overrides would make the description false, prefer not to override them or create a more generic description.
- Add the subclass instance to a suite exactly like a built-in expectation: `suite.add_expectation(ExpectValidPassengerCount())`.
- Test the subclass against a representative `Batch` before relying on it in a suite.

## Registry and Serialization Constraints

- Expectation classes register when imported through the `MetaExpectation` metaclass. A custom class must be importable in any runtime that loads or validates suites containing it.
- The serialized expectation type is the class name converted to snake_case unless the class sets `expectation_type` explicitly.
- If a persisted suite references a custom expectation type that is not importable in the current process, registry lookup can fail with `ExpectationNotFoundError` or suite loading errors.
- Avoid local-only module paths, notebooks, or dynamically generated classes for suites that must run in production. Package custom expectations in normal Python modules loaded before validation.
- Keep custom expectation fields JSON-serializable when they become expectation configuration kwargs.

## Defaults and Descriptions

Good custom subclasses define one stable semantic rule:

```python
class ExpectActiveStatusVocabulary(gx.expectations.ExpectColumnValuesToBeInSet):
    column: str = "status"
    value_set: list[str] = ["new", "active", "paused", "closed"]
    mostly: float = 1.0
    severity: str = "critical"
    description: str = "Status must be one of the active product lifecycle values."
```

Prefer these practices:

- Defaults should be business-owned and reusable, not copied from a one-off data sample.
- Keep `mostly` between `0` and `1`; use `1.0` unless there is an explicit tolerance.
- Use `severity` to express business impact, not debugging priority.
- Use `meta` on instances for ownership/rationale, not in class defaults unless it applies everywhere.

## Diagnostics and Testing

For simple subclasses of existing expectations, validate against a tiny known-good and known-bad batch:

```python
passing = batch.validate(ExpectActiveStatusVocabulary())
assert passing.success
```

For deeper custom expectations that define new metrics or rendering, use GX diagnostics/testing patterns before shipping:

- Run `Expectation.run_diagnostics(...)` when available for the custom class to inspect examples, renderers, metrics, and backend support.
- Provide example cases that include success, failure, null/missing behavior, and backend-specific edge cases.
- Check serialization by adding the custom expectation to an `ExpectationSuite`, converting to JSON/dict, then loading or validating in a fresh process where the class is imported.
- Verify renderer text if Data Docs will be used; incorrect descriptions are more harmful than generic descriptions.

## When to Avoid Custom Classes

Avoid a custom subclass when:

- The rule is just one suite-specific threshold; use a built-in expectation with `meta` or `notes`.
- The value changes each run; use `$PARAMETER` and validation-time `expectation_parameters`.
- The check is row-filtered but otherwise standard; use `row_condition`.
- The desired logic requires joining to another datasource or full validation orchestration; route to `../validations-and-results/SKILL.md` or use `UnexpectedRowsExpectation` where appropriate.
- The custom class cannot be packaged/imported in the production runtime.

## Minimal Conversion Workflow

1. Inventory repeated ad hoc checks and identify the common built-in parent class.
2. Name one business concept per subclass.
3. Move stable fields to typed class defaults and write a truthful `description`.
4. Instantiate the subclass without overriding defaults in normal suite code.
5. Validate against a tiny passing and failing batch.
6. Persist the suite only after import/serialization behavior is proven in the target runtime.
