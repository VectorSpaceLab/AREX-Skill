# DreamerV3 JAX API Reference

This reference lists the model/JAX APIs that future agents most often need when inspecting, extending, or debugging DreamerV3 neural internals.

## Import Roots

The package distribution is `dreamer`; the relevant import roots are:

```python
import dreamerv3
import embodied
import embodied.jax
```

Public JAX exports from `embodied.jax` include:

```python
Agent
DictHead, Head, MLPHead
LayerScan, Normalize, SlowModel
Optimizer
nets, outs, opt
```

## `dreamerv3.agent.Agent`

Construction:

```python
Agent(obs_space, act_space, config)
```

Because `dreamerv3.agent.Agent` subclasses `embodied.jax.Agent`, the actual returned object is the outer JAX wrapper. The inner Dreamer model is stored as `returned_agent.model`.

Inner model methods and properties:

| Member | Contract |
|---|---|
| `policy_keys` | Regex string `^(enc|dyn|dec|pol)/`; controls parameters synced to policy mesh. |
| `ext_space` | Extra train/report spaces: `consec`, `stepid`, and optional replay-context entries. |
| `init_policy(batch_size)` | Returns `(enc_carry, dyn_carry, dec_carry, prevact)`. |
| `init_train(batch_size)` | Same carry contract as `init_policy()`. |
| `init_report(batch_size)` | Same carry contract as `init_policy()`. |
| `policy(carry, obs, mode='train')` | Encodes one step, updates RSSM, samples actions, returns finite diagnostics. |
| `train(carry, data)` | Applies replay context, optimizes `loss()`, updates slow value model, returns replay outs and metrics. |
| `loss(carry, obs, prevact, training)` | Builds world-model, imagination, and optional replay-value losses. |
| `report(carry, data)` | Returns train metrics and optional open-loop reconstructions. |

Private helpers worth knowing when debugging:

| Helper | Use |
|---|---|
| `_apply_replay_context(carry, data)` | Reconstructs previous action sequence and optionally replaces prefix carry from replay. |
| `_make_opt(...)` | Builds AGC + RMS + momentum + optional weight decay + schedule optimizer chain. |
| `imag_loss(...)` | Actor/value loss over imagined trajectories. |
| `repl_loss(...)` | Optional replay value loss. |
| `lambda_return(...)` | Reverse-time lambda return used by both imagined and replay value losses. |

## `dreamerv3.rssm` Modules

### `RSSM`

Constructor:

```python
RSSM(act_space, **kw)
```

Configurable fields include `deter`, `hidden`, `stoch`, `classes`, `norm`, `act`, `unroll`, `unimix`, `outscale`, `imglayers`, `obslayers`, `dynlayers`, `absolute`, `blocks`, and `free_nats`.

Methods:

| Method | Contract |
|---|---|
| `entry_space` | `{'deter': Space(float32, deter), 'stoch': Space(float32, (stoch, classes))}`. |
| `initial(bsize)` | Zero RSSM carry in compute dtype. |
| `truncate(entries, carry=None)` | Takes the last time entry as carry; expects `entries['deter'].ndim == 3`. |
| `starts(entries, carry, nlast)` | Flattens the last `nlast` entries from `[B,T,...]` to `[B*nlast,...]`. |
| `observe(carry, tokens, action, reset, training, single=False)` | Posterior update from encoded tokens and previous actions. |
| `imagine(carry, policy, length, training, single=False)` | Prior rollout using callable policy or provided action sequence. |
| `loss(carry, tokens, acts, reset, training)` | Returns RSSM carry, entries, `dyn`/`rep` KL losses, features, and entropy metrics. |

Feature dictionaries:

```text
carry: {'deter', 'stoch'}
entry: {'deter', 'stoch'}
feat:  {'deter', 'stoch', 'logit'}
```

### `Encoder`

Constructor:

```python
Encoder(obs_space, **kw)
```

Fields: `units`, `norm`, `act`, `depth`, `mults`, `layers`, `kernel`, `symlog`, `outer`, `strided`.

Methods:

| Method | Contract |
|---|---|
| `entry_space` | `{}` for the simple encoder. |
| `initial(batch_size)` | `{}`. |
| `truncate(entries, carry=None)` | `{}`. |
| `__call__(carry, obs, reset, training, single=False)` | Returns `carry`, empty entries, and encoded tokens. |

### `Decoder`

Constructor:

```python
Decoder(obs_space, **kw)
```

Fields: `units`, `norm`, `act`, `outscale`, `depth`, `mults`, `layers`, `kernel`, `symlog`, `bspace`, `outer`, `strided`.

Methods:

| Method | Contract |
|---|---|
| `entry_space` | `{}` for the simple decoder. |
| `initial(batch_size)` | `{}`. |
| `truncate(entries, carry=None)` | `{}`. |
| `__call__(carry, feat, reset, training, single=False)` | Returns `carry`, empty entries, and reconstruction output dict. |

## `embodied.jax.Agent` Wrapper

Options dataclass fields read from `config.jax`:

| Option | Default | Meaning |
|---|---:|---|
| `policy_devices` | `(0,)` | Device indices used by policy inference. |
| `train_devices` | `(0,)` | Device indices used by training/reporting. |
| `policy_mesh` | `-1,1,1` | Mesh shape string for policy axes `d,f,t`. |
| `train_mesh` | `-1,1,1` | Mesh shape string for train axes `d,f,t`. |
| `profiler` | `True` | Enables JAX profiler trace around updates 100-120. |
| `expect_devices` | `0` | If positive and count mismatches, the wrapper prints an alert and waits. |
| `use_shardmap` | `False` | Enables shard-map path with data-axis constraints. |
| `enable_policy` | `True` | If false, `init_policy()` and `policy()` raise. |
| `ckpt_chunksize` | `-1` | Positive byte limit splits checkpoint gather/shard groups. |
| `precompile` | `True` | Compiles train/report at construction. |

Other `config.jax` keys are passed into `embodied.jax.internal.setup()`.

Public wrapper methods:

| Method | Behavior |
|---|---|
| `init_policy(batch_size)` | Multiplies by process count, adjusts for shardmap, initializes policy carry, returns local split carry. |
| `init_train(batch_size)` | Initializes train carry on train mesh. |
| `init_report(batch_size)` | Initializes report carry on train mesh. |
| `policy(carry, obs, mode='train')` | Validates obs keys/finite inputs, puts data on policy sharding, calls compiled policy, asserts finite diagnostics/actions, and returns local carry/actions/outs. |
| `train(carry, data)` | Consumes `seed`, validates data keys, calls compiled train with donated non-policy params, schedules policy-parameter sync, and returns delayed outs/metrics. |
| `report(carry, data)` | Consumes `seed`, calls compiled report, appends `params/summary`. |
| `stream(st)` | Prefetch stream wrapper that checks NaNs, device-puts batches, and adds a JAX seed. |
| `save()` | Gathers params and counters into `{'params': ..., 'counters': ...}`. |
| `load(data, regex=None)` | Restores counters and params; regex mode filters checkpoint keys before loading. |

Checkpoint counters:

- `updates` restores from checkpoint `counters['updates']`.
- `batches` is restored to the update counter so prefetched-but-untrained batches are repeated.
- `actions` restores from checkpoint `counters['actions']`.

## `embodied.jax.internal`

### `setup()`

Signature summary:

```python
setup(
    platform=None,
    compute_dtype=jnp.bfloat16,
    debug=False,
    jit=True,
    prealloc=False,
    mock_devices=0,
    transfer_guard=True,
    deterministic=True,
    autotune=1,
    gpuflags=True,
    tpuflags=False,
    xladump=None,
    debug_nans=False,
    process_id=-1,
    num_processes=1,
    coordinator_address=None,
    compilation_cache=True,
)
```

Effects:

- `platform` updates JAX platform selection.
- `debug=True` disables most XLA optimizations.
- `jit=False` disables JIT.
- `prealloc` sets `XLA_PYTHON_CLIENT_PREALLOCATE`.
- `mock_devices` adds `--xla_force_host_platform_device_count=<N>`.
- `debug_nans=True` enables JAX NaN checks.
- `compute_dtype` string or dtype sets `embodied.jax.nets.COMPUTE_DTYPE`.
- `num_processes > 1` initializes JAX distributed when not using TPU.

Helper APIs:

| Function | Use |
|---|---|
| `get_named_axes()` | Returns active JAX named axes available in the current transformed context. |
| `get_data_axes()` | Returns `('d','f')` only when both axes are active, else `()`. |
| `fetch_async(value)` | Copies leaves to host asynchronously; converts multihost arrays local first. |
| `device_put(value, sharding)` | Multihost-aware `jax.device_put`. |
| `local_sharding(sharding)` | Converts global named sharding to local mesh sharding. |
| `to_local(x)` / `to_global(x, global_sharding)` | Converts array trees between local and global shapes. |
| `move(xs, dst_sharding)` | Moves arrays, using local/global conversion in multihost mode. |
| `mesh(devices, shape, names)` | Builds `jax.sharding.Mesh`; `shape` may contain one `-1`. |
| `grouped_ckpt_fns(params, chunksize)` | Builds compiled gather/shard functions, optionally chunked. |
| `ckpt_fn(params, compile=True)` | Compiles gather-to-mirrored and shard-from-mirrored functions. |

## `embodied.jax.transform`

### `init()`

```python
init(fn, mesh, arg_shardings, param_partition_rules=(),
     act_partition_rules=(), static_argnums=(), dummy_inputs=(),
     print_partition=False)
```

Runs a Ninjax function in creation mode, resolves parameter partition rules, initializes params with sharding, and returns `(params, params_sharding)`.

### `apply()`

```python
apply(fn, mesh, in_shardings, out_shardings, partition_rules=(),
      static_argnums=(), single_output=False, return_params=False,
      donate_params=False, split_rng=True, use_shardmap=False,
      first_outnums=())
```

Wraps a Ninjax-pure function with JAX JIT or shard-map, applies activation sharding constraints through `nets.LAYER_CALLBACK`, optionally returns/donates params, and optionally treats one output as a single non-tuple output.

Partition rule behavior:

- Empty parameter rules default to `[('.*', P())]`.
- Every parameter key must match exactly one rule through first-match search.
- Activation constraints require a matching rule; otherwise an exception is raised.

## `embodied.jax.nets`

Global state:

| Name | Meaning |
|---|---|
| `COMPUTE_DTYPE` | Floating activation dtype set by `internal.setup()`, default `bfloat16`. |
| `LAYER_CALLBACK` | Sharding callback set temporarily by `transform.init/apply()`. |

Utility functions:

| Function | Contract |
|---|---|
| `cast(xs, force=False)` | Casts floating leaves, or all leaves when forced, to `COMPUTE_DTYPE`. |
| `act(name)` | Returns activation: `none`, `mish`, `relu2`, `swiglu`, or a `jax.nn` activation. |
| `init(name)` | Converts initializer names such as `trunc_normal_in` to `Initializer`. |
| `dropout(x, prob, training)` | Ninjax-seeded dropout when training and `prob` non-zero. |
| `symlog(x)` / `symexp(x)` | Symmetric log/exponential transforms. |
| `where(condition, xs, ys)` | Tree-wise broadcasted boolean selection. |
| `mask(xs, mask)` | Tree-wise zeroing where mask is false. |
| `available(*trees, bdims=None)` | Availability mask: finite sentinels for floats/ints, true for uint/bool. |
| `ensure_dtypes(x, fwd=None, bwd=None)` | Custom VJP assertion for forward/backward dtypes. |
| `rms(xs)` | Root-mean-square over tree leaves. |
| `rope(x, ts=None, inverse=False, maxlen=4096)` | Rotary positional embedding for `[B,T,H,D]`. |

Core modules:

| Module | Key contract |
|---|---|
| `Initializer(dist='trunc_normal', fan='in', scale=1.0)` | Supports `zeros`, `uniform`, `normal`, `trunc_normal`, `normed`; computes fan from shape. |
| `Embed(classes, units, shape=())` | Lookup table for discrete inputs; optional combine over event dims. |
| `Linear(units)` | Last-dim linear projection; `units` can be int or tuple. |
| `BlockLinear(units, blocks)` | Grouped linear; input and output sizes must be divisible by `blocks`. |
| `Conv2D(depth, kernel, stride=1)` | NHWC conv; optional manual transposed-style path when `transp=True`. |
| `Conv3D(depth, kernel, stride=1)` | NTHWC conv or transpose. |
| `Norm(impl)` | `none`, `rms`, or `layer`; supports `1em<N>` epsilon suffix. |
| `Attention` | Multi-head attention with optional kv heads, RoPE, q/k norm, dropout. |
| `DictConcat(spaces, fdims, squish=lambda x: x)` | Deterministic sorted concatenation for non-image dict spaces. |
| `DictEmbed(spaces, units)` | Embeds dict observations with onehot or lookup path. |
| `MLP(layers=5, units=1024)` | Linear + norm + activation stack. |
| `Transformer` | Residual transformer block stack. |
| `GRU` | Reset-masked GRU cell/scan. |

## Heads And Output Distributions

### Heads

```python
MLPHead(space, output, **hkw)(x, bdims)
DictHead(spaces, outputs, **kw)(x)
Head(space, output, **kw)(x)
```

Head implementations:

| Output name | Space requirement | Returned output |
|---|---|---|
| `binary` | Classes equal 2 | `outs.Binary`. |
| `categorical` | Discrete space | `outs.Categorical`; exposes `minent=0`, `maxent=log(classes)`. |
| `onehot` | Continuous one-hot-shaped space | `outs.OneHot`. |
| `mse` | Continuous space | `outs.MSE`. |
| `huber` | Continuous space | `outs.Huber`. |
| `symlog_mse` | Continuous space | `outs.MSE` with symlog target squash. |
| `symexp_twohot` | Continuous space | `outs.TwoHot` with symmetric bins. |
| `bounded_normal` | Continuous space | `outs.Normal(tanh(mean), stddev)` with entropy range attributes. |
| `normal_logstd` | Continuous space | `outs.Normal(mean, exp(logstd))`. |

If `space.shape` is non-empty, `Head.__call__()` wraps the output in `outs.Agg` so `.loss()` and `.logp()` aggregate event dimensions and leave only batch dimensions.

### Output base API

Every output object supports:

```python
pred()
loss(target)          # default: -logp(stop_gradient(target)) when not overridden
sample(seed, shape=())
logp(event)
prob(event)           # exp(logp(event))
entropy()
kl(other)
```

Output implementations:

| Class | Notes |
|---|---|
| `Agg(output, dims, agg=jnp.sum)` | Aggregates the last `dims` event dimensions for loss/logp/entropy/KL. |
| `Frozen(output)` | Stops gradients through delegated output methods. |
| `Concat(outputs, midpoints, axis)` | Slices inputs, delegates to multiple outputs, concatenates results. |
| `MSE(mean, squash=None)` | Squared error to optional squashed target; expects floating target. |
| `Huber(mean, eps=1.0)` | Charbonnier/soft Huber loss. |
| `Normal(mean, stddev=1.0)` | Gaussian sample/logp/entropy/KL. |
| `Binary(logit)` | Bernoulli log-prob and samples. |
| `Categorical(logits, unimix=0.0)` | Integer class pred/sample/logp/entropy/KL. |
| `OneHot(logits, unimix=0.0)` | Straight-through one-hot pred/sample; categorical KL. |
| `TwoHot(logits, bins, squash=None, unsquash=None)` | Soft two-hot target loss and numerically symmetric prediction. |

## Optimizer APIs

### `Optimizer`

```python
Optimizer(modules, opt, summary_depth=2)
Optimizer.__call__(lossfn, *args, has_aux=False, **kwargs)
```

Behavior:

1. Wraps `lossfn` to require scalar `float32` loss.
2. Uses `nj.grad()` over the supplied module parameters.
3. Averages gradients across active data axes `('d','f')` when present.
4. Applies float16 gradient scaling when `nets.COMPUTE_DTYPE == jnp.float16`.
5. Updates Ninjax context with `optax.apply_updates()`.
6. Returns metrics under `<optimizer_name>/...`.

Metrics include `loss`, `updates`, `grad_norm`, `grad_rms`, `update_rms`, `param_rms`, and `param_count`; float16 mode also adds `grad_scale` and `grad_overflow`.

### Optimizer transformations

| Function | Meaning |
|---|---|
| `clip_by_agc(clip=0.3, pmin=1e-3)` | Adaptive gradient clipping by parameter norm. |
| `scale_by_rms(beta=0.999, eps=1e-8)` | RMS normalization with bias correction. |
| `scale_by_momentum(beta=0.9, nesterov=False)` | Momentum or Nesterov momentum with bias correction. |

DreamerV3 `_make_opt()` chains AGC, RMS, momentum, optional regex weight decay, learning-rate schedule (`const`, `linear`, or `cosine`), and warmup.

## Utility APIs

### `Normalize`

```python
Normalize(impl, rate=0.01, limit=1e-8, perclo=5.0, perchi=95.0, debias=True)
```

Implementations:

| `impl` | State | `stats()` |
|---|---|---|
| `none` | No variables | `(0.0, 1.0)`. |
| `meanstd` | EMA mean and second moment | Debiased mean and std clamped by `limit`. |
| `perc` | EMA low/high percentiles | Low offset and `(hi-lo)` scale clamped by `limit`. |

`__call__(x, update)` updates when requested and returns `(offset, scale)`.

### `SlowModel`

```python
SlowModel(model, *, source, rate=1.0, every=1)
```

Tracks an exponential moving copy of a Ninjax module. It initializes the target parameters from `source` on first use, then `update()` mixes source into target every `every` steps with `rate`.

### `LayerScan`

```python
LayerScan(module, count, names=('__call__',))
```

Wraps selected callable methods of a Ninjax module in a JAX scan while managing inner/outer Ninjax state. See [debugging-numerics.md](debugging-numerics.md#layerscan-pitfalls) before changing stateful scanned modules.

## Minimal Introspection Snippets

These snippets are safe in an environment where the package is importable; they inspect objects but do not start training.

```python
from dreamerv3.agent import Agent
from dreamerv3.rssm import RSSM, Encoder, Decoder
from embodied.jax import internal, nets, heads, outs, opt, utils

print(Agent.policy_keys.fget)  # property object on the inner model class
print(RSSM.deter, RSSM.stoch, RSSM.classes)
print(nets.COMPUTE_DTYPE)
```

For final config values, prefer the bundled script:

```bash
python scripts/inspect_model_config.py defaults debug size1m
```
