# Compatibility overview

This page summarizes the highest-value compatibility rules for the package. For the full constructor matrix, see `sub-skills/core-models/references/feature-compatibility.md`.

## Flash-attention path

- Optional packed-sequence and flash-attention paths require compatible CUDA hardware and the optional `flash-attn` package.
- Treat flash attention as unsafe whenever a feature needs the raw attention matrix.
- The main rejection patterns are flash with residual attention, flash with T5-style relative positional bias, flash with dynamic positional bias, and flash with CoPE.

## Positional families

- Choose only one of T5 relative bias, dynamic positional bias, or ALiBi for a given stack.
- Rotary and polar positional embeddings are mutually exclusive.
- Rotary-XPos is not the same as plain rotary, and it is not intended for bidirectional encoder stacks.

## Pooling and wrapper exclusives

- Choose one pooling route at a time: average pooling, class token, or attention pool.
- `cross_attend=True` needs a `context` tensor.
- `pre_norm=False` conflicts with sandwich norm.

## Sequence-workflow shape rules

- Token wrappers usually want `[batch, seq]`.
- Continuous wrappers usually want `[batch, seq, dim]`.
- xVal wrappers need matched token and number tensor shapes.
- XL and latent wrappers often need longer sequences or matching module shapes for memory and TTT-style flows.

## Recipe compatibility

- The enwik8 scripts expect a local `data/enwik8.gz` file.
- Several recipes import extras such as Accelerate, Fire, W&B, tqdm, and optional optimizer/helper packages.
- Many recipe scripts are long-running and initialize training at module scope; use the bundled smoke before trying them directly.
