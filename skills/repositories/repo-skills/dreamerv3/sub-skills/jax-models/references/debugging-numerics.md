# Debugging DreamerV3 JAX Numerics

Use this reference when outputs become non-finite, JAX/XLA fails, checkpoints no longer load, or Ninjax state behaves unexpectedly after model edits.

## First Principles

DreamerV3 mixes three layers of invariants:

1. **Environment/data invariants**: observations and actions match `obs_space`/`act_space`, reset masks are boolean, image observations are `uint8`, and train batches include extras such as `consec` and `stepid`.
2. **Model invariants**: RSSM dimensions divide grouped layers, heads produce losses with batch/time shape, and `loss_scales` exactly covers all loss keys.
3. **JAX/Ninjax invariants**: compute dtype is consistent, state keys are stable, sharding rules match every parameter/activation, and JAX platform flags are set before backend initialization.

Debug in that order. A CUDA or XLA symptom can still be caused by a shape or dtype assertion inside a compiled model.

## Finite Policy Output Checks

The DreamerV3 inner policy returns a diagnostics tree under `outs['finite']`. The outer `embodied.jax.Agent.policy()` wrapper pops that tree and asserts every leaf is true.

The finite diagnostics cover:

```text
obs       current observation tree
carry     previous carry tree
tokens    encoder output
feat      RSSM feature tree
act       sampled action tree
```

When an assertion fails:

1. Reproduce with a fresh process and CPU/debug settings.
2. Print the finite tree before it is asserted only in a temporary debugging branch; do not remove the assertion permanently.
3. If `obs/*` fails, route environment-space/data issues to `embodied-dataflow`.
4. If `tokens/*` fails, inspect encoder inputs: vector sentinel values, `symlog`, image dtype/range, and CNN resolution.
5. If `feat/*` fails, inspect RSSM logits, KL losses, action normalization, and reset masks.
6. If `act/*` fails, inspect policy head distribution type, logits/stddev, and action-space shape.

The outer wrapper separately asserts:

- observation keys exactly equal `obs_space` keys;
- floating observations are finite;
- discrete actions are non-negative;
- continuous actions are finite.

## CPU Debug Route

Use CPU debug when you need readable tracebacks or when a CUDA failure may mask a model assertion. A typical small inspection combination is:

```bash
python scripts/inspect_model_config.py defaults debug size1m
```

For a real run, set the equivalent config keys in the training/config workflow:

```text
jax.platform=cpu
jax.debug=True
jax.prealloc=False
jax.jit=False          # only when you need Python-level execution
jax.debug_nans=True    # only when tracing NaNs is worth the slowdown
agent.* small dimensions from debug or size1m
```

Notes:

- JAX platform, mock-device, preallocation, and many XLA flags must be set before the JAX backend is initialized. Relaunch a fresh process after changing them.
- `jax.debug=True` disables most XLA optimizations through `jax_disable_most_optimizations`.
- `jax.jit=False` maps to `jax_disable_jit=True`; this is much slower but can expose Python assertions.
- `jax.debug_nans=True` can conflict with transfer-guard assumptions and can be very slow. Use it for narrow reproductions.
- For numeric debugging, `jax.compute_dtype=float32` can make failures easier to localize than `bfloat16` or `float16`.

## Platform, Dtype, Preallocation, And Mock Devices

`embodied.jax.internal.setup()` owns JAX setup for the wrapper. Relevant config keys:

| Key | Effect | Debug advice |
|---|---|---|
| `jax.platform` | Updates JAX platform selection. | Use `cpu` for debugging; use the production accelerator only after shape/numeric checks pass. |
| `jax.compute_dtype` | Sets `embodied.jax.nets.COMPUTE_DTYPE`. | `bfloat16` is default; use `float32` for narrow numeric investigations. |
| `jax.prealloc` | Sets `XLA_PYTHON_CLIENT_PREALLOCATE`. | Use `False` when debugging memory contention or CUDA allocation failures. |
| `jax.jit` | Enables/disables JIT. | Disable only for small debug configs. |
| `jax.debug` | Disables most XLA optimizations. | Pair with CPU for readable behavior. |
| `jax.mock_devices` | Adds host-device count flag. | Use for CPU mesh/sharding tests; must be set before backend init. |
| `jax.expect_devices` | Validates device count. | If wrong, wrapper intentionally waits after printing an alert. |
| `jax.policy_devices`, `jax.train_devices` | Device indices selected from local devices. | Ensure indices exist under the selected platform or mock device count. |
| `jax.policy_mesh`, `jax.train_mesh` | Mesh shape string for axes `d,f,t`. | Product after resolving `-1` must equal selected device count. |

`nets.ensure_dtypes()` asserts forward and backward dtypes on many layers. If you see dtype assertions:

1. Confirm `internal.setup()` ran before module construction.
2. Confirm new floating tensors are cast with `nets.cast()` or `.astype(nets.COMPUTE_DTYPE)` before feeding Dreamer layers.
3. Keep scalar losses as `jnp.float32`; `Optimizer` asserts scalar `float32` loss.

## Loss And Metric Localization

DreamerV3 exposes enough metrics to narrow most training failures:

| Metric prefix/key | Component |
|---|---|
| `loss/<obs_key>` | Decoder reconstruction for one observation key. |
| `loss/rew` | Reward head. |
| `loss/con` | Continuation head. |
| `loss/dyn` | RSSM dynamics KL. |
| `loss/rep` | RSSM representation KL. |
| `loss/policy` | Imagined actor loss. |
| `loss/value` | Imagined value loss. |
| `loss/repval` | Optional replay value loss. |
| `dyn_ent` | RSSM prior entropy. |
| `rep_ent` | RSSM posterior entropy. |
| `adv`, `adv_std`, `adv_mag` | Advantage scale before normalization. |
| `rew`, `con`, `ret`, `val`, `tar`, `weight`, `slowval` | Imagined trajectory summaries. |
| `ent/<action_key>` | Policy entropy per action head. |
| `rand/<action_key>` | Entropy normalized by head min/max when available. |
| `opt/grad_norm`, `opt/grad_rms` | Gradient magnitude. |
| `opt/update_rms`, `opt/param_rms` | Optimizer update/parameter magnitude. |
| `opt/grad_scale`, `opt/grad_overflow` | Float16-only dynamic scaling. |

Localization checklist:

1. If `dyn_ent` or `rep_ent` collapses or explodes, inspect RSSM logits, `unimix`, `free_nats`, and stochastic class count.
2. If `loss/<image_key>` dominates, confirm image dtype is `uint8`, image shape is stable, decoder spatial minimum resolution is between 3 and 16, and image values are not pre-normalized floats.
3. If `loss/rew` or `loss/value` is unstable, inspect `symexp_twohot` bins, reward scale, `retnorm`, and `valnorm`.
4. If `loss/policy` is unstable, inspect `advnorm`, `actent`, action entropy metrics, and continuation probabilities.
5. If `opt/grad_norm` becomes non-finite while individual losses look finite, inspect dtype and optimizer gradient scaling; use `float32` compute dtype for a narrow reproduction.

## Loss-Scale And Shape Assertions

`Agent.loss()` asserts:

```text
all loss arrays have shape (B, T) before imagination/replay reductions
final loss key set == config.loss_scales key set after rec expansion
optimizer loss is scalar float32
```

When adding or removing losses:

- Add a scale to `agent.loss_scales`.
- If the new loss is per-imagination start, reduce it to a `[B,K]` or `[B,T]` form before final aggregation.
- If it is a decoder reconstruction for an observation key, let `rec` expansion cover it or explicitly add the key with a scale.
- Return metrics with stable names; avoid reusing existing metric keys for different semantics.

## Checkpoint And PyTree Mismatches

`embodied.jax.Agent.save()` returns:

```python
{'params': params, 'counters': {'updates': int, 'batches': int, 'actions': int}}
```

`load(data, regex=None)` has two modes:

- `regex=None`: full restore. It asserts equal tree shapes before replacing current params.
- `regex='<pattern>'`: filters checkpoint params to keys matching `re.match(pattern, key)`, deletes current arrays for those keys, and loads only that subset through checkpoint sharding functions.

Common mismatch causes:

| Change | Expected symptom | Safer route |
|---|---|---|
| `size1m`/`size*`/`debug` dimension change | Shape mismatch for many kernels/biases. | Use a new logdir/checkpoint, or regex-load only unchanged modules. |
| Changed Ninjax module name/path | Missing or unexpected parameter keys. | Preserve `self.sub(..., name)` paths or write a checkpoint migration. |
| Changed action/observation spaces | Head shape mismatch. | Do not reuse checkpoints across incompatible spaces. |
| Changed policy/value/reward output bins | Head kernel and bias shape mismatch. | New checkpoint or regex excluding changed heads. |
| Changed sharding/mesh only | Checkpoint data may load, but device placement differs. | Let wrapper shard via `load()`; do not manually device-put mismatched shardings. |

Useful regex examples for partial loads:

```text
^(enc|dyn)/        # load encoder and RSSM only
^pol/             # load policy head only
^(enc|dyn|pol)/   # load policy-relevant core, excluding decoder/value/reward
```

Partial loading is not a semantic guarantee. After regex load, run a finite policy smoke and watch loss metrics before long training.

## Ninjax State And Parameter Names

Ninjax parameter/state keys are path-like strings such as:

```text
enc/.../kernel
dyn/dyngru/kernel
pol/mlp/linear0/kernel
opt/state/...
slowval/...
```

Rules for safe edits:

- Use stable `self.sub('<name>', Module, ...)` names.
- Do not create parameters conditionally on data values that may differ between init and apply.
- Do not mutate Ninjax context outside pure/init wrappers unless you understand creation/modify flags.
- `SlowModel` requires `source.values` to be initialized before it can copy parameters; otherwise it raises `no parameters to track`.
- If using custom partition rules, ensure every parameter and every activation callback name matches a rule.

## LayerScan Pitfalls

`embodied.jax.utils.LayerScan(module, count, names=('__call__',))` wraps selected module methods in a scan while managing Ninjax state.

Distilled invariants from the native `LayerScan` apply case:

- A scanned module with `count=L` stores inner created parameters with a leading scan dimension `L`.
- Outer state that is modified inside the scanned call is threaded separately from inner state.
- Created outer state is created outside the scan; created inner state is created inside the scan.
- On apply, changing inner state must have shape `(L, ...)` and update per scanned layer.
- Inputs passed as scan arguments must have a leading dimension of `L`; non-scanned keyword arguments keep their normal shape.

Typical failure modes:

| Symptom | Likely cause |
|---|---|
| Inner parameter lacks leading scan dimension | Parameter was created outside `LayerScan` or method name was not wrapped. |
| Outer counter/state changes once instead of `L` times | State was classified as unchanging or not threaded as modified. |
| Shape mismatch in scanned argument | Argument intended for each layer is missing leading `count` dimension. |
| Randomly identical layer parameters | Seed splitting or creation path was bypassed. |

When debugging, reduce `count`, `B`, and hidden units, disable JIT, and inspect Ninjax context keys after `nj.init()` and one `nj.pure()` apply.

## XLA/CUDA Failures That May Be Model Issues

Before treating an error as an installation problem, try to separate model from backend:

1. Parse the config with `scripts/inspect_model_config.py` and resolve warnings.
2. Run the same model size on CPU/debug if feasible.
3. Turn off preallocation for memory-contention errors.
4. Use smaller `batch_size`, `batch_length`, and `imag_length` to reduce memory.
5. Use `jax.compute_dtype=float32` for debug-only numeric clarity, or lower precision only after confirming stability.
6. If the error mentions transfer guard, avoid host conversions inside JIT; collect metrics after wrapper `_take_outs()`.

If CPU/debug passes but CUDA fails before model code runs, route backend installation/driver repair to `results-ops`. If CPU/debug also fails with shape, dtype, or Ninjax assertions, keep debugging here.
