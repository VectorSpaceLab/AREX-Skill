# Evaluators, verifiers, and safe test workflows

Separate **verification** (a bounded check with a clear contract) from
**evaluation** (measurement over examples). A verifier can gate a retry; an
evaluator should preserve the full evidence needed to audit the measurement.

## Deterministic verifier pattern

Use `simple_validate` when the latest output string is sufficient:

```python
from mellea.core import ModelOutputThunk
from mellea.stdlib.context import ChatContext
from mellea.stdlib.requirements import req, simple_validate

short = req(
    "The answer is at most 20 words.",
    validation_fn=simple_validate(
        lambda text: (
            len(text.split()) <= 20,
            f"Got {len(text.split())} words; limit is 20.",
        )
    ),
)
ctx = ChatContext().add(ModelOutputThunk("one two three"))
verdict = short.validation_fn(ctx)
assert verdict.as_bool() is True
assert verdict.reason == "Got 3 words; limit is 20."
```

This assertion runs only the deterministic validator; it does not call a
backend. To test a model-dependent requirement, use a fake backend and assert
its call/return contract separately. Do not claim that a model output passed
unless the validator actually ran on that output.

For context-aware checks, return `ValidationResult` explicitly:

```python
import json
from mellea.core import Context, Requirement, ValidationResult

def valid_json(ctx: Context) -> ValidationResult:
    output = ctx.last_output()
    text = str(output.value) if output and output.value is not None else ""
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return ValidationResult(False, reason=f"Invalid JSON at {exc.pos}: {exc.msg}")
    return ValidationResult(True, reason="JSON parsed")

json_requirement = Requirement("Output must be JSON.", validation_fn=valid_json)
```

Multiple requirements are evaluated after each candidate. All must be truthy
for a base sampling success. A deterministic validator may be paired with a
natural-language `req()` or silent `check()`; the latter avoids steering the
generation prompt but still invokes a judge unless it has a `validation_fn`.

## Assertion-backed sampling inspection

Use a fake backend for unit tests and inspect the result contract, not generated
quality. A backend double should return a `ModelOutputThunk`, attach a
`GenerateLog`, and return a context containing the action/output. Then:

```python
from mellea.core import GenerateLog, ModelOutputThunk, Requirement, ValidationResult
from mellea.stdlib.components import Instruction
from mellea.stdlib.context import ChatContext
from mellea.stdlib.sampling import RejectionSamplingStrategy

# In an async test, use a fake backend with generate_from_context(...).
strategy = RejectionSamplingStrategy(loop_budget=2, concurrency_budget=1)
requirement = Requirement("always passes", validation_fn=lambda _: ValidationResult(True))
assert strategy.loop_budget == 2
assert strategy.concurrency_budget == 1
assert requirement.description == "always passes"
```

Native tests exercise the stronger assertions: failed `RepairTemplateStrategy`
reasons appear in the repaired instruction; `MultiTurnStrategy` grows a chat
context; concurrency stops after success; backend exceptions are not swallowed;
and opaque `CBlock`/`ModelOutputThunk` actions do not require `.parse()`.
Those are deterministic API checks and do not prove model quality.

## Unit-test generative code data

A test file is a JSON object or array of objects. Each object has:

```json
{
  "source": "email",
  "name": "professional-email",
  "instructions": "The response follows the requested tone and content.",
  "id": "email-001",
  "examples": [
    {
      "input_id": "case-1",
      "input": [{"role": "user", "content": "Write a short thank-you email."}],
      "targets": [{"role": "assistant", "content": "Thank you for your time."}]
    }
  ]
}
```

`TestBasedEval.from_json_file()` validates the Pydantic data model and rejects
an empty `examples` list. It selects the last user message from each example,
skips examples with no user message, and extracts only assistant-role target
messages. Keep `input`, `targets`, and `input_ids` aligned after filtering.
Multiple targets are references, not exact-match alternatives enforced by
Mellea. The judge receives all references as numbered text; it decides whether
the prediction meets `instructions`.

`TestBasedEval` is a formatting component. A caller must generate a prediction,
call `set_judge_context(input, prediction, targets)`, then pass the component
to a judge session. The component does not perform the candidate generation or
parse the judge result.

## LLM-as-a-judge

A `Requirement` without `validation_fn` makes a separate judge call. The default
boolean converter looks for `yes` in the judge output, so use a deterministic
validator when a criterion is machine-checkable. For a judge-based score,
record the raw judge output, prompt/guidelines, model/backend, and parsing
result. A larger or different judge may change pass rates; no source evidence
supports treating a judge pass as ground truth.

The `m eval` runner uses a separate generation session and judge session. For
each input it generates one candidate, asks the judge once, parses a JSON object
containing `score` and optional `justification`, then falls back to a textual
`score: N` pattern. `score == 1` passes; an absent score fails. Its result
schema is described in [cli-reference.md](cli-reference.md).

## Safe generated-code evaluation

Use a layered gate:

1. `PythonCodeExtraction` finds a code block or supported code-bearing tool
   field.
2. `PythonSyntaxValid` parses with `ast.parse` and does not execute.
3. `PythonExecutionReq` is static by default; choose `local`, `local_unsafe`,
   `docker`, or `docker_unsafe` only deliberately.
4. `ImportRestrictions` checks static imports but is not a sandbox.
5. Enforce output and timeout limits in the execution policy.

For untrusted or externally supplied code, prefer Docker with a restrictive
`CapabilityPolicy`, and do not pass secrets or writable production paths into
the environment. Never use the configuration validator in this skill to run,
compile, import, or inspect generated code.

## Metrics and comparison

Evaluation metrics available without a judge are counts and rates: per-input
`passed`, `score`, `total_count`, and `pass_rate`, plus aggregate pass rate.
Keep denominators and skipped/error cases explicit. A pass rate changes if you
silently skip malformed cases, so treat `continue_on_error` as a reporting
choice and preserve the skipped-test count in surrounding records.

When telemetry is enabled, Mellea records sampling attempts/successes/failures
and requirement checks/failures through plugins; token, duration, error, and
cost signals are separate operational evidence. Configuration and hook details
belong to `observability-and-extensions`. These metrics describe runtime
behavior, not correctness.

## Hard-case test ideas

- **Nested deterministic output:** a fake backend returns two JSON candidates,
  one with nested arrays and one with a malformed child. A custom verifier must
  inspect the nested structure without calling a judge; assert the selected
  index, `success`, and per-requirement reasons.
- **Judge preflight:** a configuration has `test_files` and `threshold: 1.5`
  but no `backend`; the bundled validator must report both missing backend and
  invalid threshold, with no model/backend/file execution. See
  `scripts/validate_eval_config.py`.
