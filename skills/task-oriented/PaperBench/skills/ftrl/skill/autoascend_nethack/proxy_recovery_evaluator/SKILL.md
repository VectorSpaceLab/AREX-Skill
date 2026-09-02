---
name: proxy_recovery_evaluator
description: Validate soft recovery traces by checking AutoAscend mechanism evidence and pass-rate metrics.
---
# Proxy Recovery Evaluator

Use this skill after a bounded AutoAscend recovery run produces trace artifacts. It determines whether a proxy run exercised the symbolic mechanisms claimed by the module plan. Do not use it to excuse missing executable evidence or original-repository dependence.

## Inputs
- A trace containing generated skill invocation names, state memory, selected strategy, combat ranking, survival decision, command evidence, and optional optimizer trace.
- Recovery target metadata from the module plan.

## Outputs
- Boolean mechanism checks.
- Numeric `mechanism_pass_rate`.
- Missing evidence list for refinement.

## Workflow
1. Confirm every core generated skill has invocation evidence.
2. Confirm state memory contains derived flags and remembered levels.
3. Confirm strategy selection has an explicit action queue and interruption evidence when urgent flags are present.
4. Confirm combat ranking includes safety reasons.
5. Confirm survival rules produce an ordered decision.
6. Confirm executable command evidence exists.
7. Compute pass rate from all checks.

## Validation
Run `python tests/test_proxy_eval.py` or the bundled skill validator with `--run-tests`.

## Limitations
This evaluator judges proxy mechanism fidelity, not full NLE challenge score. Soft-mode acceptance still requires a valid recovery experiment gate and source-boundary compliance.
