# Reversible coupling and wrapper contracts

Reversible layers are a memory-saving construction, not a different graph
layout. Start with a correct ordinary sparse block, then introduce coupling
and checkpointing.

## GroupAdditiveCoupling

`GroupAdditiveCoupling(Fms, split_dim=-1, group=2)` requires:

- `len(Fms) == group` and every function has a `forward` method compatible
  with `Fm(chunk, edge_index, *extra_chunked_args)`.
- The feature width along `split_dim` is divisible by `group`. For node
  features `(N,C)`, the default `-1` splits channels; use an explicit channel
  dimension if the calling tensor layout makes that clearer.
- Each `Fm` maps the group width back to the same group width. The additive
  update is sequential: let `y_in = sum(x_chunks[1:])`; for each group,
  `y_i = x_i + Fm_i(y_in, edge_index, ...)`, then set `y_in = y_i`.
  The output concatenates all `y_i` in group order.
- Every extra positional argument after `edge_index` is chunked along the same
  `split_dim` before being passed to the matching `Fm`. This is a strict
  wrapper contract: masks and channel-aligned edge embeddings can be chunked,
  but a graph structure or scalar cannot. Keep `edge_index` in the dedicated
  second argument position so it is shared unchanged by all groups.

The inverse reverses group order and subtracts the same `Fm` result. Each Fm
must therefore be deterministic for the same inputs during reconstruction.
Dropout must use an externally supplied shared mask or be otherwise
reproducible; ordinary independent random dropout breaks inversion.

In the inspected reversible protein construction, hidden node width and
encoded edge width are both divided/replicated consistently with the group
count, while `edge_index` remains shared. Use that as the model-shape pattern,
not as permission to silently pad a non-divisible width.

## InvertibleModuleWrapper

`InvertibleModuleWrapper(fn, keep_input=False, keep_input_inverse=False,
num_bwd_passes=1, disable=False, preserve_rng_state=False)` expects `fn` to
implement both `forward` and `inverse` with compatible positional arguments.
Its forward and inverse methods accept one or more inputs and unpack a single
returned tensor; multiple outputs remain a tuple.

- `disable=True` executes the wrapped module normally. Use this first for
  debugging and correctness comparison.
- With checkpointing enabled (`disable=False`), the wrapper discards/rebuilds
  input storage as configured and recomputes during backward. The supported
  training pattern is ordinary `.backward()`, not arbitrary repeated
  `torch.autograd.grad()` calls.
- `num_bwd_passes` must cover the number of backward traversals. The default
  one is the safe memory-freeing choice; setting it too high retains memory,
  setting it too low causes a later backward failure.
- `keep_input=True` or `keep_input_inverse=True` trades memory for easier
  reconstruction. These settings are ignored when disabled.
- `preserve_rng_state=True` is required when reconstruction depends on RNG
  state and a valid deterministic inverse is not enough. Shared masks are
  usually clearer for reversible graph blocks.

The wrapper stores learnable parameters from `fn` for the custom backward.
Avoid hidden, unregistered state or side effects in an Fm. Validate a forward /
`inverse` round trip before enabling checkpointing.

## Safe construction recipe

1. Pick `group=2` unless there is a reason to use another divisor. Assert
   `C % group == 0` and that every channel-aligned extra argument has the same
   divisible width.
2. Create one same-width Fm and deep-copy it for the remaining groups when
   independent parameters are intended. Do not accidentally share modules if
   independent group parameters are required.
3. Call coupling as `(x, edge_index, mask, edge_embedding)` rather than putting
   graph structure in the chunked extra-argument list.
4. With `disable=True`, verify output shape, finite values, and
   `max(abs(inverse(forward(x,...)) - x))` against a small tolerance.
5. Run a scalar loss backward once with the wrapper disabled, then once enabled
   if the environment's PyTorch/PyG combination supports it. Compare parameter
   gradient finiteness, not exact bitwise values.
6. Scale to GPU/deep models only through the owner workflow. Large reversible
   OGB runs, data acquisition, and checkpoint/result comparison belong to
   [ogb-workflows](../../ogb-workflows/SKILL.md).

## Known boundary

The reversible primitive itself is CPU-testable with a tiny additive module.
Memory savings, long-depth stability, and GPU performance are not established
by a tiny CPU round trip. DGL RevGAT is an optional sibling workflow and is not
covered by this layer-level helper.
