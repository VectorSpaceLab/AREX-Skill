---
name: proxy_recovery_evaluator
description: Evaluate soft-mode REINFORCE proxy recoveries for target consistency, numeric metrics, and mechanism-faithful evidence.
---

# Proxy Recovery Evaluator

Use this skill after a reduced REINFORCE recovery has produced a training trace and recovery result. It checks whether the proxy is acceptable evidence for the paper mechanism under soft mode. Do not use it to bless a recovery that lacks executable command logs or bypasses stochastic score-function training.

## Inputs

- Module-plan fast recovery target.
- Recovery result with `metrics`, `paper_target`, `is_proxy`, and `mechanism_checks`.
- Training trace with `params_before`, `params_after`, and reward metrics.
- Generated skill invocation records.

## Outputs

- `accepted`: boolean proxy decision.
- `errors`: mechanism or metadata failures.
- `metric_gap`: recovered metric minus declared target value.
- `mechanism_summary`: compact copy of required mechanism booleans.

## Workflow

1. Require proxy mode for the seeded bandit reduced recovery.
2. Confirm recovery target metadata matches the module plan.
3. Confirm the declared metric is numeric and reaches the proxy threshold.
4. Confirm stochastic sampling, score-function update computation, baseline use, reduced training, and optimizer parameter change.
5. Confirm generated skills were called or cross-checked.
6. Return concrete errors for missing mechanism evidence.

## Validation

Run:

```bash
python scripts/evaluate_proxy.py --module-plan module_plan.json --recovery-result recovery_result.json --training-trace training_trace.json --invocations generated_skill_invocations.json
python -m pytest tests
```

Tests cover both an accepted mechanism-faithful proxy and a rejected high-metric result with no optimizer evidence.

## Limitations

The evaluator checks artifact consistency and mechanism evidence; it does not replace the Distiller recovery experiment gate or final attempt validator.
