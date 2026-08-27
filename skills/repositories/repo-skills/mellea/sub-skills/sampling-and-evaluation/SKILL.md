---
name: sampling-and-evaluation
description: "Use Mellea 0.8.0.dev0 sampling, requirements, verifiers,
  evaluators, metrics, and m eval workflows to make generation more reliable and
  measure outputs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sampling and evaluation

Use this route when the task involves retries, rejection, majority voting,
feedback, a verifier, an LLM judge, generated-code tests, benchmarks, metrics,
or `m eval`. It turns a generation call into an explicit **candidate → check →
repair/select → report** pipeline.

## Route first

1. Decide whether the goal is reliability during one generation or evaluation
   across a dataset. Use [strategies.md](references/strategies.md) for the
   former and [evaluators-and-verifiers.md](references/evaluators-and-verifiers.md)
   for the latter.
2. Make every check that can be expressed in Python deterministic. Reserve
   LLM-as-a-judge for semantic or subjective criteria, and label its result
   qualitative and model-dependent.
3. Bound both attempts and tokens before running a model. With
   `concurrency_budget > 1`, the upper bound is approximately
   `loop_budget * concurrency_budget` generations per base action; majority
   voting multiplies this again by `number_of_samples`.
4. Use `return_sampling_results=True` when failure diagnosis, per-attempt
   comparisons, or evidence is needed. Otherwise consume the output thunk.
5. For bulk judge evaluation, validate the dataset shape first, then run
   `m eval run`; the bundled validator checks a local configuration without
   opening files, calling a backend, or executing generated code.

## Strategy decision table

| Need | Start with | Important output/limit |
|---|---|---|
| Retry an unchanged prompt | `RejectionSamplingStrategy` | First passing attempt; failed fallback is index 0 |
| Give repair reasons to an instruction | `RepairTemplateStrategy` | Copy of `Instruction` with failed reasons |
| Continue a conversation while repairing | `MultiTurnStrategy` | Requires `ChatContext`; failed fallback is last attempt |
| Fast solver then escalation | `SOFAISamplingStrategy` | S1 loop, then one S2 attempt |
| Consensus-like math/text selection | MBRD strategy | Pairwise score maximum, not a semantic guarantee |
| Force a reasoning token budget | direct budget-forcing module | Ollama-only and usage metadata required |
| Safe generated Python checks | code-generation preset | Prefer static or Docker policy; never trust an allowlist as isolation |

## Reliability contract

A `Requirement` validates the latest model output and returns a
`ValidationResult`. A passing result is `bool(result)` or
`result.as_bool()`—there is no public `.result` property on
`ValidationResult`. Failure `reason` is the repair signal. `score`, `thunk`,
and `context` are optional evidence, not automatic acceptance criteria.

`SamplingResult` contains `success`, the selected `result`, and parallel
histories: `sample_generations`, `sample_validations`, `sample_actions`, and
`sample_contexts`. Treat `success=False` as a failed reliability gate even
though a best-effort selected output is still available.

## Evaluation contract

`TestBasedEval.from_json_file()` accepts one object or a JSON array. Each test
needs `source`, `name`, `instructions`, `id`, and a non-empty `examples` list.
Examples contain role/content messages; the last user message becomes the
input and assistant messages become reference targets. `set_judge_context()`
then supplies input, prediction, target(s), and guidelines to one judge call.

The `m eval` runner produces per-input `score`, `passed`, and `justification`,
plus per-test and overall pass rates. A missing or unparsable score is a failed
input. Do not compare raw judge prose as if it were a deterministic metric.

## Safety and boundaries

Generated code is untrusted input. Static Python requirements parse and inspect
without execution. If execution is required, choose a declared policy and
prefer the Docker tier; `ImportRestrictions` is only an AST check, not a
security boundary. Do not put generated code, shell commands, credentials, or
network side effects into the configuration validator.

`seed` in `model_options` is only a request to the selected backend; it does
not make providers, retries, concurrency, or judges universally reproducible.
Record model, backend, strategy, budgets, seed, requirement definitions, and
raw validation reasons with benchmark results.

## Handoff and related routes

- Typed `@generative`, Pydantic output, parsing, and structured generation:
  route to `generative-programming`.
- General `m` command discovery, serving, backend flags, and deployment:
  route to `serving-and-cli`; this route owns only evaluation semantics and
  the `m eval` contract.
- Hooks and OpenTelemetry setup details: route to
  `observability-and-extensions`; this route records which evaluation signals
  are useful.

Read [api-reference.md](references/api-reference.md) for exact signatures,
[evaluators-and-verifiers.md](references/evaluators-and-verifiers.md) for
assertion-backed patterns, [cli-reference.md](references/cli-reference.md) for
`m eval`, and [troubleshooting.md](references/troubleshooting.md) before
classifying a failure as a model failure.