---
name: opal_recovery_evaluation
description: Validate OPAL recovery evidence, mechanism checks, source boundaries, and proxy metric comparison.
---

# OPAL Recovery Evaluation

## When To Use
Use this skill after a recovery harness produces OPAL metrics. It checks whether the result is a mechanism-faithful OPAL recovery rather than a generic controller success.

## Inputs
- Module-plan target metadata.
- Recovery result JSON.
- Generated skill invocation evidence.
- Source manifest and experiment command log.

## Outputs
- Evaluation summary with metric gap and mechanism status.
- Boolean pass/fail for proxy acceptance checks.

## Workflow
1. Confirm the recovered target metadata matches the module plan target.
2. Confirm the source manifest excludes the original repository.
3. Require numeric metrics and command evidence.
4. For proxy recovery, require mechanism booleans for segmentation, primitive learning, optimizer updates, latent relabeling, and high-level control.
5. Report gap between proxy metric and paper table value without pretending the proxy is full D4RL reproduction.

## Validation
Run:

```bash
python tests/test_recovery_evaluation.py
```

## Limitations
This skill validates evidence structure and OPAL mechanism coverage. It does not replace the Distiller recovery gate.
