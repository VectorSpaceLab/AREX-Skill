---
name: latent_pair_protocol
description: Validate DCL latent-paired source/target feature batches and separate real-target negatives for few-shot GAN adaptation recovery.
---

# Latent Pair Protocol

Use this skill when a recovery experiment must construct or validate a DCL-style batch. It is appropriate for reduced feature-level experiments and for checking that source and target generated samples share latent identifiers. Do not use it to compute the contrastive loss or evaluation metric.

## Inputs
- Source generated feature records with `latent_id` and numeric `features`.
- Target generated feature records with matching `latent_id` and numeric `features`.
- Few real target exemplar feature records.

## Outputs
- A JSON-compatible batch with ordered latent pairs.
- Separate generated negatives and real-target negatives.
- Validation errors for missing or duplicated latent ids.

## Workflow
1. Normalize feature records into lists of floats.
2. Require exactly one source and one target record per latent id.
3. Build positives from same-latent source/target records.
4. Keep real-target exemplars separate so later DCL loss code can apply anti-collapse negatives.

## Validation
Run `python tests/test_latent_pair_protocol.py` from this skill directory.

## Limitations
This skill validates feature-level protocol semantics only; it does not implement StyleGAN, discriminator features, FID, or LPIPS.


## Refinement Note
Recovery now includes an edge-case check that mismatched source/target latent ids are rejected before loss computation.
