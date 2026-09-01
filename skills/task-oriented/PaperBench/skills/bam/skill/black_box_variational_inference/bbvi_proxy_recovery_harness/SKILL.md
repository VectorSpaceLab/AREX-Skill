---
name: bbvi_proxy_recovery_harness
description: Run a bounded mechanism-faithful proxy recovery for Black Box Variational Inference using generated BBVI estimator and optimizer skills.
---

# BBVI Proxy Recovery Harness

## When To Use

Use this skill when full BBVI paper reproduction is blocked by unavailable private data or long runtime, and soft-mode recovery permits an explicit proxy. The proxy must still execute score-function gradients, variance reduction, and stochastic optimization.

Do not use it as success evidence in hard recovery mode or when a full real-data result is feasible within budget.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing `bbvi_score_function_gradient`, `bbvi_variance_reduction`, and `bbvi_stochastic_optimizer`.
- Fixed seed and small synthetic Normal observations.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_skill_invocations.json`.
- Numeric variance-reduction and optimizer evidence.

## Workflow

1. Load the module plan and runtime handoff.
2. Generate synthetic Normal observations from a fixed seed.
3. Build deterministic BBVI sample arrays and log-density signals.
4. Invoke generated score-gradient, variance-reduction, and optimizer scripts by subprocess.
5. Record invocation evidence and mechanism checks.
6. Write a validation-ready recovery result whose target matches the module plan.

## Validation

Run:

```bash
python tests/test_proxy_harness.py
```

## Limitations

This is a reduced/proxy recovery. It does not reproduce the medical-data predictive likelihood table or the 20-hour MCMC comparison.
