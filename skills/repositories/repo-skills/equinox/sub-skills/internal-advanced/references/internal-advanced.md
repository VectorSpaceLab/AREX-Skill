# Internal Advanced Workflows

`equinox.internal` is a semi-public namespace for advanced JAX users and
downstream libraries. Prefer public `eqx.*` APIs unless the task explicitly
requires internal behavior.

## Namespace overview

Useful exports include:

| Family | Symbols | Use |
| --- | --- | --- |
| No-inline compilation | `noinline`, `noinline_p` | Create MLIR subgraphs and reduce repeated inlining/compile pressure. |
| Loops | `while_loop`, `scan`, `buffer_at_set`, `MaybeBuffer` | Lax, bounded, and checkpointed loop/scan variants over PyTrees. |
| Transform restrictions | `nontraceable`, `nondifferentiable`, `nondifferentiable_backward`, `nonbatchable` | Mark values or paths that must not participate in certain transforms. |
| Primitive helpers | `filter_primitive_def`, `filter_primitive_jvp`, `filter_primitive_transpose`, `filter_primitive_batching`, `filter_primitive_bind`, `materialise_zeros`, `create_vprim` | Write JAX primitives that accept filtered PyTrees and custom transform rules. |
| JAXPR helpers | `finalise_jaxpr`, `finalise_fn`, `finalise_make_jaxpr`, `register_impl_finalisation` | Finalize or reify JAXPRs for downstream-library work. |
| Closure/progress/string helpers | `closure_to_pytree`, `GetKey`, `str2jax`, progress meters, `ω` | Utilities used by Equinox and ecosystem libraries. |

## `noinline`

`eqxi.noinline(fn, abstract_fn=None)` wraps a function so it is lowered as a
separate subgraph instead of being inlined everywhere. This can reduce compile
cost when the same expensive subfunction is called repeatedly.

```python
import equinox as eqx
import equinox.internal as eqxi
import jax
import jax.numpy as jnp

@eqxi.noinline
def block(x):
    return jnp.sin(x) + 1

@eqx.filter_jit
def f(x):
    return block(x) + block(x)
```

If the function has shape-dependent output that cannot be inferred directly,
provide `abstract_fn`. If repeated scalar arguments should be dynamic, pass them
as JAX arrays rather than Python scalars, because static leaves can trigger
recompilation.

Native evidence marks `noinline` as CPU-only tested. Treat accelerator behavior
as unverified until a backend-specific smoke passes.

## Internal `while_loop`

Useful signature:

```python
eqxi.while_loop(cond_fun, body_fun, init_val, *, max_steps=None,
                buffers=None, kind, checkpoints=None, base=16)
```

Kinds:

- `kind="lax"`: closest to `jax.lax.while_loop`; efficiently supports
  forward-mode autodifferentiation, but not reverse-mode autodifferentiation.
- `kind="bounded"`: supports forward and reverse AD, but requires an integer
  `max_steps`; time and memory increase as `max_steps` grows.
- `kind="checkpointed"`: supports reverse-mode differentiation through loops
  with checkpointing trade-offs, but does not support forward-mode AD.

Use `buffers=` only when the loop writes into explicit buffer-like structures.
Buffer restrictions are unchecked: do not write the same location twice and do
not read a location before it has been written. Keep tiny shape tests for each
new loop because transform and buffer semantics are subtle.

## Internal `scan`

Useful signature:

```python
eqxi.scan(f, init, xs, length=None, *, buffers=None,
          kind, checkpoints=None)
```

Use `kind="lax"` for ordinary scan behavior. Use `kind="checkpointed"` when
memory/reverse-mode behavior is the point. `checkpoints="all"` or an integer
changes memory/compute trade-offs.

## Restricting transforms

`eqxi.nontraceable`, `eqxi.nondifferentiable`,
`eqxi.nondifferentiable_backward`, and `eqxi.nonbatchable` are explicit guards.
They are useful when a value may pass through some transforms but should raise in
others.

Expected failures are part of the contract. For example, `nontraceable` can be
valid in eager or selected JIT paths but intentionally fail under gradient or
batching transforms.

## Primitive authoring

Filtered primitive helpers support custom primitives that accept PyTrees with
both dynamic and static leaves.

Minimal planning checklist:

1. Define the primitive implementation.
2. Define abstract evaluation.
3. Add a JVP rule if forward AD is supported.
4. Add a transpose rule if reverse AD is supported.
5. Add a batching rule if `vmap`/`pmap` is supported.
6. Bind through `filter_primitive_bind` so PyTree dynamic/static partitioning is
   handled consistently.
7. Test eager, `jit`, AD, and batching separately.

Use `materialise_zeros` when transform rules must convert symbolic zeros into
concrete zero-like leaves.

## JAXPR finalisation

Use `finalise_jaxpr`, `finalise_fn`, or `finalise_make_jaxpr` when a downstream
library needs a finalized JAXPR representation. Finalisation rewrites custom
primitives through registered implementation finalisations, so it should be the
last JAXPR-processing step; the native docs warn not to apply later JAX
transforms such as `vmap` or `grad` to finalised functions because results may
be silently incorrect. These helpers are sensitive to JAX internals, so run
version-pinned tests after JAX upgrades.

## ONNX note

`eqxi.to_onnx` exists, but the repo’s ONNX test is skipped due to an upstream
`tf2onnx` issue. This generated skill does not claim ONNX export coverage. Treat
ONNX as a separate environment-and-verification task.

## Validation checklist

- Public API alternatives were ruled out first.
- The exact internal helper and transform context are named.
- CPU smoke passes before writing user-facing guidance.
- Any accelerator claim has separate backend evidence.
- Expected transform failures are documented as expected, not hidden.
- JAX and Equinox versions are pinned or reverified for fragile internal paths.
