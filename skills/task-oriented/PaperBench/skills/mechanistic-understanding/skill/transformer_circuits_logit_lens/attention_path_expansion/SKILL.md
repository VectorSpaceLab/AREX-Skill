---
name: attention_path_expansion
description: Compute frozen-attention direct, head, and virtual-head path contributions for attention-only circuits.
---

# Attention Path Expansion

Use this skill when you have fixed or frozen attention patterns and want to decompose attention-only logits into additive circuit paths. It is suited for toy transformers, ablations, and mechanism checks inspired by Transformer Circuits. Do not use it for full transformers with changing layer normalization or MLP paths unless those parts are explicitly separated.

## Inputs

- Token ids and an embedding matrix.
- Unembedding matrix.
- One or more attention patterns shaped destination-position by source-position.
- Matching OV matrices shaped model-by-model.

## Outputs

- Direct residual-to-logit contribution.
- First-order per-head contributions.
- Optional virtual-head contribution for a two-head sequence.
- Maximum consistency error against explicit frozen-attention forward computation.

## Workflow

1. Embed tokens into residual states.
2. Compute direct logits through the unembedding.
3. Apply each head as `attention @ residual @ OV` and unembed the result.
4. For two sequential heads, compute the virtual contribution `A2 @ A1 @ residual @ OV1 @ OV2`.
5. Compare the expanded sum with an explicit sequential frozen-attention forward pass.

## Validation

Run the deterministic tests or validate with the module-to-skill tree validator.

## Limitations

The script implements the paper's simplified attention-only setting with supplied attention patterns. It intentionally does not implement softmax QK score construction.
