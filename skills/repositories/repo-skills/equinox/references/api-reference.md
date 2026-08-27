# Equinox API Reference

Use this file as a compact cross-skill index. For workflow depth, read the
nearest sub-skill reference.

## Package and installation

- Distribution: `equinox`
- Import root: `import equinox as eqx`
- Common submodules: `equinox.nn`, `equinox.debug`, `equinox.internal`
- Public install: `pip install equinox`
- Python requirement: Python 3.10+
- Core dependencies: JAX, jaxtyping, typing-extensions, wadler-lindig

A minimal import check is:

```python
import equinox as eqx
import jax
print(eqx.__version__)
print(jax.default_backend())
```

## Root package surface

| Area | Symbols | Use |
| --- | --- | --- |
| Modules | `Module`, `field`, `static_field`, `AbstractVar`, `AbstractClassVar`, `module_update_wrapper`, `Partial` | Define callable PyTree models, static fields, converters, abstract attributes, and wrapped callables. |
| Filtering | `is_array`, `is_array_like`, `is_inexact_array`, `is_inexact_array_like`, `filter`, `partition`, `combine` | Split mixed PyTrees into dynamic array leaves and static non-array leaves. |
| Transformations | `filter_jit`, `filter_grad`, `filter_value_and_grad`, `filter_jvp`, `filter_vjp`, `filter_jacfwd`, `filter_jacrev`, `filter_hessian`, `filter_custom_jvp`, `filter_custom_vjp`, `filter_checkpoint`, `filter_closure_convert`, `filter_vmap`, `filter_pmap`, `filter_eval_shape`, `filter_make_jaxpr`, `filter_shard`, `filter_pure_callback` | Apply JAX transforms to arbitrary PyTrees instead of only all-array arguments. |
| Tree utilities | `tree_at`, `tree_equal`, `tree_check`, `tree_flatten_one_level`, `apply_updates` | Replace leaves, compare structures, check duplicated nodes, inspect one-level flattening, and apply optimizer updates. |
| Serialization | `tree_serialise_leaves`, `tree_deserialise_leaves`, `default_serialise_filter_spec`, `default_deserialise_filter_spec` | Save and load serializable leaves while using a like-tree to restore structure and non-array leaves. |
| Runtime checks | `error_if`, `branched_error_if`, `Enumeration` | Raise runtime errors inside transformed JAX code and use JAX-compatible enumerations. |
| Diagnostics | `tree_pformat`, `tree_pprint`, `clear_caches`, `debug.*` | Pretty-print PyTrees, clear internal caches, and debug NaNs/traces/dead-code elimination. |

## Key verified signatures

The exact overloads are richer than shown here; these signatures are the most
useful forms to remember.

```python
# Module and fields
eqx.Module() -> None
eqx.field(*, converter=None, static=False, **dataclass_kwargs)

# Filtering
eqx.filter(pytree, filter_spec, inverse=False, replace=None, is_leaf=None)
eqx.partition(pytree, filter_spec, replace=None, is_leaf=None)
eqx.combine(*pytrees, is_leaf=None)

# Transformations
eqx.filter_jit(fun=sentinel, *, donate="none", **jitkwargs)
eqx.filter_grad(fun=sentinel, *, has_aux=False, **gradkwargs)
eqx.filter_vmap(fun=sentinel, *, in_axes=eqx.if_array(0), out_axes=eqx.if_array(0), axis_name=None, axis_size=None, **vmapkwargs)
eqx.filter_pmap(fun=sentinel, *, in_axes=eqx.if_array(0), out_axes=eqx.if_array(0), axis_name=None, axis_size=None, donate="none", **pmapkwargs)
eqx.filter_eval_shape(fun, *args, **kwargs)
eqx.filter_make_jaxpr(fun)
eqx.filter_shard(pytree, sharding)

# Tree utilities
eqx.tree_at(where, pytree, replace=sentinel, replace_fn=sentinel, is_leaf=None)
eqx.tree_equal(*pytrees, typematch=False, rtol=0, atol=0)
eqx.tree_check(pytree)
eqx.apply_updates(model, updates)

# Serialization and runtime errors
eqx.tree_serialise_leaves(path_or_file, pytree, filter_spec=eqx.default_serialise_filter_spec, is_leaf=None)
eqx.tree_deserialise_leaves(path_or_file, like, filter_spec=eqx.default_deserialise_filter_spec, is_leaf=None)
eqx.error_if(x, pred, msg, *, on_error="default")
eqx.branched_error_if(x, pred, index, msgs, *, on_error="default")
```

## `equinox.nn` surface

Most `equinox.nn` layers operate on a single example, not an entire batch. Use
`jax.vmap`, `eqx.filter_vmap`, or `eqx.filter_pmap` around the call when a batch
or device axis is needed.

| Family | Symbols | Notes |
| --- | --- | --- |
| Dense and composition | `Linear`, `Identity`, `MLP`, `Sequential`, `Lambda` | `MLP(..., scan=True)` can improve compile-time behavior for deep stacks. `Sequential` splits a key across layers when a key is supplied. |
| Convolution and pooling | `Conv`, `Conv1d`, `Conv2d`, `Conv3d`, `ConvTranspose*`, `MaxPool*`, `AvgPool*`, `Adaptive*Pool*` | Follow single-example conventions and vmap over batches. |
| Sequence and attention | `GRUCell`, `LSTMCell`, `MultiheadAttention`, `Embedding`, `RotaryPositionalEmbedding` | Call shape is layer-specific; pass PRNG keys for stochastic or initialization paths as documented. |
| Regularization and inference | `Dropout`, `inference_mode` | `inference_mode(pytree, value=True)` toggles all nested `inference` attributes. |
| Normalization and state | `LayerNorm`, `GroupNorm`, `RMSNorm`, `BatchNorm`, `State`, `StateIndex`, `make_with_state`, `delete_init_state` | `BatchNorm` is stateful and must run inside a matching named `vmap`/`pmap` axis for training statistics. |
| Weight sharing and parametrization | `Shared`, `WeightNorm`, `SpectralNorm` | `Shared` ties leaves by replacing duplicate destinations with values computed from a source. |
| Activations | `PReLU` | Some activations may have trainable parameters and are PyTrees. |

Useful verified signatures:

```python
eqx.nn.MLP(in_size, out_size, width_size, depth, activation=jax.nn.relu, final_activation=lambda x: x, use_bias=True, use_final_bias=True, dtype=None, *, scan=False, key)
eqx.nn.Sequential(layers)
eqx.nn.BatchNorm(input_size, axis_name, eps=1e-5, channelwise_affine=True, momentum=0.99, inference=False, dtype=None, mode="legacy")
eqx.nn.State(model)
eqx.nn.StateIndex(init)
eqx.nn.Shared(pytree, where, get)
eqx.nn.inference_mode(pytree, value=True)
```

## `equinox.debug`

| Symbol | Use |
| --- | --- |
| `debug.announce_transform` | Print or collect which transform stage is being traced/lowered. |
| `debug.backward_nan(x, name=None, terminate=True)` | Detect NaNs produced during backward passes. |
| `debug.breakpoint_if(pred, **kwargs)` | Open a JAX debugger conditionally. |
| `debug.store_dce` / `debug.inspect_dce` | Check whether values were dead-code eliminated. |
| `debug.assert_max_traces(fn=sentinel, *, max_traces)` | Fail when a function is traced too many times. |
| `debug.get_num_traces(fn)` | Inspect the current trace count for a wrapped function. |

## `equinox.internal`

`equinox.internal` is semi-public and has no stability guarantees. Use it only
when a task explicitly needs advanced JAX-library-building behavior.

Common advanced signatures:

```python
eqx.internal.noinline(fn, abstract_fn=None)
eqx.internal.while_loop(cond_fun, body_fun, init_val, *, max_steps=None, buffers=None, kind, checkpoints=None, base=16)
eqx.internal.scan(f, init, xs, length=None, *, buffers=None, kind, checkpoints=None)
eqx.internal.nontraceable(x, *, name="nontraceable operation")
eqx.internal.nondifferentiable(x, *, name="nondifferentiable operation")
eqx.internal.filter_primitive_def(rule)
eqx.internal.filter_primitive_jvp(rule)
eqx.internal.filter_primitive_transpose(rule=sentinel, *, materialise_zeros=False)
eqx.internal.filter_primitive_batching(rule)
eqx.internal.filter_primitive_bind(prim, *args)
eqx.internal.finalise_jaxpr(closed_jaxpr)
eqx.internal.finalise_fn(fn)
eqx.internal.str2jax(msg)
```

Prefer public `eqx.*` APIs unless the user specifically names one of these
helpers or is implementing a downstream JAX library.
