---
name: cdc_similarity_loss
description: Compute cross-domain distance consistency softmax-KL losses for few-shot generator adaptation experiments.
---

# Cross-Domain Distance Consistency Loss

Use this skill when implementing or auditing a few-shot generator adaptation run that must preserve the relative relationships learned by a pretrained source generator. The skill is appropriate for full image features, intermediate generator activations, or reduced vector proxies. Do not use it as a target-realism loss by itself; it only checks whether source and adapted samples keep comparable pairwise similarity structure.

## Inputs
- `source_layers`: mapping from layer name to a list of source activation vectors for the same latent batch.
- `adapted_layers`: mapping with identical layer names and vector counts for the adapted generator.
- Optional `temperature` and `eps` values for stable probability and KL calculations.

## Outputs
- Total CDC loss averaged across layers and anchor rows.
- Per-layer KL divergence values.
- Source and adapted row-wise similarity distributions for debugging.

## Workflow
1. For each layer, compute cosine similarities between each anchor vector and every non-self vector in the batch.
2. Convert each anchor row to a probability distribution using a temperature-scaled softmax.
3. Compute KL divergence from the source distribution to the adapted distribution for every anchor row.
4. Average the KL values across layers and rows and save row diagnostics when requested.
5. Treat identical source/adapted activations as a near-zero-loss sanity check.

## Validation
Run `python tests/test_cdc_loss.py` or validate this skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not train a generator, compute LPIPS, or replace discriminator losses. In a reduced recovery it can operate on vectors, but the recovery must explicitly label that execution as proxy evidence.
