---
name: reduced_recovery_harness
description: Run a bounded mechanism-faithful proxy experiment for probabilistic bilevel coreset selection with executable evidence.
---

# Reduced Recovery Harness

Use this skill when full MNIST or CIFAR neural coreset reproduction is blocked by time, package, or dataset constraints, and the run mode permits reduced recovery. It creates a deterministic noisy and imbalanced classification task, exercises the generated probabilistic coreset modules, and records validation-loss improvement over a uniform coreset baseline.

Do not use this skill to claim full paper reproduction. It is a soft-mode proxy that must be labeled as reduced/proxy evidence and accompanied by mechanism checks.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing mask relaxation, projection, and policy update scripts.
- Optional output paths for recovery artifacts.

## Outputs
- `recovery/recovery_result.json` with numeric proxy metric.
- `recovery/logs/generated_data_item.json` describing the synthetic noisy/imbalanced task.
- `recovery/logs/training_trace.json` with loss and parameter changes.
- Generated-skill invocation evidence for every core module.

## Workflow
1. Load the declared recovery target from `module_plan.json`.
2. Generate a deterministic imbalanced binary dataset with controlled label noise.
3. Train a tiny logistic model on uniform coreset samples for baseline validation loss.
4. Run repeated Bernoulli mask sampling, inner logistic training, outer validation scoring, policy-gradient probability updates, and capped projection.
5. Save metrics and mechanism checks showing reduced training and optimizer updates occurred.

## Validation
Run the recovery script from the attempt directory and then run `validate_recovery_experiment.py`. Skill tests invoke the harness on a temporary directory and assert a numeric metric and required mechanism checks.

## Limitations
The harness uses a small synthetic dataset and a tiny student model. It validates the algorithmic mechanism, not the paper's full-scale image classification numbers.
