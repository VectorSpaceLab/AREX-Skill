# Troubleshooting parameters, state, RNG, naming, and hooks

Use this reference when a Haiku module, direct API call, RNG path, or state update fails. Start with the error text, then verify the transform wrapper and expected parameter/state tree keys.

## Quick triage checklist

1. Is the failing code executed inside a function wrapped by `hk.transform` or `hk.transform_with_state`?
2. Does the function use mutable state? If yes, it must use `hk.transform_with_state` and thread state through `apply`.
3. Does any executed path call `hk.next_rng_key()` or `hk.next_rng_keys(...)`? If yes, the corresponding `init` or `apply` call needs a non-`None` RNG key.
4. Are you creating modules or values in a constructor/import-time closure outside the transformed function? Move creation inside the transformed function or into an `hk.Module` method called from it.
5. Do your expected keys match Haiku naming rules: module/name-scope path first, leaf name second, and top-level values under `"~"`?

## Common symptoms and fixes

| Symptom or error text | Likely cause | Fix | Quick check |
| --- | --- | --- | --- |
| `must be used as part of an hk.transform` for `get_parameter`, `get_state`, `set_state`, `next_rng_key`, `name_scope`, or hooks | A direct Haiku API was called outside a transformed context. | Wrap the owning function with `hk.transform` or `hk.transform_with_state`, then call `init`/`apply`. Do not call direct APIs at module import time or in plain utility functions. | Put a breakpoint/print in the function passed to `hk.transform*`, not around `apply`. |
| `All hk.Modules must be initialized inside an hk.transform` | An `hk.Module` was instantiated before entering the transformed function. | Instantiate modules inside the transformed function or inside another module method called from it. Avoid global module instances. | Search for `hk.Linear(...)`, custom `hk.Module(...)`, or `MyModule(...)` outside the transformed function. |
| `super constructor must be called` or missing `module_name` | Custom module did not call `super().__init__(name=name)` before creating submodules/values. | Make the first meaningful line of `__init__` call `super().__init__(name=name)`. | Confirm `self.module_name` exists after construction inside a transform. |
| `Initializer must be specified` | First creation of a parameter used `hk.get_parameter(name, shape)` without an initializer. | Provide `init=...` for the first creation, or ensure the parameter already exists in `params` during `apply`. | In `init`, every new parameter needs a shape, dtype, and initializer. |
| `does not match shape` for a parameter | The same module/scope and leaf name was requested with a different shape. | Use separate names for different shapes, or ensure all calls reuse the same shape. | Print `jax.tree.map(lambda x: x.shape, params)`. |
| `No value for ... perhaps set an init function?` | `hk.get_state` requested missing state without an initializer. | Pass `shape`, `dtype`, and `init`, or call `hk.set_state` earlier in the same transformed call. | Check whether the state key exists in the input state tree. |
| `Must provide shape and dtype to initialize` | `hk.get_state` had `init` but omitted `shape` or `dtype` while state was missing. | Provide explicit `shape` and `dtype` for state initialization. | State init has no parameter-shape inference unless you supply it. |

## Recovering from `hk.next_rng_key()` with `rng=None`

Typical error:

```text
You must pass a non-None PRNGKey to init and/or apply if you make use of random numbers.
```

What it means:

- `hk.next_rng_key()` or `hk.next_rng_keys(...)` executed during `init` or `apply`.
- That transformed call received `rng=None`, or the apply function was wrapped to omit RNG and then reached stochastic code.

Fixes:

1. If randomness is required, pass a real key:

   ```python
   params = forward.init(jax.random.PRNGKey(0), x)
   y = forward.apply(params, jax.random.PRNGKey(1), x)
   ```

2. In a loop, split before each stochastic call:

   ```python
   rng, apply_rng = jax.random.split(rng)
   y = forward.apply(params, apply_rng, x)
   ```

3. If randomness is optional, rewrite the path with `hk.maybe_next_rng_key()` and handle `None` explicitly:

   ```python
   key = hk.maybe_next_rng_key()
   if key is None:
       return deterministic_output
   return stochastic_output(key)
   ```

4. Do not use `hk.without_apply_rng` on a transformed function that can execute `hk.next_rng_key()`. If the function has both deterministic and stochastic modes, either keep the RNG argument or make the stochastic branch require a key.

## Mutable state with the wrong transform

Typical symptoms:

- Error text pointing to `hk.transform_with_state`.
- State updates appear to be missing.
- `apply` return signature does not include updated state.

Fix:

```python
forward = hk.transform_with_state(forward_fn)
params, state = forward.init(rng, *args)
out, state = forward.apply(params, state, rng, *args)
```

Do not wrap stateful code in `hk.transform` and expect `hk.set_state` values to persist. If you want to call a stateful Haiku module but expose a stateless interface, choose that wrapper deliberately in the transform-selection sub-skill and verify the state is empty or intentionally ignored.

## Duplicate module names and parameter reuse

### Error: `Module name 'name_1' is not unique`

Likely causes:

- You explicitly requested a numbered name that Haiku already generated or reserved.
- A refactor with `hk.name_like` made two methods create modules under the same method-like name.
- A `hk.name_scope` or `hk.force_name` introduced an absolute name collision.

Fixes:

- Use explicit stable unique names: `encoder`, `decoder`, `head_a`, `head_b`.
- Avoid manually using `_1`, `_2` suffixes unless preserving known checkpoint keys.
- If using `hk.name_like`, explicitly name submodules that used to be auto-numbered.
- If using `hk.force_name`, confirm intentional sharing by inspecting the parameter tree.

### Unexpected sharing

Symptom: two logical modules update the same parameter bundle.

Causes and fixes:

- Same module instance reused: expected sharing; create a second instance if independence is needed.
- `hk.force_name` used: remove it unless absolute-name sharing is intentional.
- Same explicit name under same scope with compatible shape: Haiku may treat it as the same parameter request. Give distinct names.

### Unexpected non-sharing

Symptom: keys such as `linear` and `linear_1` appear when you expected sharing.

Fixes:

- Reuse the same module object instead of constructing two modules.
- Pass `name=hk.force_name(existing.module_name)` only if object reuse is impossible and sharing is truly desired.

## Parameter/state tree key confusion

Common surprises:

- `"~"` means the value was created at top level inside a transform, outside any module.
- `parent/~/child` means `child` was created in `Parent.__init__`.
- `parent/~encode/child` means `child` was created in a method named `encode`.
- `outer/proj` may come from `with hk.name_scope("outer"):` around `hk.Linear(name="proj")`.
- The leaf key (`"w"`, `"b"`, `"count"`) is separate from the module/scope key.

Debugging snippet:

```python
def shape_tree(tree):
    return jax.tree.map(lambda v: getattr(v, "shape", None), tree)

print(shape_tree(params))
print(shape_tree(state))
```

If a checkpoint does not load because names changed, compare old and new shape trees before editing. Prefer preserving names with explicit `name=` or `hk.name_like` over broad renaming after the fact.

## Calling Haiku APIs inside raw JAX transforms

Symptom: an error explains that a Haiku side-effecting API was used inside `jax.vmap`, `jax.scan`, `jax.grad`, `jax.cond`, `jax.switch`, or similar.

Cause: raw JAX transformations expect pure functions, while direct Haiku APIs mutate Haiku's internal transformed context.

Fix: use Haiku's wrappers (`hk.vmap`, `hk.scan`, `hk.grad`, `hk.cond`, etc.) or move the JAX transform outside the transformed Haiku function. Route this repair to the `jax-interop-and-advanced` sub-skill.

## Hook-specific failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| Hook silently affects too much code | Creator/getter/setter/interceptor scoped too broadly. | Put the `with hk.custom_*` or `with hk.intercept_methods` block around the narrow subcall only, and filter by `context.module_name`, `context.name`, or `context.method_name`. |
| Stacked hook does not run later hooks | Callback returned without calling `next_creator`, `next_getter`, `next_setter`, or `next_fun`. | Call the continuation unless you deliberately short-circuit the stack. |
| Interceptor causes recursion or repeated names | Interceptor creates modules/scopes without guarding against the modules it introduces. | Avoid module creation in interceptors; if necessary, filter out helper scope/module types and inspect names. |
| State getter/creator hook did not affect state | `custom_creator` or `custom_getter` defaults to parameters only. | Pass `state=True` when state should be intercepted. |

## When to run the smoke script

Run `scripts/haiku_rng_state_smoke.py --mode all` after changing module/state/RNG code or when confirming a new environment. It checks:

- expected parameter tree keys for a custom module;
- a mutable counter under `hk.transform_with_state`;
- required RNG failure with `rng=None` and success with a real key;
- optional no-RNG fallback via `hk.maybe_next_rng_key`.
