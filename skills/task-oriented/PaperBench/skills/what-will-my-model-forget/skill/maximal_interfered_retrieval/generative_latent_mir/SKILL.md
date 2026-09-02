---
name: generative_latent_mir
description: Score latent replay candidates with KL drift, entropy confidence penalties, and diversity filtering for MIR.
---

# Generative and Latent MIR

Use this skill when MIR must operate over generated samples, compressed memories, or a deterministic latent proxy rather than raw replay examples. It captures the paper's generative MIR mechanism without requiring a VAE for small validation tests.

## Inputs
- Latent candidate ids and vectors.
- Pre-update and virtual-update class probability distributions for each candidate.
- Entropy weight, diversity distance threshold, and replay budget.
- Optional nearest-neighbor mapping from latent points to stored compressed examples.

## Outputs
- KL, entropy, and combined score per candidate.
- A diversity-filtered ranked selection.
- Mechanism diagnostics showing KL drift and entropy confidence were evaluated.

## Workflow
1. Normalize candidate probability vectors with small numerical smoothing.
2. Compute `KL(y_pre || y_hat)` for prediction drift after the virtual classifier update.
3. Compute entropy of `y_pre` and subtract `entropy_weight * entropy`.
4. Sort candidates by descending score.
5. Apply greedy diversity filtering by Euclidean distance in latent space.
6. Return selected candidates and diagnostics for recovery logging.

## Validation
Run the included tests or `validate_skill_tree.py --run-tests`. Tests cover KL ranking, entropy penalties, smoothing, and diversity filtering using standard-library numeric fixtures.

## Limitations
This helper validates the latent MIR objective and selection contract. It does not train an encoder, decoder, or VAE; a full neural implementation should provide probability vectors and latent candidates from the model stack while preserving the same output schema.

Validation note: the diversity smoke test intentionally verifies that near-duplicate latent candidates can be suppressed while a distant interfered candidate remains selected.
