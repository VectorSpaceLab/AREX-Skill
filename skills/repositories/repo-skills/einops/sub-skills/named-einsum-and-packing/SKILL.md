---
name: named-einsum-and-packing
description: "Use einops.einsum, pack, and unpack for named-axis contractions
  and reversible heterogeneous tensor packing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Named Einsum And Packing

Use this sub-skill when the task needs named-axis tensor contractions or
reversible packing of tensors with heterogeneous middle structure. It covers
`einops.einsum`, `einops.pack`, and `einops.unpack` as public runtime APIs.

## Load When

- Translating NumPy/backend einsum formulas into readable named-axis patterns.
- Computing attention scores, dot products, linear projections, traces, diagonal
  reductions, or ellipsis-aware contractions.
- Packing class tokens, image tokens, text tokens, or other modalities into one
  sequence-like tensor and unpacking the processed result.
- Carrying packed-shape bookkeeping (`PS`) through transformer/model flows.
- Splitting one prediction tensor into multiple logical outputs with manual
  `packed_shapes`.
- Debugging failures involving `->`, tensors-first call order, unsupported
  grouped einsum axes, invalid `*` packing patterns, bad `packed_shapes`, or
  `-1` inference.

## Route Elsewhere

- Ordinary reshape, transpose, split, stack, reduce, repeat, pooling, or
  dimension parsing recipes belong to sibling sub-skill `tensor-operations`.
- Framework layer abstractions such as `EinMix` and `einops.layers.*` belong to
  sibling sub-skill `framework-integrations`.
- Repository development commands, native test selection, packaging, docs
  builds, or source maintenance belong to sibling sub-skill `repo-development`.

## Public APIs

```python
from einops import einsum, pack, unpack
```

- `einsum(*tensors_and_pattern)` takes one or more tensors first and the pattern
  string last. This is the reverse of `numpy.einsum(pattern, *tensors)`.
- `pack(tensors, pattern)` returns `(packed_tensor, packed_shapes)`.
- `unpack(tensor, packed_shapes, pattern)` returns a list of tensors.

See [references/api-reference.md](references/api-reference.md) for signatures,
parameters, return contracts, limitations, and error behavior.

## Golden Rules

1. Always call `einsum` as `einsum(tensor1, tensor2, ..., "axes -> axes")`.
   A non-string last argument is a call-order bug.
2. Always include an explicit `->` in `einsum`; implicit-output NumPy-style
   shorthand is intentionally rejected.
3. Use semantic multi-letter axis names such as `batch`, `query`, `head`, and
   `channel`. Internally they are compacted to backend single-letter einsum
   symbols, but user code should stay named and readable.
4. `einsum` supports ellipsis and repeated axes on an input term for diagonal or
   trace-style operations. It does not support grouped axes like `(h w)`,
   singleton `()`, or anonymous numeric axes like `2`.
5. Use `pack`/`unpack`, not manual concatenate/slice/reshape, when tensors have
   heterogeneous axes in the packed position or when the inverse split must be
   carried safely through later code.
6. A packing pattern is not an arrow expression. It is a space-separated list of
   axes with exactly one literal `*`, for example `"batch * channel"`.
7. Keep `packed_shapes` (`PS`) next to the packed tensor. Treat it as part of the
   data contract, especially across model calls that change only non-packed axes
   such as `channel -> channel_out`.
8. In manual `unpack`, use at most one `-1` across the entire `packed_shapes`
   argument, and validate round trips when shapes are computed dynamically.
9. Zero-length packed items are valid and should usually be preserved through
   `PS` instead of special-cased away.

## Pattern Quick Reference

### Named einsum

```python
scores = einsum(
    queries, keys,
    "batch query head channel, batch key head channel -> batch head query key",
)
```

- Axes absent from the right side are summed over.
- Axes repeated within one input term select diagonals before summation.
- Ellipsis (`...`) carries arbitrary leading, middle, or trailing dimensions.

### Packing and unpacking

```python
packed, ps = pack([class_token_bc, image_tokens_bhwc, text_tokens_btc], "batch * channel")
class_out, image_out, text_out = unpack(processed_packed, ps, "batch * channel_out")
```

- Axes before `*` match leading axes of every input.
- Axes after `*` match trailing axes of every input.
- Every remaining input axis is flattened into the packed axis, concatenated,
  and recorded in the corresponding `PS` entry.
- `PS` entries are shapes that replace `*` during `unpack`; `()` means the item
  contributed one element with no explicit packed axes.

## Workflow References

Use [references/workflows.md](references/workflows.md) for these recipes:

- Convert backend/NumPy attention or dot-product formulas to named `einsum`.
- Catch unsupported grouped-axis einsum and repair it with a separate reshape
  step owned by `tensor-operations`.
- Pack class tokens and patch tokens for ViT-like flows.
- Pack multimodal token streams, including zero-length modalities.
- Split multi-output prediction tensors with manual `packed_shapes`.
- Auto-batch single examples and batches with `pack([x], "* ...")` style flows.
- Validate reversible pack/unpack round trips and `PS` bookkeeping.

Use [references/troubleshooting.md](references/troubleshooting.md) for the
failure matrix and fixes for common error fragments.

## Bundled Smoke Scripts

The scripts are deterministic, NumPy-only checks derived from public behavior
covered by the repository tests and examples. They do not import repo tests or
require a source checkout.

- [`scripts/einsum_smoke.py`](scripts/einsum_smoke.py) checks named einsum,
  attention, ellipsis, traces, and expected unsupported-syntax errors.
- [`scripts/packing_smoke.py`](scripts/packing_smoke.py) checks trivial packing,
  heterogeneous round trips, class-token and multimodal flows, multi-output
  unpacking, auto-batching, zero-length cases, and expected packing errors.

Run from the sub-skill directory or pass the script path explicitly:

```bash
python scripts/einsum_smoke.py --help
python scripts/einsum_smoke.py
python scripts/packing_smoke.py --help
python scripts/packing_smoke.py
```

## Recovery Checklist

When a user reports a broken named-axis contraction or packing flow:

1. Identify whether the operation is a contraction (`einsum`) or reversible
   shape bookkeeping (`pack`/`unpack`). Do not solve a packing problem with a
   lossy manual slice unless reversibility is irrelevant.
2. Check API call order first: tensors before pattern for `einsum`; sequence of
   tensors before pattern for `pack`; packed tensor, `PS`, then pattern for
   `unpack`.
3. Validate pattern family: arrow pattern for `einsum`, one-star no-arrow
   pattern for `pack`/`unpack`.
4. For `einsum`, remove unsupported groups, singletons, and anonymous axes by
   doing explicit reshapes or singleton insertion outside `einsum`.
5. For `pack`/`unpack`, inspect the `PS` entries and the product they imply for
   the packed axis; then run a minimal round-trip assertion.
6. Reproduce with the bundled smoke script case nearest to the failure, then
   adapt its small deterministic arrays to the user's shapes.
