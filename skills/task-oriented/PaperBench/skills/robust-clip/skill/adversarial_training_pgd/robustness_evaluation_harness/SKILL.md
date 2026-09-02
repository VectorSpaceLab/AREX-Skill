---
name: robustness_evaluation_harness
description: Evaluate natural and PGD adversarial metrics and emit validator-compatible recovery evidence for robust optimization experiments.
---

# Robustness Evaluation Harness

## When To Use
Use this skill after a model has been trained or updated and needs natural plus white-box PGD adversarial evaluation. It is especially useful for reduced recovery where artifacts must prove that the proxy exercised the paper mechanism.

Do not use natural accuracy alone as evidence of robustness.

## Inputs
- Model parameters.
- Evaluation examples and labels.
- PGD attack configuration.
- `module_plan.json.fast_recovery_target` metadata.
- Optional before/after training trace.

## Outputs
- Natural loss and accuracy.
- PGD adversarial loss and accuracy.
- Metric gap or loss-reduction value.
- Mechanism checks and recovery-result-ready JSON.

## Workflow
1. Evaluate natural metrics on clean examples.
2. Generate PGD adversarial examples using the attack skill.
3. Evaluate adversarial metrics on the generated examples.
4. Compare before/after PGD losses for reduced training recovery.
5. Preserve target metadata exactly from the module plan.

## Validation
Run:

```bash
python scripts/evaluate_robustness.py --self-test
python tests/test_evaluate_robustness.py
```

## Limitations
This harness measures the provided model and attack settings. Full robustness claims require stronger datasets, larger models, and multiple attacks as in the paper.
