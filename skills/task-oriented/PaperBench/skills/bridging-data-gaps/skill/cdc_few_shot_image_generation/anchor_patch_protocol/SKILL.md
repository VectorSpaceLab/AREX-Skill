---
name: anchor_patch_protocol
description: Route latent samples through anchor image realism or patch realism for few-shot adaptation.
---

# Anchor and Patch Realism Protocol

Use this skill when a few-shot image adaptation method needs to distinguish latent samples that should be judged against complete target images from samples that should only receive local patch realism. It implements the protocol from the paper in a deterministic, model-agnostic form suitable for full or reduced experiments.

## Inputs
- Latent vectors sampled for a training step.
- Saved anchor vectors, usually one per few-shot target image.
- A maximum anchor distance or sampling radius.

## Outputs
- One route per latent sample: `image` for anchor-region samples or `patch` otherwise.
- Nearest-anchor distances and indices for auditability.
- Aggregate route counts for validating that both realism pathways are represented.

## Workflow
1. Validate vector dimensionality and require at least one anchor.
2. Compute Euclidean distance from each latent to every saved anchor.
3. Mark a sample as `image` if its nearest distance is at or below the configured threshold.
4. Mark all other samples as `patch` and report route counts.
5. Use route counts in recovery to prove the relaxed realism mechanism executed.

## Validation
Run `python tests/test_anchor_patch.py` or validate this skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not implement a discriminator. It provides the routing contract that a discriminator or proxy realism term must follow.
