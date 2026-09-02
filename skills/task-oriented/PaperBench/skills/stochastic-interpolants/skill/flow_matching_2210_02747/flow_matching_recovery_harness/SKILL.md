---
name: flow_matching_recovery_harness
description: Run a bounded soft-mode Flow Matching proxy recovery that invokes generated OT-path, CFM-loss, and CNF-ODE skills.
---

# Flow Matching Recovery Harness

Use this skill when validating whether generated Flow Matching skills can execute the paper's core mechanism under bounded soft-mode recovery. The harness must not read the original source repository and must clearly label proxy evidence.

## Inputs

- Attempt directory with `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing `conditional_ot_paths`, `conditional_flow_matching_loss`, and `cnf_ode_sampling`.
- Deterministic synthetic noise/data pairs for a small OT-CFM proxy.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/source_manifest.json`.

## Workflow

1. Read the module-plan target and runtime handoff.
2. Build deterministic paired vectors that define an analytic OT displacement problem.
3. Import and call the generated OT-path, CFM-loss, and ODE-sampling scripts.
4. Run a scalar proxy optimizer update against the CFM loss and record before/after values.
5. Integrate the learned constant vector field and compare to the analytic OT endpoint.
6. Write validator-compatible recovery artifacts with mechanism checks and command provenance.

## Validation

Run:

```bash
python tests/test_proxy_recovery.py
python scripts/run_proxy_recovery.py --attempt-dir /path/to/attempt --skill-root /path/to/generated_skills
```

## Limitations

This harness is a declared reduced/proxy recovery. It validates the paper mechanism on deterministic vectors and must not be reported as full ImageNet/CIFAR-scale reproduction.
