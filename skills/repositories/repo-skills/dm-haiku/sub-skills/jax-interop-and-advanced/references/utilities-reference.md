# Advanced Haiku utilities reference

This reference covers utilities owned by the JAX interop and advanced sub-skill: Haiku parameter/state data structures, mixed precision, summaries and graph inspection, configuration/optimization flags, and testing helpers.

## Haiku data structures

Haiku `init` and stateful `apply` functions return two-level mappings shaped like:

```python
{
    "module_name": {
        "parameter_or_state_name": value,
    }
}
```

Use `hk.data_structures` helpers rather than hand-mutating nested dictionaries when splitting, merging, or traversing these trees.

| API | Use when | Notes |
| --- | --- | --- |
| `hk.data_structures.traverse(structure)` | Iterate over `(module_name, name, value)` leaves. | Iteration is sorted by module/name, which makes logs and tests deterministic. |
| `hk.data_structures.filter(predicate, structure)` | Keep leaves matching a predicate. | Predicate receives `(module_name, name, value)`. Returns a new structure, not a view. |
| `hk.data_structures.partition(predicate, structure)` | Split into `(matching, not_matching)`. | Primary helper for trainable/frozen params or optimizer groups. |
| `hk.data_structures.partition_n(fn, structure, n)` | Split into `n` buckets. | `fn(module_name, name, value)` must return an integer in `[0, n)`. |
| `hk.data_structures.merge(*structures, check_duplicates=False)` | Recombine structures. | Later structures win on duplicate paths. With `check_duplicates=True`, duplicate array paths with different shape/dtype raise. |
| `hk.data_structures.map(fn, structure)` | Transform every leaf while preserving two-level keys. | Useful for masks, dtype casts, or summaries. |
| `hk.data_structures.is_subset(subset=..., superset=...)` | Check path membership. | Compares paths, not array values. Empty leaves are vacuously subsets. |
| `hk.data_structures.tree_size(tree)` | Count scalar array elements in a pytree. | Useful for parameter counts. |
| `hk.data_structures.tree_bytes(tree)` | Estimate minimum array bytes in a pytree. | Device allocation may be larger due to padding/alignment. |
| `hk.data_structures.to_haiku_dict(structure)` | Copy into Haiku's normal mutable two-level mapping type. | Use when building params/state from external nested mappings. |
| `hk.data_structures.to_mutable_dict(mapping)` | Convert immutable/flat mappings to plain mutable dicts. | Use before local edits to copies. |
| `hk.data_structures.to_immutable_dict(mapping)` | Convert to an immutable `FlatMap`. | Mainly useful for checkpoint compatibility and JAX pytree efficiency. |

### Freezing or optimizer grouping recipe

```python
# Keep only the classification head trainable.
trainable, frozen = hk.data_structures.partition(
    lambda module_name, name, value: module_name.startswith("head"),
    params,
)

# Pass `trainable` to the optimizer; preserve `frozen` for apply.
updated_trainable = optimizer_update(trainable)
params_for_apply = hk.data_structures.merge(frozen, updated_trainable,
                                            check_duplicates=True)

# Optional diagnostics.
for module_name, name, value in hk.data_structures.traverse(trainable):
    print(f"trainable: {module_name}/{name} {value.shape} {value.dtype}")
print("total parameters:", hk.data_structures.tree_size(params_for_apply))
```

Use path predicates based on Haiku module names, parameter names (`"w"`, `"b"`, etc.), or value metadata (`shape`, `dtype`). Avoid mutating `params` in place; prefer partition/merge to make the applied tree explicit.

## Mixed precision

Haiku mixed precision uses `hk.mixed_precision` and JMP policies. Typical entry points:

| API | Contract |
| --- | --- |
| `hk.mixed_precision.set_policy(module_cls, policy)` | Apply a JMP policy to all instances of a Haiku module class created in the current thread. |
| `hk.mixed_precision.get_policy(module_cls)` | Return the explicit policy for a class, or `None`. |
| `hk.mixed_precision.current_policy()` | Return the policy active while a module method is running, or `None`. |
| `hk.mixed_precision.clear_policy(module_cls)` | Remove a policy for a class. |
| `hk.mixed_precision.push_policy(module_cls, policy)` | Context manager that sets a policy then restores the previous policy. |

Minimal pattern:

```python
import jmp

policy = jmp.get_policy("params=float32,compute=float16,output=float32")
try:
    hk.mixed_precision.set_policy(hk.Linear, policy)
    transformed = hk.transform(lambda x: hk.Linear(4)(x))
    params = transformed.init(jax.random.PRNGKey(0), jnp.ones([2, 3]))
    y = transformed.apply(params, None, jnp.ones([2, 3]))
finally:
    hk.mixed_precision.clear_policy(hk.Linear)
```

Guidance:

- Set policies before constructing/calling affected modules.
- Scope policies in tests with `push_policy` or `try/finally` cleanup to avoid contaminating later tests.
- Mixed precision can be validated on CPU for API behavior, but speedups usually require accelerator support from JAX.
- Policies are per module class and current thread; top-level module policies can implicitly affect child modules during that top-level call.

## Visualization and summaries

### DOT graphs

- `hk.to_dot(fun)` returns a callable that produces a Graphviz DOT source string from concrete inputs.
- `hk.experimental.abstract_to_dot(fun)` uses abstract inputs such as `jax.ShapeDtypeStruct` and avoids concrete execution, but it does not support data-dependent control flow.
- Producing the DOT string does not require the Python `graphviz` package. Rendering it to an image/notebook object does.

Pattern for a transformed apply function:

```python
def forward(x):
    return hk.nets.MLP([8, 2])(x)

net = hk.without_apply_rng(hk.transform(forward))
x = jnp.ones([4, 3])
params = net.init(jax.random.PRNGKey(0), x)
dot_source = hk.to_dot(net.apply)(params, x)
assert "digraph" in dot_source
```

Keep DOT generation optional in scripts that must run in minimal environments; do not require Graphviz rendering unless the user asked for a visualization artifact.

### `hk.experimental.tabulate` and `eval_summary`

`hk.experimental.tabulate(f, columns=..., filters=..., tabulate_kwargs=...)` returns a callable that summarizes module calls, shapes, owned parameters, and parameter sizes as a table string. `f` may be an untransformed function, a transformed object, or a transformed apply/init callable.

`hk.experimental.eval_summary(f)` returns raw `MethodInvocation` records, including module details, input/output specs, context, and call stack. Use it when you need programmatic inspection rather than a table.

Useful columns for `tabulate` include `module`, `config`, `owned_params`, `input`, `output`, `params_size`, and `params_bytes`. Useful filters include `has_output` and `has_params`.

### `haiku.experimental.jaxpr_info`

`hk.experimental.jaxpr_info` provides lower-level JAX expression inspection:

- `make_model_info(f, name=None, include_module_info=True, compute_flops=None, axis_env=None)` returns a callable that captures a nested `Module` tree for example arguments.
- `format_module(module)` converts that tree into a readable text representation.
- `as_html(module)` and `as_html_page(module)` return interactive HTML strings for notebooks or reports.
- `Module` and `Expression` records include module names, parameter/state counts, primitive expressions, optional FLOPs, and shape details.

Pattern:

```python
info_fn = hk.experimental.jaxpr_info.make_model_info(apply_callable,
                                                     name="model")
module_info = info_fn(*example_args)
print(hk.experimental.jaxpr_info.format_module(module_info))
```

This can be expensive for large models; run it on the smallest representative shapes that exercise the relevant modules.

## Configuration and optimization flags

| API | Use when | Caution |
| --- | --- | --- |
| `hk.config.context(...)` | Temporarily override `check_jax_usage`, `module_auto_repr`, `restore_flatmap`, or `rng_reserve_size`. | Preferred for local experiments/tests. |
| `hk.config.set(...)` | Set global config values in the current thread. | Restore values manually if used in shared sessions. |
| `hk.experimental.check_jax_usage(enabled=True)` | Make raw JAX transforms/control flow used incorrectly inside Haiku produce clearer errors. Returns previous value. | Turn on while debugging; restore previous value after the check. |
| `hk.experimental.module_auto_repr(enabled)` | Enable/disable automatic `hk.Module.__repr__`. Returns previous value. | Useful when repr generation is noisy or slow. |
| `hk.experimental.rng_reserve_size(size)` | Reserve blocks of RNG keys for `hk.next_rng_key`. Returns previous value. | `size` must be positive and changing it changes produced random numbers. |
| `hk.experimental.optimize_rng_use(fun)` | Wrap a Haiku function to pre-count RNG use and split keys once. | Calls abstract evaluation first; use when RNG splitting overhead matters. |
| `hk.experimental.fast_eval_shape(fun, *args, **kwargs)` | Faster shape evaluation by replacing initializers with zeros, dropout with identity, and `jax.random.fold_in` with identity. | This is for shape/structure, not validating stochastic values. |

Debug pattern:

```python
old = hk.experimental.check_jax_usage(True)
try:
    params = transformed.init(rng, *example_args)
finally:
    hk.experimental.check_jax_usage(old)
```

## Testing helper

`hk.testing.transform_and_run(f=None, seed=42, run_apply=True, jax_transform=None, *, map_rng=None)` transforms a small function with `hk.transform_with_state`, runs init, and optionally runs apply. It is useful for tests and notebooks that exercise module code without writing full transform boilerplate.

Examples:

```python
@hk.testing.transform_and_run
def smoke_linear():
    y = hk.Linear(2)(jnp.ones([1, 3]))
    assert y.shape == (1, 2)
    return y

out = smoke_linear()
```

With a JAX transform variant:

```python
@hk.testing.transform_and_run(jax_transform=jax.jit)
def smoke_jitted():
    return hk.Linear(2)(jnp.ones([1, 3]))
```

For `pmap`, provide `map_rng` to broadcast or split init/apply RNGs across devices. Keep these tests synthetic and shape/assertion based so they remain portable across CPU-only and accelerator-backed JAX installations.
