---
name: proxy_recovery_harness
description: Run a bounded mechanism-faithful proxy experiment for maximum softmax OOD detection recovery artifacts.
---

# Mechanism-Faithful Proxy Recovery Harness

Use this skill when full classifier training and full OOD datasets are unavailable but soft-mode recovery permits a declared proxy. The harness must still execute the paper mechanism: construct classifier-output rows, compute maximum softmax probabilities, and evaluate AUROC/AUPR in the paper orientation.

## Inputs
- Attempt directory path.
- Generated skills root containing `softmax_confidence_scoring` and `detection_metric_protocol`.
- Module-plan target metadata.

## Outputs
- `recovery/recovery_result.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json` for reduced optimizer evidence when no real training stack is available.
- Skill invocation log and command log entries.

## Workflow
1. Declare the run as proxy/reduced when real datasets and training are blocked.
2. Build a deterministic logits fixture with peaked in-distribution rows and flatter OOD rows.
3. Invoke the MSP scoring skill to compute per-row maximum probabilities.
4. Invoke the metric skill for in-positive scores and out-positive negative scores.
5. Record mechanism checks, including MSP execution, correct score orientation, AUROC/AUPR computation, source-boundary compliance, and reduced-training status.

## Validation
Run the recovery command, then run `validate_recovery_experiment.py` on the attempt directory.

## Limitations
This is not full paper reproduction. It is acceptable only under soft recovery mode after recording why full-scale datasets/training are blocked.
