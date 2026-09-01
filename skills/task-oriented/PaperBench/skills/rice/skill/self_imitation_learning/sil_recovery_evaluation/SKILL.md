---
name: sil_recovery_evaluation
description: Validate Self-Imitation Learning recovery evidence for source boundaries, executable metrics, and mechanism-faithful proxy checks.
---

# SIL Recovery Evaluation

Use this skill after running a SIL recovery experiment. It is designed for soft-mode reduced recoveries and full actor-critic recoveries that need auditable acceptance checks before analysis.

Do not use this skill to waive missing executable evidence; it should reject missing command logs, missing optimizer-step evidence, or original-repository source leakage.

## Inputs
- Recovery result JSON.
- Experiment command log JSON.
- Generated skill invocation log JSON.
- Source manifest JSON.
- Optional training trace JSON.

## Outputs
- Validation JSON with `ok`, `errors`, `warnings`, and metric summary.
- Mechanism checklist suitable for Distiller analysis.

## Workflow
1. Check that source manifest entries do not include the original source repository during recovery.
2. Check that a successful command produced the recovery result.
3. Check that generated skills were invoked or cross-checked.
4. Check that proxy mechanism booleans include replay insertion, positive-advantage loss, optimizer step, and parameter change.
5. Report metric and loss-change evidence.

## Validation
Run:

```bash
python tests/test_evaluate_recovery.py
```

The test validates a minimal passing proxy result and a failing result with missing optimizer evidence.

## Limitations
- This is a SIL-specific supplement to Distiller's generic `validate_recovery_experiment.py`; run both when finishing a recovery.

## Source-Boundary Negative Test
The recovery source manifest should not include the original implementation repository path, even as a convenience reference. Record source-boundary status without embedding forbidden paths in recovery evidence.
