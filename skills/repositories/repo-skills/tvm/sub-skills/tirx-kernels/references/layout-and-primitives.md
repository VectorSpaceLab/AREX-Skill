# Layout and Tile Primitive Notes

## Layout model

`TileLayout` describes how logical tile elements map across memory and thread
axes. Common combinators and axis names include:

- `S[...]`: shard portion of a tile layout.
- `R[...]`: replicated portion.
- `+ offset @ axis`: offset contribution along an axis.
- Thread-like axes: `laneid`, `warpid`, `wgid`, `tid_in_wg`, `wid_in_wg`, and
  target-specific block/thread axes.
- Memory-like axes: `m`, `P`, `F`, `TCol`, `TLane`.

A typical workflow is:

```python
from tvm.tirx.layout import TileLayout, S, R, laneid

layout = TileLayout(S[8 : 4 @ laneid] + R[4 : 1 @ laneid])
layout = layout.canonicalize()
assert layout.verify_well_formed()
```

Use structural equality or canonical string forms rather than object identity
when comparing layouts.

## ComposeLayout and swizzles

`ComposeLayout(per_element, swizzle_len, atom_len, tile_layout,
swizzle_inner=True)` represents a swizzled layout composed over a tile layout.
Treat bare swizzle concepts as composition over a trivial or explicit tile
layout. Check `per_element`, `swizzle_len`, and `atom_len` against the memory
scope and primitive requirements.

## Primitive dispatch

Tile primitives use specialized dispatch rules tied to:

- target backend and architecture,
- execution scope,
- input/output layouts,
- dtype and shape,
- memory space and swizzle/TMEM constraints,
- whether the primitive is run inside the expected device function context.

When dispatch fails, do not immediately rewrite the whole kernel. Instead:

1. Print the primitive call and inferred layout facts.
2. Verify each participating layout independently.
3. Confirm the target architecture supports the primitive.
4. Reduce to a single primitive invocation.
5. Compare the expected scope/dtype/shape contract to the actual arguments.

## Debug signals

| Symptom | Likely source | First check |
|---|---|---|
| Parser error around `T.` syntax | TVMScript dialect mismatch | Confirm `from tvm.script import tirx as T` and minimal function syntax |
| Layout not well formed | Axis/scope/offset inconsistency | Run `tirx_layout_probe.py` and canonicalize the layout |
| Scope disconnected or unexpected | Thread/memory axes mixed incorrectly | Inspect `layout.get_scope()` and axis names |
| Primitive dispatch rejects call | Target/layout/dtype/scope mismatch | Reduce to one primitive and verify target/backend support |
| Codegen succeeds but execution fails | Runtime backend/device mismatch | Check CUDA/device availability and module target |

## Script probe

`tirx_layout_probe.py` creates several portable layouts, canonicalizes them, and
checks well-formedness. It is intentionally not a GPU kernel runner.
