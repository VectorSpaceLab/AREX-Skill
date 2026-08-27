---
name: api-variants
description: "Select and interoperate among h3-py's string, integer, memoryview,
  and optional NumPy APIs while preserving H3 index meaning and collection
  contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# API variants

Use this route when a task mentions H3 string or integer indices, NumPy arrays,
`memoryview`, API parity, `int_to_str`, `str_to_int`, conversion, memory,
performance, or optional NumPy installation. The four public variants expose the
same public function names and signatures, but change scalar and collection
representations:

- `import h3` is the default `h3.api.basic_str` interface.
- `h3.api.basic_int` uses Python integers and ordinary Python collections.
- `h3.api.memview_int` uses Python integers and typed `uint64` buffer outputs;
  it has no NumPy dependency.
- `h3.api.numpy_int` uses Python integers for scalar results and NumPy
  `ndarray` collections with `uint64` dtype; NumPy is optional.

## Route the task

1. Keep strings at the application boundary when logs, JSON, config files, or
   human review are primary: use `h3`/`h3.api.basic_str`.
2. Keep integer scalars and ordinary Python iteration when the consumer already
   uses integer H3 values but does not need a buffer: use `basic_int`.
3. Use `memview_int` for dependency-free typed-buffer exchange. Supply a
   `uint64` buffer, not a list or set, and preserve the returned view's lifetime.
4. Use `numpy_int` when downstream code already consumes NumPy arrays or needs
   vectorized array handling. Install the optional NumPy extra first.
5. For a mixed pipeline, compute in an integer/buffer variant and normalize once
   at the boundary. Measure the actual workload before making performance claims;
   documentation timing examples are illustrative, not universal.

Read [the root router](../../SKILL.md) for overall H3 routing. For geographic
indexing algorithms, use [core-indexing](../core-indexing/SKILL.md); for polygon
and shape workflows, use [polygon-geospatial](../polygon-geospatial/SKILL.md).

## Operating rules

- Treat an H3 string as a hexadecimal representation without assuming a `0x`
  prefix. `str_to_int` and `int_to_str` are the explicit conversion boundary.
- Do not mix a string scalar into an integer API or an integer scalar into the
  string API without converting it first.
- Normalize collections element by element when crossing APIs. Do not compare a
  string collection directly with an integer or NumPy collection.
- Preserve collection semantics separately from representation: choose whether
  order and duplicates matter, then use a list, set, or sorted canonical list
  deliberately. API output types are not a substitute for domain semantics.
- Treat NumPy and memoryview outputs as unsigned 64-bit H3 values. Validate
  ranges before constructing buffers; do not use signed buffers for
  `memview_int`.
- `np.asarray(view)` can share the memoryview's storage, whereas `np.array(view)`
  makes an independent copy. Choose deliberately before mutating or retaining a
  result.
- The public API surface is shared across variants, with representation-specific
  exceptions documented in [the reference](references/api-reference.md).

## Common actions

- Compare or serialize outputs: normalize to strings with
  `int_to_str`/`str_to_int` as described in [workflows](references/workflows.md).
- Accept user-facing indices: validate the scalar type and convert at the
  boundary; see [troubleshooting](references/troubleshooting.md) for invalid
  hex, overflow, and collection errors.
- Diagnose an installation or representation issue: run
  `python scripts/check_api_variants.py`. It reports available variants,
  scalar/collection types, NumPy dtype, and a tiny parity check without running
  a geospatial benchmark.

## Handoff checklist

Before handing a result to another component, record:

1. Which API module owns each scalar and collection value.
2. Whether collection order, duplicates, or set semantics are significant.
3. Whether the consumer requires a copied snapshot or may share a buffer.
4. Whether NumPy is a required dependency or only an optional fast path.
5. Which conversion boundary turns values back into the consumer's contract.

When an API boundary is part of a public function, document the accepted scalar
and collection representation rather than relying on a module import name. For
reproducibility, include the package version and the diagnostic output, but keep
those task artifacts outside this runtime skill tree.

If a caller can select more than one variant, expose the choice as an explicit
configuration value and test both the selected representation and the normalized
semantic result. Do not switch variants implicitly because an optional import
happens to be present. A missing optional dependency should produce a clear
fallback or a clear installation error, depending on the caller's contract.

## Deliberate non-coverage

This route does not teach cell geometry, hierarchy, grid algorithms, edge/vertex
algorithms, or polygon construction. Follow the sibling routes above for those
operations, then return here only for representation conversion or interop.

Keep this route focused on public Python behavior and observable contracts.
