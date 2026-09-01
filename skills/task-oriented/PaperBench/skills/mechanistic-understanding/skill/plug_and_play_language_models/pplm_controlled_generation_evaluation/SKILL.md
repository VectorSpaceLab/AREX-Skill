---
name: pplm_controlled_generation_evaluation
description: Evaluate PPLM controlled-generation proxies with target-mass gain, KL fluency cost, and target consistency checks.
---

# PPLM Controlled Generation Evaluation

Use this skill to decide whether a PPLM recovery run improved attribute control while preserving enough fluency. It is useful for full GPT-2 runs and for declared reduced/proxy experiments.

## Inputs
Base probabilities, controlled/fused probabilities, target token indices, and the module-plan recovery target.

## Outputs
Numeric metrics including target mass gain and KL divergence, plus pass/fail status against thresholds.

## Workflow
1. Sum target mass before and after control.
2. Compute absolute target-mass gain.
3. Compute KL from controlled/fused distribution to the base distribution.
4. Pass only when gain meets the target and KL is bounded.

## Validation
Run `python tests/test_controlled_generation_evaluation.py` or Distiller validation.

## Limitations
Human fluency and Perspective-style toxicity scores are outside this deterministic reduced evaluator.
