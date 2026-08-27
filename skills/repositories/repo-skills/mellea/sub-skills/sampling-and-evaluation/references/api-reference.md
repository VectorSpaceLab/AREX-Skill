# API reference

This is the public operating surface for Mellea `0.8.0.dev0` on Python 3.11+.
Use imports shown here rather than private helpers.

## Requirements and validation

| Symbol | Import | Contract |
|---|---|---|
| `Requirement` | `mellea.core` or `mellea.stdlib.requirements` | `Requirement(description=None, validation_fn=None, *, output_to_bool=default_output_to_bool, check_only=False)` |
| `ValidationResult` | `mellea.core` or `mellea.stdlib.requirements` | `ValidationResult(result: bool, *, reason=None, score=None, thunk=None, context=None)` |
| `simple_validate` | `mellea.stdlib.requirements` | Wraps `str -> bool` or `str -> (bool, str)` as a context validator |
| `req` | `mellea.stdlib.requirements` | Shorthand for `Requirement` |
| `check` | `mellea.stdlib.requirements` | Requirement with `check_only=True`; it is not included in the generation prompt |
| `LLMaJRequirement` | `mellea.stdlib.requirements` | Forces LLM-as-a-judge rather than an available adapter |
| `ALoraRequirement` | `mellea.stdlib.requirements` | Adapter-backed requirement; backend and adapter availability are prerequisites |

`Requirement.validate(backend, ctx, *, format=None, model_options=None)` is
async. With a `validation_fn`, it calls Python validation and avoids an LLM
judge. Without one, it asks the backend to judge the latest
`ModelOutputThunk`, then converts its answer using `output_to_bool` (the
built-in converter recognizes a standalone or word-level `yes`).

`ValidationResult` exposes `as_bool()`, `reason`, `score`, `thunk`, and
`context`. `bool(validation_result)` is equivalent to `as_bool()`.
A custom validator must return `ValidationResult`; `simple_validate` rejects
other return shapes with `ValueError`. A missing output is a failed check.

`PartialValidationResult` is returned by streaming validation and has
`success` equal to `"pass"`, `"fail"`, or `"unknown"`; do not treat
`unknown` as a definitive violation.

## Sampling result and base strategies

| Symbol | Import | Constructor defaults |
|---|---|---|
| `SamplingResult` | `mellea.core` or `mellea.stdlib.sampling` | `result_index`, `success`, optional histories |
| `RejectionSamplingStrategy` | `mellea.stdlib.sampling` | `loop_budget=1`, `concurrency_budget=1`, `requirements=None` |
| `RepairTemplateStrategy` | `mellea.stdlib.sampling` | Same budgets; appends failed reasons to an `Instruction` |
| `MultiTurnStrategy` | `mellea.stdlib.sampling` | Same budgets; needs `ChatContext` for repair |
| `BaseSamplingStrategy` | `mellea.stdlib.sampling` | Base for custom `repair` and `select_from_failure` |
| `ModelFriendlyRepairStrategy` | `mellea.stdlib.sampling` | Specialized repair feedback for Python checks |

`sample(action, context, backend, requirements, *, validation_ctx=None,
format=None, model_options=None, tool_calls=False, show_progress=True)` is
async. Strategy-level `requirements` supersede per-call requirements when
provided. Constructor budgets must be positive. A successful loop stops at the
first passing slice; an exhausted loop calls `select_from_failure`.

With concurrency, order and total request timing are not deterministic. The
upper-bound request count for a base strategy is
`loop_budget * concurrency_budget`; early success can reduce it. Keep
`concurrency_budget=1` when reproducible ordering matters.

## Built-in strategy-specific APIs

### Presets

```python
from mellea.stdlib.sampling import (
    python_code_generation_sampling,
    python_plotting_sampling,
)

code = python_code_generation_sampling(
    loop_budget=2,
    allowed_imports=None,
    output_limit_chars=10_000,
    timeout_seconds=5,
    use_sandbox=False,
)
plot = python_plotting_sampling(
    output_path=None,
    loop_budget=3,
    allowed_imports=None,
    timeout_seconds=10,
    use_sandbox=True,
)
```

Both return `SamplingPreset(requirements, strategy, feedback_strategy_name,
description, example_usage)`. The code preset bundles extraction, syntax,
execution, output limits, and either import restrictions or an explicit
no-restrictions marker. The default code execution tier is static; set
`use_sandbox=True` to select Docker execution. Plotting adds headless backend
and dependency/file requirements and defaults to sandboxing.

### Majority voting / MBRD

Import `MajorityVotingStrategyForMath` and `MBRDRougeLStrategy` from
`mellea.stdlib.sampling.majority_voting`, not from the package-level export.
Both take `number_of_samples=8`, `weighted=False`, `loop_budget=1`, and
`requirements=None`. Math uses math-aware extraction/verification; Rouge-L
compares text. The current `weighted=True` path uses unit weights and is not a
real confidence weighting feature. Number of underlying sampling runs is up
to `number_of_samples * loop_budget` (with the inner rejection strategy).

### SOFAI

```python
from mellea.stdlib.sampling import SOFAISamplingStrategy
strategy = SOFAISamplingStrategy(
    s1_solver_backend=fast_backend,
    s2_solver_backend=slow_backend,
    s2_solver_mode="fresh_start",  # or continue_chat, best_attempt
    loop_budget=3,
    judge_backend=None,
    feedback_strategy="simple",    # first_error or all_errors
)
```

Both solver arguments must be `Backend` objects. SOFAI requires a
`ChatContext`. It loops S1, may stop early when failure feedback does not
improve, then performs one S2 attempt. With `judge_backend`, requirements
without `validation_fn` are wrapped for that judge; custom Python validators
remain custom validators.

### Budget forcing

Import `BudgetForcingSamplingStrategy` from
`mellea.stdlib.sampling.budget_forcing`. Its constructor requires the keyword
`requirements` argument and defaults to `think_max_tokens=4096`,
`answer_max_tokens=None`, `<think>`/`</think>` markers, and `loop_budget=1`.
It currently asserts `OllamaModelBackend`, disallows tool calls, and requires
per-call token usage. It is a specialized route, not a provider-neutral token
budget.

## Python code requirements

`python_code_generation_requirements(allowed_imports=None,
output_limit_chars=10_000, timeout_seconds=5, use_sandbox=False)` returns four
requirements in order: `PythonCodeExtraction`, `PythonSyntaxValid`,
`PythonExecutionReq`, and `ImportRestrictions` or `NoImportRestrictions`.
`PythonExecutionReq` tiers are `static`, `local_unsafe`, `local`,
`docker_unsafe`, and `docker`. Static parses/import-checks and does not run
code. Use a capability policy and Docker for untrusted code.

`ImportRestrictions` checks static `import` and `from ... import ...` nodes.
Dynamic imports are outside its scope. `PythonCodeExtraction` prefers visible
Python blocks and may fall back to code-bearing tool-call fields; it returns
extracted code in `ValidationResult.reason`, so do not log that reason without
considering sensitive content.

## Evaluation component

| Symbol | Import | Contract |
|---|---|---|
| `Message` | `mellea.stdlib.components.unit_test_eval` | Pydantic `{role: str, content: str}` |
| `Example` | same | `{input: Message[], targets: Message[], input_id: str}` |
| `TestData` | same | `{source, name, instructions, examples, id}`; examples must be non-empty |
| `TestBasedEval` | same | Runtime component built from one test; `targets` and `input_ids` default to empty lists |

`TestBasedEval.from_json_file(filepath)` returns one object per JSON object or
array member. Examples with no user message are skipped. The latest user
message is selected; only assistant target messages are retained. Multiple
assistant targets are enumerated in the judge context, while no targets become
`"N/A"`.

`set_judge_context(input_text, prediction, targets_for_input)` returns `None` and
stores the context used by `format_for_llm()`. The judge component itself does
not parse a verdict; the CLI runner parses the judge text.
