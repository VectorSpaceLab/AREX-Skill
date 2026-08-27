---
name: "core-models"
description: "Base text and vision transformer constructors, attention flags,
  positional families, normalization and residual variants, pooling, and
  shape/mask sanity checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Core Models

Use this sub-skill when the task is to choose, instantiate, or inspect the base x-transformers model stack rather than a task wrapper or training recipe.

## Use this route for

- `TransformerWrapper`, `XTransformer`, `ViTransformerWrapper`, `Encoder`, `Decoder`, `PrefixDecoder`, `CrossAttender`, `AttentionPool`, `TransformerBlock`, `Attention`, and `AttentionLayers`.
- Text and vision model construction, including memory tokens, register tokens, class tokens, pooling, and prepended embeddings.
- Attention-kernel choices, positional families, normalization variants, and residual variants.
- Shape and mask sanity checks for constructor-level debugging.

## Do not use this route for

- `AutoregressiveWrapper`, `Continuous*`, `XVal*`, `XLAutoregressiveWrapper`, `BeliefStateWrapper`, `NextLatentWrapper`, `DPO`, `FreeTransformer`, `GPTVAE`, `NeoMLP`, `EntropyBasedTokenizer`, `XMLatentDecoder`, or `train_*.py` recipes. Use the sibling [sequence-workflows](../sequence-workflows/SKILL.md) or [training-recipes](../training-recipes/SKILL.md) sub-skills instead.
- Import/export or publication tasks.

## Read first

- [Feature compatibility](references/feature-compatibility.md)
- [Troubleshooting](references/troubleshooting.md)

## Quick constructor map

- `TransformerWrapper + Decoder`: decoder-only text, memories, pooled embeddings, and generation.
- `TransformerWrapper + Encoder`: bidirectional text / masked modeling.
- `XTransformer`: encoder-decoder text with cross attention.
- `ViTransformerWrapper`: image patches to logits or embeddings.
- `PrefixDecoder`: prefix-LM masking.
- `CrossAttender`: pure cross attention.
- `AttentionPool`: query pooling over a context sequence.
- `TransformerBlock`: generic stack helper when you want `AttentionLayers` directly.

## Operating checklist

1. Match the input rank first: token ids for wrappers, `(b, n, d)` for attention modules.
2. Pick only one positional-bias family at a time unless the reference says otherwise.
3. Keep `pre_norm=True` if you enable `sandwich_norm`.
4. Pass `context` whenever `cross_attend=True` or you instantiate a cross-attention-only stack.
5. Treat flash attention as the highest-risk path: if a feature needs the raw attention matrix, disable flash and retry.
6. Use the references for exact shape, mask, and compatibility rules before writing code.
