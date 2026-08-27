# checks-evals workflows

These workflows are self-contained package-use recipes. They assume an installed
`giskard.checks` package and avoid source-checkout dependencies.

## Deterministic scenario with structured outputs

Use `Scenario.interact(...).check(...)` for one evaluation path. Static values,
callables, and async callables are accepted. Checks read from the accumulated
`Trace`.

```python
import asyncio
from giskard.checks import Equals, JsonValid, Scenario, StringMatching


def answer(inputs: dict[str, str]) -> dict[str, object]:
    return {
        "answer": f"Paris answers: {inputs['question']}",
        "confidence": 0.98,
        "payload": '{"city": "Paris"}',
    }


async def main() -> None:
    result = await (
        Scenario("capital_answer")
        .interact({"question": "What is the capital of France?"}, answer)
        .check(StringMatching(keyword="Paris", text_key="trace.last.outputs.answer"))
        .check(Equals(expected_value=0.98, key="trace.last.outputs.confidence"))
        .check(JsonValid(key="trace.last.outputs.payload"))
        .run()
    )
    assert result.passed, result.failures_and_errors


asyncio.run(main())
```

Notes:

- Prefer `trace.last.outputs.<field>` over `trace.interactions[-1]...` for the
  current turn.
- `JsonValid(parse=True)` expects a serialized JSON string. Use
  `JsonValid(parse=False)` for already-parsed dicts/lists/scalars.
- A scenario with interactions and no checks passes, but it is usually less
  useful than adding at least one assertion.

## Suite with a shared target

Use a `Suite` when multiple scenarios exercise the same system under test.
`Suite.run(verbose=False)` is a good default for scripts and CI logs.

```python
import asyncio
from giskard.checks import Equals, Scenario, Suite


def target(inputs: str) -> str:
    return f"Echo: {inputs}"


async def main() -> None:
    scenario_a = (
        Scenario("echo_hello")
        .interact("hello")
        .check(Equals(expected_value="Echo: hello", key="trace.last.outputs"))
    )
    scenario_b = (
        Scenario("echo_world")
        .interact("world")
        .check(Equals(expected_value="Echo: world", key="trace.last.outputs"))
    )

    suite = Suite(name="echo_suite", target=target).append(scenario_a).append(scenario_b)
    suite_result = await suite.run(verbose=False)
    assert suite_result.pass_rate == 1.0, suite_result.failures_and_errors


asyncio.run(main())
```

Target precedence is `run(target=...)` over `Suite(target=...)` over
`Scenario(target=...)`. Use `parallel=True` only when the target is concurrency
safe and provider/rate limits are understood; `max_concurrency` caps parallel
scenario execution. Use `return_exception=True` when you want errors captured in
results rather than raised immediately.

## Composition patterns

Use composition checks to keep scenario steps readable.

```python
from giskard.checks import AllOf, AnyOf, Equals, Not, StringMatching

check = AllOf(
    checks=[
        StringMatching(keyword="approved", text_key="trace.last.outputs.status"),
        AnyOf(
            checks=[
                Equals(expected_value="gold", key="trace.last.outputs.tier"),
                Equals(expected_value="platinum", key="trace.last.outputs.tier"),
            ]
        ),
        Not(check=StringMatching(keyword="forbidden")),
    ]
)
```

`AllOf` and `AnyOf` short-circuit internally. `Not` inverts pass/fail only and
passes through `error`/`skip` unchanged.

Use `from_fn` for local, one-off checks that do not need portable
serialization:

```python
from giskard.checks import CheckResult, from_fn


def has_audit_id(trace):
    last = trace.last
    if last is None:
        return CheckResult.error(message="No interaction was recorded")
    return "audit_id" in last.metadata

check = from_fn(has_audit_id, name="has_audit_id")
```

For reusable serialized checks, write a registered `Check` subclass instead;
see `custom-checks.md`.

## JSONPath extraction in practice

- Use scalar keys (`trace.last.outputs.answer`) when a check expects one value.
- Use wildcard or descendant keys (`trace.interactions[*].outputs.score`,
  `trace..score`) only when you expect a list.
- For collection comparisons, pass `match="any"`, `match="all"`, or
  `match="none"` to comparison checks.

```python
from giskard.checks import GreaterEquals

score_check = GreaterEquals(
    key="trace.interactions[*].outputs.score",
    expected_value=0.8,
    match="all",
)
```

A missing scalar key is an evaluation `error`, not an assertion `fail`; fix the
selector or output shape.

## LLM judge workflow

Judge checks need a working `giskard.agents.Generator`. You can pass one per
check or configure a default for all judge checks. A live generator usually
requires the provider package extra, provider configuration, network access, and
a provider API key such as `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`,
or `ANTHROPIC_API_KEY` depending on the provider.

```python
import asyncio
from giskard.agents import Generator
from giskard.checks import Groundedness, Scenario, set_default_generator

set_default_generator(Generator(model="openai/gpt-4o-mini"))

async def main() -> None:
    result = await (
        Scenario("grounded_answer")
        .interact(
            inputs="Where is the Eiffel Tower?",
            outputs="The Eiffel Tower is in Paris.",
            metadata={"context": ["The Eiffel Tower is a landmark in Paris."]},
        )
        .check(Groundedness())
        .run()
    )
    assert result.passed

asyncio.run(main())
```

Use direct fields when the trace shape does not match defaults:

```python
from giskard.checks import AnswerRelevance, Contradiction, LLMJudge

AnswerRelevance(
    question_key="trace.last.inputs.question",
    answer_key="trace.last.outputs.answer",
    context="The assistant answers travel questions.",
)
Contradiction(
    answer_key="trace.last.outputs.answer",
    context_key="trace.last.metadata.documents",
)
LLMJudge(
    prompt=(
        "Judge whether this answer is concise.\n"
        "Question: {{ trace.last.inputs }}\n"
        "Answer: {{ trace.last.outputs }}\n"
        "Return JSON with boolean passed and non-empty reason."
    )
)
```

Do not run live judges in no-key environments. Prefer deterministic checks,
mocked generators in tests, or a planning-only evaluation until provider setup
is complete.

## Input generation workflow

Use generators as the `inputs=` argument to `interact(...)`.

```python
from giskard.checks import DatasetInputGenerator, LLMGenerator, Scenario, UserSimulator

# No LLM call for a string target: the prompt is yielded verbatim.
dataset_scenario = Scenario("dataset_case").interact(
    DatasetInputGenerator(prompt="Ask about refund policy"),
    outputs=lambda inputs: f"Received: {inputs}",
)

# LLM-backed generation: requires a working generator/default generator.
llm_scenario = Scenario("llm_user").interact(
    LLMGenerator(prompt="Play a customer asking one billing question.", max_steps=2),
    outputs=lambda inputs: f"Answering: {inputs}",
)

persona_scenario = Scenario("persona_user").interact(
    UserSimulator(
        persona="A polite user who needs step-by-step help",
        context="Ask about account recovery",
        max_steps=3,
    ),
    outputs=lambda inputs: "I can help with that.",
)
```

`DatasetInputGenerator` uses the LLM only for structured non-string target input
types, where it asks for a schema template containing `{{prompt}}` and then
injects the real prompt locally.

## Serialization round-trip

Registered discriminated classes include a computed `kind` in dumps. Import
custom registered classes before validation.

```python
from giskard.checks import Check, Equals, Scenario

scenario = (
    Scenario("serializable")
    .interact("hello", "Echo: hello")
    .check(Equals(expected_value="Echo: hello", key="trace.last.outputs"))
)

payload = scenario.model_dump()
restored = Scenario.model_validate(payload)
check_payload = scenario.steps[0].checks[0].model_dump()
restored_check = Check.model_validate(check_payload)
```

`FnCheck` excludes the Python callable from serialization. If the serialized
artifact must be portable, use a registered custom class rather than `from_fn`.

## JUnit export workflow

Export at the `SuiteResult` level:

```python
import asyncio
from pathlib import Path
from giskard.checks import Equals, Scenario, Suite
from giskard.checks.export.junit import to_junit_xml

async def main() -> None:
    suite = Suite(name="junit_demo", target=lambda inputs: inputs)
    suite.append(Scenario("ok").interact("x").check(Equals(expected_value="x", key="trace.last.outputs")))
    result = await suite.run(verbose=False)

    xml_text = result.to_junit_xml()
    same_xml = to_junit_xml(result, path=Path("junit-giskard-checks.xml"))
    assert xml_text.startswith("<testsuite")
    assert same_xml.startswith("<testsuite")

asyncio.run(main())
```

The JUnit export maps failed scenarios to `<failure>`, errored scenarios to
`<error>`, skipped scenarios to `<skipped>`, and includes metrics/properties in
XML-friendly fields.
