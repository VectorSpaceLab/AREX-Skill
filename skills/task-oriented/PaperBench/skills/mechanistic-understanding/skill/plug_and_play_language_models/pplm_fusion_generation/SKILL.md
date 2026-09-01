---
name: pplm_fusion_generation
description: Fuse PPLM perturbed and unperturbed token distributions using geometric mixing for fluent controlled decoding.
---

# PPLM Perturbed Distribution Fusion

Use this skill after an attribute perturbation has produced controlled logits and the run needs to combine them with the unperturbed language-model distribution.

## Inputs
Base logits or probabilities, perturbed logits or probabilities, `gm_scale` in `[0,1]`, and a deterministic selection mode.

## Outputs
A normalized fused distribution, selected token index, entropy, and endpoint diagnostics.

## Workflow
1. Convert logits to probabilities when needed.
2. Compute geometric mixture `base^(1-gm_scale) * perturbed^gm_scale`.
3. Normalize the fused probabilities.
4. Select the argmax token for deterministic recovery tests.

## Validation
Run `python tests/test_fusion_generation.py` or Distiller validation.

## Limitations
This skill validates the fusion rule and does not implement full top-k or nucleus sampling.
