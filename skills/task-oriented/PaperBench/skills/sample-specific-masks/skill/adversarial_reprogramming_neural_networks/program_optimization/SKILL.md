---
name: program_optimization
description: Optimize only universal program parameters through a frozen model for adversarial reprogramming recovery experiments.
---

# Frozen-Model Program Optimization

Use this skill when testing whether a fixed model can be repurposed by training an input program. The target model must remain frozen; only the program parameters may change. This is not ordinary fine-tuning.

## Inputs
- Synthetic or real task examples and labels.
- A frozen target model or reduced differentiable proxy.
- Input programming and output remapping functions.
- Learning rate and step count.

## Outputs
- Updated program parameters.
- Training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and accuracy.
- Mechanism booleans showing universal program reuse, frozen model unchanged, remapping use, and optimizer execution.

## Workflow
1. Build programmed inputs for all examples using one shared program.
2. Evaluate the frozen target and output remapper.
3. Compute a classification loss.
4. Update only the program.
5. Log parameter and loss changes.

## Validation
Run `python tests/test_program_optimization.py`.

## Limitations
The included script is a standard-library reduced proxy for bounded recovery. Full ImageNet recovery should replace the proxy model with the available frozen classifier while preserving the same contract.
