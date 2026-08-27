---
name: tensor-operations
description: "Core einops tensor operations for rearrange, reduce, repeat,
  parse_shape, asnumpy, shape recipes, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tensor Operations

Use this sub-skill when a task asks for everyday tensor shape work with
`einops.rearrange`, `einops.reduce`, `einops.repeat`, `einops.parse_shape`, or
`einops.asnumpy`: readable replacements for reshape/view/permute/transpose,
shape-checked refactors, pooling/reduction, broadcasting/repetition, stack or
concatenate from lists, ellipsis patterns, and pattern debugging.

## Route Boundaries

Stay here for:

- Core imperative APIs: `rearrange`, `reduce`, `repeat`, `parse_shape`, and
  `asnumpy`.
- Pattern syntax for named axes, composed axes like `(c h w)`, decomposed axes
  like `(h h2)`, singleton axes `1`/`()`, anonymous numeric axes in allowed
  contexts, and ellipsis `...`.
- Built-in reductions: `min`, `max`, `sum`, `mean`, `prod`, `any`, `all`, plus
  callable reductions with signature `f(tensor, axes_tuple) -> tensor`.
- NumPy-style, PyTorch-style, JAX-style, TensorFlow-style, and other supported
  tensor objects when using the same core functions.
- Shape mismatch diagnosis and recovery for the core pattern language.

Route elsewhere:

- Named-axis `einsum`, `pack`, and `unpack`: use
  [`named-einsum-and-packing`](../named-einsum-and-packing/SKILL.md).
- Framework layers, backend-specific layer modules, `EinMix`, compilation, and
  deep framework integration: use
  [`framework-integrations`](../framework-integrations/SKILL.md).
- Repository tests, docs builds, CI, packaging, or maintainer workflows: use
  [`repo-development`](../repo-development/SKILL.md).

## Quick Operating Model

1. Import the needed functions:

   ```python
   from einops import rearrange, reduce, repeat, parse_shape, asnumpy
   ```

2. Write patterns as `"left axes -> right axes"`.
   - Axis names describe semantic dimensions, not implementation steps.
   - Parentheses compose/decompose axes: `b c h w -> b (c h w)` or
     `b (patch c) h w -> patch b c h w`.
   - Axis composition uses C-order semantics: in `(a b)`, neighboring linear
     positions differ first in the rightmost axis `b`.
   - Axes present only on the left are reduced by `reduce`.
   - New axes appear only in `repeat` or as singleton `1`/`()` axes.

3. Supply `axes_lengths` whenever einops cannot infer a factor or must check a
   contract:

   ```python
   y = rearrange(x, "b c (h h2) (w w2) -> b h w (c h2 w2)", h2=2, w2=2)
   ```

4. Preserve original shape facts with `parse_shape` when undoing a flatten or
   refactoring code that previously relied on comments:

   ```python
   shape = parse_shape(x, "b c h w")
   flat = rearrange(x, "b c h w -> (b h w) c")
   restored = rearrange(flat, "(b h w) c -> b c h w", **shape)
   ```

5. Validate with explicit shapes and a tiny data check before replacing a
   framework-native snippet. For copyable assertions, run the bundled smoke
   script below.

## Reference Map

- [`references/api-reference.md`](references/api-reference.md): verified
  signatures, return behavior, pattern grammar, reduction names, callable
  reductions, `parse_shape`, `asnumpy`, and API boundaries.
- [`references/pattern-recipes.md`](references/pattern-recipes.md): copyable
  recipes for flatten/unflatten, pooling, stack/concat, space-depth transforms,
  image/video conventions, ellipsis, and reduce/repeat interplay.
- [`references/troubleshooting.md`](references/troubleshooting.md): symptom →
  cause → recovery guidance for common einops errors and pattern pitfalls.
- [`scripts/shape_recipe_smoke.py`](scripts/shape_recipe_smoke.py): deterministic
  NumPy smoke script adapted from public example/test recipes; runs core shape
  recipes and assertion-backed failure checks.

## Common Task Patterns

### Replace reshape/permute/view with a readable pattern

```python
# NCHW -> NHWC
x_nhwc = rearrange(x_nchw, "b c h w -> b h w c")

# Per-example flatten with explicit semantic axes
features = rearrange(x_nchw, "b c h w -> b (c h w)")
```

Add fixed lengths when the refactor is meant to assert an interface:

```python
features = rearrange(x, "b c h w -> b (c h w)", c=256, h=19, w=19)
```

### Pool or normalize without framework-specific pooling code

```python
pooled = reduce(x, "b c (h h2) (w w2) -> b c h w", "max", h2=2, w2=2)
centered = x - reduce(x, "b c h w -> b c 1 1", "mean")
```

For integer tensors, avoid `"mean"` until the tensor is floating-point; see the
troubleshooting reference.

### Repeat or broadcast explicit axes

```python
rgb = repeat(gray, "h w -> h w c", c=3)
upsampled = repeat(lowres, "b h w c -> b (h h2) (w w2) c", h2=2, w2=2)
```

Every named axis introduced by `repeat` must have a supplied size or be written
as an anonymous numeric axis such as `5`.

### Stack or concatenate list inputs

```python
stacked = rearrange(list_of_images, "b h w c -> b c h w")
wide_strip = rearrange(list_of_images, "b h w c -> h (b w) c")
```

A list input is stacked on a new zeroth axis before the pattern is interpreted;
name that axis explicitly (`b` above).

### Use ellipsis for shape-polymorphic middle dimensions

```python
moved = rearrange(x, "batch ... channels -> batch channels ...")
summary = reduce(x, "batch ... channels -> batch channels", "mean")
repeated = repeat(x, "... channels -> ... channels copies", copies=4)
```

Use ellipsis when the rank between known outer axes can vary. Do not place
ellipsis inside parentheses on the left side.

## Minimal Validation Loop

For any nontrivial transformation:

1. Write a one-line shape expectation beside the operation.
2. If decomposing axes, assert divisibility before calling einops when the
   recovery path is user-facing.
3. Compare one or two sentinel values after rearrangement to confirm axis order.
4. For refactors, run:

   ```bash
   python sub-skills/tensor-operations/scripts/shape_recipe_smoke.py --case all
   ```

   from any directory after installing `einops` and `numpy`.

## Evidence Summary

This sub-skill distills public evidence from `README.md`, `einops/einops.py`,
`einops/parsing.py`, `einops/tests/test_ops.py`,
`einops/tests/test_examples.py`, `einops/tests/test_other.py`, and the headings
and example patterns from `docs/1-einops-basics.ipynb` and
`docs/2-einops-for-deep-learning.ipynb`. Installed package inspection verified
core function availability and signatures for the 0.9.0 development runtime.
