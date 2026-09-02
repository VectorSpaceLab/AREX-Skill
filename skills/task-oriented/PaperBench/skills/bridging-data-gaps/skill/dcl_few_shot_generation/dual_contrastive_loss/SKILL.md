---
name: dual_contrastive_loss
description: Compute and inspect a DCL-style contrastive proxy loss with same-latent positives and real-target anti-collapse negatives.
---

# Dual Contrastive Loss

Use this skill when a recovery needs a deterministic feature-level version of the paper's DCL objective. It accepts a latent-paired batch and produces an InfoNCE-like scalar loss plus mechanism checks. Do not use it as a replacement for full StyleGAN training when full models are available.

## Inputs
- Batch from `latent_pair_protocol`.
- Temperature scalar.
- Optional real-target negative weight.

## Outputs
- Mean contrastive proxy loss.
- Positive and negative similarity diagnostics.
- Checks showing same-latent positives and real-target negatives were used.

## Workflow
1. Compute dot-product similarity divided by temperature.
2. For each source feature, treat the same-latent target feature as the positive.
3. Treat other generated target features and real-target exemplars as negatives.
4. Average the negative log softmax probability assigned to the positive.

## Validation
Run `python tests/test_dual_contrastive_loss.py` from this skill directory.

## Limitations
The script uses small numeric vectors and standard-library math; it preserves objective structure but not neural feature extraction.


## Refinement Note
A shuffled-positive stress check should produce higher loss than aligned same-latent positives; see `cycle1_shuffled_stress.json` in recovery logs.
