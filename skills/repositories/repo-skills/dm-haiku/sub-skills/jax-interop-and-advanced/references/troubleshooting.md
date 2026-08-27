# Troubleshooting Haiku JAX interop and advanced utilities

Use this guide when advanced Haiku wrappers or utilities fail in ways that look like tracer leaks, missing state, bad RNG behavior, name collisions, optional dependency errors, or stale mixed precision policy.

## Raw JAX transform inside transformed Haiku code

**Symptoms**

- `haiku.JaxUsageError` after enabling `hk.experimental.check_jax_usage(True)`.
- JAX tracer errors such as an unexpected tracer escaping a transformation.
- Params/state/RNG appear unchanged after a raw `jax.vmap`, `jax.lax.scan`, or `jax.remat` body that calls Haiku APIs.
- The failure only appears under `jax.jit`, `jax.vmap`, `jax.checking_leaks`, or a larger training step.

**Likely cause**

A raw JAX transform was used before Haiku side effects were made pure. Functions that call `hk.Linear`, `hk.get_parameter`, `hk.get_state`, `hk.set_state`, `hk.next_rng_key`, or other Haiku context APIs are not pure until wrapped by Haiku.

**Fix**

1. If possible, move the JAX transform outside Haiku:
   - Define `forward` with Haiku modules.
   - Run `transformed = hk.transform(forward)` or `hk.transform_with_state(forward)`.
   - Apply `jax.jit`, `jax.vmap`, `jax.grad`, etc. to the pure `init`/`apply` or loss function.
2. If the transform must stay inside Haiku, replace raw JAX with a Haiku wrapper:
   - `jax.vmap(...)` -> `hk.vmap(..., split_rng=False)` or `split_rng=not hk.running_init()`.
   - `jax.lax.scan(...)` -> `hk.scan(...)`.
   - `jax.lax.map(...)` -> `hk.map(...)`.
   - `jax.remat(...)` -> `hk.remat(...)`.
   - `jax.lax.cond`/`switch`/`while_loop`/`fori_loop` -> `hk.cond`/`hk.switch`/`hk.while_loop`/`hk.fori_loop`.
3. Enable guardrails while debugging:

```python
old = hk.experimental.check_jax_usage(True)
try:
    params = transformed.init(rng, *example_args)
finally:
    hk.experimental.check_jax_usage(old)
```

## `hk.vmap` errors and RNG surprises

**Symptoms**

- `TypeError` says `split_rng` must be passed to `hk.vmap`.
- `ValueError` says the function must have at least one non-`None` `in_axes`.
- A `split_rng=True` init fails with an `out_axes` or mapped-parameter error.
- Every mapped example gets the same dropout/noise key, or each mapped example unexpectedly gets a different key.

**Fix**

- Always pass `split_rng` explicitly.
- Use `split_rng=False` for shared params/state and no per-example RNG splitting.
- Use `split_rng=not hk.running_init()` when the body uses RNG and should split keys during apply but not while initializing shared parameters.
- Use `hk.lift` + raw `jax.vmap` on an inner transformed function if you intentionally need mapped parameter axes, such as an ensemble.
- Check `in_axes`: at least one mapped argument must have a non-`None` axis and all mapped axes must have compatible sizes.

## `hk.scan`, `hk.map`, and loop state leaks

**Symptoms**

- State changes inside the loop are missing or only reflect one iteration.
- Parameter/state tree shape differs between iterations.
- RNG behavior changes under `jax.jit` or when the scan length changes.

**Fix**

- Use `hk.scan` or `hk.map`, not raw `jax.lax.scan` or `jax.lax.map`, for bodies that touch Haiku APIs.
- Make parameter/state creation unconditional and stable. Create optional modules before the scan or run the creation path under `hk.running_init()`.
- Keep body return structure fixed: `scan` bodies return `(carry, y)` and carry shape/structure should be stable.
- If the body consumes many keys, consider `hk.experimental.rng_reserve_size(size)` or `hk.experimental.optimize_rng_use` only after correctness is established.

## Control-flow branch or while-loop failures

**Symptoms**

- `hk.while_loop` fails during `init` with a message that initialization is not supported.
- `hk.while_loop` condition fails when it calls `hk.set_state` or `hk.next_rng_key`.
- `hk.switch`/`hk.cond` fails because branch output structures differ.
- Apply fails because a branch uses parameters that were not created during init.

**Fix**

- For `hk.while_loop`, run the body once under `hk.running_init()` and only call `hk.while_loop` during apply.
- Keep `cond_fun` pure: no `hk.set_state`, `hk.next_rng_key`, or module calls in the while condition.
- For `hk.cond` and `hk.switch`, ensure every branch returns the same pytree structure and compatible shapes/dtypes.
- If branches create different modules, create all branch modules during init before using the data-dependent branch at apply.

## Tracer or state leakage during shape evaluation

**Symptoms**

- Shape-check code changes module state or consumes RNG unexpectedly.
- A tracer leak is reported when `eval_shape` is nested inside a transformed function.
- The code relies on state changes performed only during shape evaluation.

**Fix**

- Use `hk.eval_shape` inside transformed Haiku functions; use `jax.eval_shape` outside transformed Haiku.
- Remember that `hk.eval_shape` discards changed Haiku state. Treat it as a shape query only.
- Use `hk.experimental.fast_eval_shape` when you only need shape/structure and want Haiku-specific shortcuts for initializers/dropout/fold-in.

## `hk.lift*` name collisions and state updater problems

**Symptoms**

- `ValueError` mentions a key already exists in destination params or state.
- Transparent lift changes or collides with expected module names.
- A transparent lift complains about closing over a module from the outer transform.
- `LiftWithStateUpdater` says it must be used once, must be used inside `hk.transform_with_state`, or was used in the wrong context.
- A stateful inner transform appears to run, but its updated state is not visible in the outer state tree.

**Fix**

- Give `hk.lift`/`hk.lift_with_state` a unique `name` prefix unless you intentionally need transparent names.
- Use `transparent_lift*` only when the inner names are known not to collide with outer module names.
- Do not close over outer `hk.Module` instances from an inner transparent-lifted function; instantiate modules inside the inner function or pass data explicitly.
- For stateful inner transforms, call `params_and_state_fn, updater = hk.lift_with_state(inner.init, name="...")`, run `inner.apply`, then call `updater.update(new_state)` exactly once. If intentionally ignoring state updates, call `updater.ignore_update()` exactly once.
- Use `allow_reuse=True` only when reusing outer params/state is intentional, commonly in control-flow patterns. Otherwise let the default collision checks catch accidental closures.

## Optional Graphviz or JAX2TF dependency failures

**Symptoms**

- `hk.to_dot` or `hk.experimental.abstract_to_dot` returns a DOT string, but rendering fails with `ModuleNotFoundError: graphviz` or a missing Graphviz executable.
- JAX2TF conversion code fails because TensorFlow or `jax.experimental.jax2tf` support is missing or incompatible.
- A notebook-style visualization or conversion example pulls in TensorFlow, Graphviz, or dataset dependencies that are not present in the minimal Haiku/JAX environment.

**Fix**

- Separate DOT generation from rendering. `dot = hk.to_dot(fn)(*args)` should work without Graphviz rendering packages; only `graphviz.Source(dot)` needs Graphviz.
- Keep bundled or CI smoke scripts free of Graphviz and TensorFlow unless the user explicitly requests visualization rendering or JAX2TF export.
- For JAX2TF, first validate the pure Haiku `apply` function with normal JAX arrays, then install/verify TensorFlow and JAX2TF compatibility in a separate optional environment before conversion.
- When using transformed apply functions for DOT or JAX2TF, pass arguments in the correct pure signature, including `params`, optional `state`, optional `rng`, and model inputs.

## Mixed precision policy contamination

**Symptoms**

- A later test/model unexpectedly runs in float16/bfloat16 compute.
- `hk.mixed_precision.current_policy()` is non-`None` inside a module unexpectedly.
- Parameter dtypes or output dtypes differ after an unrelated experiment.
- `push_policy` fails because it is called inside a method on the same module class.

**Fix**

- Set mixed precision policies before constructing/calling modules, not inside the affected module's method.
- Use `hk.mixed_precision.push_policy` or `try/finally` cleanup:

```python
policy = jmp.get_policy("params=float32,compute=float16,output=float32")
try:
    hk.mixed_precision.set_policy(hk.Linear, policy)
    run_experiment()
finally:
    hk.mixed_precision.clear_policy(hk.Linear)
```

- In tests, assert cleanup with `hk.mixed_precision.get_policy(hk.Linear) is None` for any class you modified.
- Remember policies are current-thread state; set them explicitly in worker threads/processes if needed.

## Partition/merge mistakes when freezing parameters

**Symptoms**

- Frozen parameters disappear from `apply`.
- Optimizer updates include bias or normalization parameters that should be excluded.
- `merge(..., check_duplicates=True)` raises about duplicate arrays with different shape/dtype.
- Parameter grouping behaves nondeterministically because predicates inspect unordered dicts.

**Fix**

- Partition full `params` into disjoint structures, update only the trainable partition, then merge frozen and updated trainable partitions before `apply`.
- Base predicates on `(module_name, name, value)` from `hk.data_structures.traverse`; traversal is sorted, so diagnostics are deterministic.
- Use `check_duplicates=True` during development to catch accidental overlapping groups.
- Print grouped paths and counts:

```python
for label, group in [("trainable", trainable), ("frozen", frozen)]:
    print(label, hk.data_structures.tree_size(group))
    for module_name, name, value in hk.data_structures.traverse(group):
        print(f"  {module_name}/{name}: {value.shape} {value.dtype}")
```

## Summary/table inspection issues

**Symptoms**

- `hk.experimental.tabulate` reports invalid columns or filters.
- Summary output is enormous or slow.
- `jaxpr_info` recursion or tracing is expensive on a production-size model.

**Fix**

- Use valid tabulate columns: `module`, `config`, `owned_params`, `input`, `output`, `params_size`, `params_bytes`.
- Use valid filters: `has_output`, `has_params`.
- Run summaries on smaller representative inputs first.
- Prefer `hk.experimental.eval_summary` when you need structured records; prefer `hk.experimental.tabulate` for human-readable tables; prefer `hk.experimental.jaxpr_info` only when JAX primitive/module expression detail is needed.
