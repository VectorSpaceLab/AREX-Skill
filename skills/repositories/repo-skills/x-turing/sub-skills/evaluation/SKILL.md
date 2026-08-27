---
name: evaluation
description: "Enable built-in perplexity evaluation with `model.evaluate` and
  scaffolded adapter-based evaluation with persisted JSON results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill for xTuring evaluation work that stays inside the package's current contract.

## When to use
- Score a causal model with `model.evaluate(...)` and get a single perplexity scalar.
- Wrap an evaluation backend behind `BaseEvalAdapter`.
- Persist a standardized `EvalRunResult` JSON artifact with `run_eval_adapter(...)` or `persist_eval_result(...)`.
- Inspect or normalize `EvalMetric` and `EvalRunResult` payloads.

## When not to use
- The dataset schema is still invalid or needs conversion.
- You need model selection, loading, generation config tuning, or inference debugging.
- You need training, serving, or API/UI behavior.
- You expect full lm-evaluation-harness execution; the current adapter is scaffold-only.

## Read in this order
1. `references/evaluation-workflows.md`
2. `references/api-reference.md`
3. `references/troubleshooting.md`

## Main entry points
- `CausalModel.evaluate(dataset, batch_size=1)`
- `BaseEvalAdapter`
- `LMEvalAdapter`
- `run_eval_adapter(...)`
- `persist_eval_result(...)`
- `EvalMetric`
- `EvalRunResult`

## Contract summary
- `model.evaluate(...)` returns one perplexity tensor, not a metric table.
- `run_eval_adapter(...)` returns `EvalRunResult` and fills timing fields when the adapter does not.
- `persist_eval_result(...)` writes the result as UTF-8 JSON with parent directories created as needed.
- `LMEvalAdapter` currently returns `status="planned"` and `metadata["integration_status"]="scaffold_only"`.

## Safe smoke check
Use `scripts/evaluation_scaffold_smoke.py` to verify the adapter and persistence contract without downloading a model.

If a dataset fails validation, fix it in the data sub-skill first; evaluation assumes an already-valid dataset object.
