---
name: msfm_mechanism_evaluation
description: Evaluate whether an MSFM recovery result exercised BatchOT coupling, Joint CFM loss, optimizer evidence, and soft-mode proxy constraints.
---

# MSFM Mechanism Evaluation

Use this skill after a Multisample Flow Matching recovery experiment has produced `recovery_result.json`, `training_trace.json`, and generated skill invocation logs.

Do not accept a proxy run only because its metric is positive; this skill checks whether the recovery exercised the paper mechanisms and respected source/runtime boundaries.

## Inputs

- Recovery result JSON.
- Training trace JSON.
- Generated skill invocation log.
- Optional minimum transport-cost reduction threshold.

## Outputs

- Mechanism pass/fail report.
- Metric gap summary.
- Refinement hints assigned to module-level causes.

## Workflow

1. Confirm proxy status is declared when full recovery is not claimed.
2. Verify BatchOT and uniform couplings were evaluated and double-stochastic evidence passed.
3. Verify Joint CFM loss and an optimizer step were executed.
4. Verify reduced/full booleans are honest and no original repository was read.
5. Confirm generated skill invocations cover coupling, loss, recovery, and evaluation modules.
6. Return actionable hints for missing mechanism evidence.

## Validation

Run:

```bash
python scripts/evaluate_mechanism.py --self-test
python tests/test_evaluate_mechanism.py
```

## Limitations

- This skill evaluates reduced/proxy mechanism evidence; it does not compare full ImageNet FID.
