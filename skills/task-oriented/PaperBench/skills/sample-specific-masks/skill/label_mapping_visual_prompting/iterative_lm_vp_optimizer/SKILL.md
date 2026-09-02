---
name: iterative_lm_vp_optimizer
description: Run reduced or full ILM-VP alternating label-remapping and prompt-optimization loops.
---

# Iterative LM-VP Optimizer

Use this skill when implementing the paper's core ILM-VP mechanism: recompute label mapping under the current prompt, then update only prompt parameters against mapped source labels. Do not use it as evidence for full recovery unless the source model and dataset are real and recorded.

## Inputs
- Target examples and target labels.
- Frozen source model or source-logit surrogate.
- Initial prompt, learning rate, epoch count.
- Frequency-label-mapping helper.

## Outputs
- Final prompt.
- Mapping history.
- Loss and accuracy trace.
- Mechanism checks indicating remapping and optimizer execution.

## Workflow
1. Initialize prompt parameters.
2. For each epoch, predict source labels with the current prompt.
3. Recompute target-to-source mapping from class-wise source predictions.
4. Evaluate mapped-source cross-entropy or a deterministic proxy loss.
5. Update only the prompt.
6. Log whether mapping changed and whether parameters changed.

## Validation
Run `python tests/test_iterative_lm_vp.py` or `validate_skill_tree.py --run-tests`.

## Limitations
The included script is a tiny deterministic proxy for bounded recovery. Full image VP should replace the source surrogate with an actual frozen vision model.
