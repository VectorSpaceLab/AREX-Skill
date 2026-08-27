# Internal Advanced Troubleshooting

Use this page for `equinox.internal` failures after you have confirmed that a
public `eqx.*` or `jax.lax.*` API is not the safer answer.

## The task probably does not need `equinox.internal`

- **Symptom:** the request is ordinary module construction, filtered JIT/AD/vmap,
  layer usage, serialization, or debug/runtime-error handling.
- **Likely cause:** the semi-public internal namespace looks relevant, but a
  stable public API covers the workflow.
- **Recovery:** route to the public API first: `eqx.filter_jit`,
  `eqx.filter_grad`, `eqx.filter_vmap`, `eqx.filter_pmap`, raw
  `jax.lax.scan`/`jax.lax.while_loop` for ordinary loops, or `eqx.debug.*` and
  `eqx.error_if` for diagnostics. Use internals only when the user or
  downstream-library context explicitly requires them.

## `noinline` recompiles or behaves differently across transforms

- **Symptom:** eager, `jit`, `vmap`, JVP, or gradient results disagree; a wrapped
  function recompiles unexpectedly; accelerator behavior is unclear.
- **Likely cause:** `noinline` creates separate MLIR subgraphs and treats
  non-array/Python-scalar leaves as static. Shape-dependent outputs may need an
  explicit `abstract_fn`. Native evidence only marks this path as CPU-tested.
- **Recovery:** test each transform separately before relying on it:

```python
fn(x)
jax.jit(fn)(x)
jax.vmap(fn)(xs)
jax.jvp(fn, (x,), (tx,))
jax.grad(lambda x: jnp.sum(fn(x)))(x)
```

Wrap repeated scalar arguments as JAX arrays when they should be dynamic, provide
`abstract_fn` for nontrivial output shape/dtype inference or swappable functions,
and keep accelerator support unclaimed until a backend-specific smoke passes.

## Internal `while_loop` gradients or buffers fail

- **Symptom:** reverse-mode gradients fail, `max_steps` errors appear, forward
  JVP fails for checkpointed loops, or buffer results/gradients are wrong.
- **Likely cause:** the loop `kind` has the wrong transform contract:
  `kind="lax"` is closest to `jax.lax.while_loop` and does not support
  reverse-mode AD; `kind="bounded"` supports forward and reverse AD but requires
  an integer `max_steps`; `kind="checkpointed"` supports reverse-mode AD with
  checkpointing but not forward-mode AD. Buffer write/read restrictions are
  unchecked.
- **Recovery:** pick the kind from the desired transform, set `max_steps` for
  bounded loops and either `max_steps` or `checkpoints` for checkpointed loops,
  then compare a tiny loop against `jax.lax.scan`/`jax.lax.while_loop`. For
  `buffers=`, verify array leaves, index shapes/dtypes, no repeated writes to
  the same location, and no reads before a location has been written.

## Internal `scan` memory or gradient behavior is unexpected

- **Symptom:** scan gradients, memory use, or output lengths differ from the
  ordinary `jax.lax.scan` baseline.
- **Likely cause:** `kind="checkpointed"` changes memory/compute trade-offs and
  is not forward-mode autodifferentiable; inconsistent `xs` lengths or an
  unsuitable `checkpoints` value can change behavior.
- **Recovery:** start with `kind="lax"` as the baseline, then switch to
  `kind="checkpointed"` only when checkpointed reverse-mode behavior is the
  point. Use a tiny scan to compare outputs/gradients, pass `length` when the
  leaves do not make it obvious, and choose `checkpoints=None`, an integer, or
  `"all"` deliberately.

## `nontraceable`, `nondifferentiable`, or `nonbatchable` raises

- **Symptom:** a value works eagerly or under plain JIT but raises under AD,
  transposition, or batching.
- **Likely cause:** these helpers are guard rails, not repair tools:
  `nontraceable` intentionally rejects AD/transposition/batching of dynamic
  leaves; `nondifferentiable` rejects forward and reverse AD;
  `nondifferentiable_backward` rejects reverse-mode cotangents; and
  `nonbatchable` rejects vmapped values unless constant-across-batch behavior is
  explicitly allowed.
- **Recovery:** document the expected failing transform and assert it in tests.
  If the value should actually be differentiable or batchable, remove the guard
  or apply it only to the static/non-array portion.

## Primitive helper rules are incomplete

- **Symptom:** a custom primitive works eagerly but fails under `jit`, `grad`,
  `vmap`, transpose, or filtered PyTree inputs; errors mention symbolic zeros,
  `UndefinedPrimal`, or mismatched PyTree/static structure.
- **Likely cause:** one of the required filtered primitive rules is missing or
  inconsistent: implementation, abstract evaluation, JVP, transpose, batching,
  or `filter_primitive_bind` dynamic/static partitioning.
- **Recovery:** add and test rules in this order:

1. implementation via `filter_primitive_def`;
2. abstract evaluation via `filter_primitive_def`;
3. JVP via `filter_primitive_jvp`;
4. transpose via `filter_primitive_transpose`;
5. batching via `filter_primitive_batching` or `create_vprim`;
6. filtered bind tests through `filter_primitive_bind`.

Use `materialise_zeros` when a rule must convert symbolic zero tangents into
concrete zero-like leaves, and test eager, `jit`, AD, and batching separately.

## JAXPR finalisation breaks or gives surprising results

- **Symptom:** `finalise_jaxpr`, `finalise_fn`, or `finalise_make_jaxpr` stops
  working after a JAX upgrade, or later `grad`/`vmap` output is surprising.
- **Likely cause:** finalisation rewrites custom primitives to their registered
  implementation finalisations and depends on JAX internals. The native docs warn
  not to apply further JAX transformations after finalisation because results may
  be silently incorrect.
- **Recovery:** finalise as the last JAXPR-processing step, register
  implementation finalisations for downstream primitives when needed, and rerun
  tiny finalise/primitive/noinline/loop cases after JAX or Equinox upgrades.
  Avoid promising cross-version stability for generated JAXPR structures.

## ONNX is requested

- **Symptom:** the user asks for `eqxi.to_onnx` or ONNX export coverage.
- **Likely cause:** this generated skill intentionally excludes ONNX as a
  verified capability; the source ONNX test is skipped due to an upstream
  `tf2onnx` issue.
- **Recovery:** treat ONNX as a separate environment-and-verification task. Ask
  for a concrete converter/runtime target and a minimal export acceptance case
  before attempting it.
