---
name: sbi_recovery_experiment_harness
description: Run a bounded source-boundary-safe recovery experiment for the sbi toolkit workflow.
---

# SBI Recovery Experiment Harness

Use this skill to execute a mechanism-faithful recovery experiment for the sbi toolkit paper without reading the original repository during recovery.

Do not use it during modularization, where repository evidence is allowed.

## Inputs
- Runtime handoff JSON.
- Generated skill root.
- Recovery mode and target declaration.
- Forbidden original repository path.

## Outputs
- Experiment command log.
- Generated skill invocation log.
- Recovery result JSON.
- Experiment validation JSON.

## Workflow
1. Read the runtime handoff and select the strongest feasible target.
2. Enforce the forbidden original-repository boundary.
3. Invoke the generated simulator protocol, family selector, SNPE proxy, and diagnostics helpers.
4. Save mechanism checks proving prior sampling, simulator execution, conditional posterior estimation, posterior sampling, and diagnostics.
5. In soft mode, declare reduced/proxy recovery when full package execution is blocked.

## Validation
Run:

```bash
python scripts/check_recovery_contract.py --result-json recovery_result.json --forbidden-path /path/to/original/repo
python tests/test_check_recovery_contract.py
```

## Limitations
- Hard mode cannot accept proxy recovery.
- This harness validates the workflow mechanism, not a paper leaderboard metric.
