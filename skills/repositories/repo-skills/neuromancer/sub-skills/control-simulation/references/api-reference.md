# Control and simulation API contract

This reference describes the public behavior needed to assemble short rollouts
without reopening package source. Examples use `torch.Tensor` for differentiable
rollouts and `numpy.ndarray` for ordinary PSL simulation.

## 1. Node and dictionary contracts

```python
Node(callable, input_keys, output_keys, name=None)
```

- `input_keys` and `output_keys` are lists of strings, or symbolic variables
  whose `.key` is used. The callable receives positional tensors in exactly
  `input_keys` order.
- A callable normally consumes `(batch, features)` tensors and returns either
  one tensor or a tuple of tensors. A non-tuple is treated as one output. The
  result is zipped with `output_keys`; a shorter result silently omits trailing
  keys, so assert output arity in new code.
- Missing input keys raise `KeyError`. Extra dictionary keys are ignored by the
  node. The callable is not introspected for dimensions.
- `name` is the graph identity. Give every node in one `System` a non-empty,
  unique name. `System` assigns `node_1`, `node_2`, ... to unnamed nodes, but
  preview maps and diagnostics are safer with explicit names.
- `freeze()` and `unfreeze()` delegate `requires_grad` changes to parameters of
  the callable. Plain Python lambdas have no parameters and remain valid for
  deterministic smoke tests.

## 2. System rollout

```python
System(nodes, name=None, nstep_key='X', init_func=None, nsteps=None)
```

`System` is an ordered, dictionary-connected rollout graph. Each node is called
once per step, in list order.

### Input and output shapes

- Initial data is a dictionary. Tensor values used by a rollout are normally
  three-dimensional `(B, T, F)`, where `B` is batch, `T` is time, and `F` is
  feature/state width. The node sees the current slice `data[key][:, i]`, which
  is `(B, F)`.
- If `nsteps` is supplied, exactly that many node passes are made. Otherwise
  the system reads `data[nstep_key].shape[1]`; the default key is `X`.
- `init_func(data) -> data` is called once before the loop. Use it to establish
  missing initial-state keys or turn a one-dimensional/single-step value into
  `(B, 1, F)`. It must return a dictionary, not a bare tensor.
- `cat` appends a newly produced `(B, F)` value at a new time index. A key not
  present in the initial dictionary starts at one time sample. A key already in
  the dictionary retains its supplied history and then receives appended
  predictions. Consequently a recurrent state initialized at `T=1` has
  `T=nsteps+1` after a rollout, while a reference supplied for the whole
  horizon keeps its original sequence length.
- The returned dictionary includes the original inputs and generated keys. A
  typical closed loop has `X: (B, N+1, nx)`, `U: (B, N, nu)`, and a supplied
  reference `R: (B, N, nr)` or `(B, N+1, nr)`.
- `nstep_key` is only the horizon-inference key. It does not have to be the
  state key; use `nstep_key='R'` when the state is one step and a reference
  supplies the horizon. With `nsteps=None`, a missing key or a two-dimensional
  value fails before a useful rollout; make the convention explicit.

### Graph and recurrence rules

Place a producer before a consumer in `nodes`. A one-step dependency such as
`policy: X -> U` followed by `plant: (X, U) -> X` is valid. A same-key output
is a recurrent feedback value and is appended after the current slice. An
invalid ordering can construct a graph but generally raises `KeyError` during
forward. Names are intended to be unique; duplicate names can collide in the
pydot graph and in preview maps even if construction does not catch every
case. Distinct nodes should also have non-conflicting output semantics;
accidental duplicate keys are easy to mistake for intended recurrence.

`show()` is optional visualization and may need a Graphviz executable. Graph
construction and tensor rollout do not require plotting output; do not make a
plot a runtime gate.

## 3. MovingHorizon

```python
MovingHorizon(module, ndelay=1, history=None)
```

This wrapper adapts a single-step dictionary interface to a module that expects
a short time stack.

- `module` must expose `input_keys` and `output_keys` (a `Node` is the normal
  choice). Its inputs are dictionaries whose values have shape
  `(ndelay, B, F)`.
- On each call, the wrapper appends every current `(B, F)` input to its mutable
  `history`, repeats the first sample `ndelay` times when history was empty,
  and stacks the last `ndelay` samples.
- The result is the module's output dictionary. A typical output value is
  `(ndelay, B, F_out)` when the wrapped callable applies independently to the
  leading stack dimension; do not assume the wrapper reduces time to one step.
- `history` may be supplied as `{key: [tensor, ...]}` with one 2-D tensor per
  prior sample. Supply all module input keys and compatible batch/device/dtype.
- The history persists across calls and is not automatically truncated beyond
  selecting the last `ndelay`. Reinstantiate, clear, or explicitly replace it
  between unrelated episodes. Do not share one wrapper across independent
  batches unless that statefulness is intended.

## 4. SystemPreview

```python
SystemPreview(
    nodes, preview_keys_map={}, preview_length=None,
    pad_mode='circular', pad_constant=0.0,
    name=None, nstep_key='X', init_func=None, nsteps=None
)
```

`preview_keys_map` maps a source variable to the node names that should receive
its future window, for example `{'r': ['policy']}`. At step `i`, a mapped node
gets `data[r][:, i:i+1+L, :]`, where `L=preview_length['r']`, padded at the end
if necessary, then flattened to `(B, (L+1)*F)`. The first value is the current
sample; future values follow in time order. Unmapped inputs receive only
`data[key][:, i]`.

- Use explicit `preview_length` for every mapped variable. The implicit default
  uses `nsteps`; with horizon inference or a missing `nsteps`, that default is
  not a safe contract.
- Use explicit node names in `preview_keys_map`. Automatically assigned names
  are easy to mismatch.
- Supported padding modes follow PyTorch functional padding: `replicate`,
  `circular`, `constant`, and `reflect`. `pad_constant` is used only for
  `constant`. Choose padding deliberately: `replicate` holds the last known
  reference, `constant` makes the terminal assumption visible, `circular`
  wraps a periodic sequence, and `reflect` mirrors values but has length
  restrictions.
- Preview inputs must be rank-3 `(B,T,F)` and contain the current step. A
  policy with preview length `L` must be built for `F*(L+1)` preview features
  in addition to its other current inputs. Padding is applied before slicing;
  test the final two steps, not only the first step.

## 5. PSL registry and backends

`neuromancer.psl.systems` is the merged registry of 46 named systems in the
verified package. It combines autonomous, non-autonomous, building-envelope,
and coupled-system registries. The lower-level registries are useful when a
category matters; coupled examples include `RCNet`, `Gravitational`, and
`Boids`. Select by name, inspect the callable signature, and prefer a small
explicit constructor rather than assuming every entry has identical parameters.

### Emulator base behavior

`EmulatorBase(exclude_norms=['Time'], backend='numpy', requires_grad=False,
seed=59, set_stats=True)` supports `backend='numpy'` and `backend='torch'`.
The base class owns a seeded NumPy generator, parameters, optional statistics,
and normalization helpers. `set_stats=True` can run a default simulation while
constructing an emulator; use `set_stats=False` for a structural smoke and
supply a short simulation explicitly when statistics are required.

- `ODE_Autonomous.simulate(nsim=None, Time=None, ts=None, x0=None)` returns
  `{'Y', 'X', 'Time'}` with `nsim` recorded rows (the integrator also uses an
  initial point internally). `forward(x, t)` is a one-step compatibility
  callable for a `System`.
- `ODE_NonAutonomous.simulate(nsim=None, Time=None, ts=None, x0=None, U=None)`
  returns `{'Y', 'X', 'U', 'Time'}`. Controls are time-indexed through an
  interpolating wrapper; when supplying controls, follow the package convention
  of providing the extra initial sample (`U[:nsim+1]`) and verify the resulting
  output length. `forward(x, u)` is a one-step plant callable.
- A non-autonomous model may expose `D`, `Dhidden`, or other domain-specific
  fields. Building-envelope models return disturbances and use a discrete
  state update; do not force every emulator into the ODE signature.
- Backend casting generally returns `float32` tensors or arrays. NumPy and CPU
  Torch are the verified comparison path. A Torch backend can support
  differentiable parameters, but external interpolation and some model code
  may materialize NumPy values. Treat GPU execution as optional and unverified;
  check device, dtype, and host/device conversion before claiming it.

A minimal autonomous CPU check is conceptually:

```python
from neuromancer.psl.nonautonomous import VanDerPolControl
plant = VanDerPolControl(backend='numpy', seed=7, set_stats=False)
short = plant.simulate(nsim=4, x0=plant.x0, U=plant.U[:5])
assert short['X'].shape[0] == 4
```

For a differentiable closed loop, wrap a compatible plant `forward` in a
`Node` and keep its state and control tensor shapes `(B,F)` at each call.

## 6. Signals and perturbations

The preferred `neuromancer.psl.signals` registry contains `walk`, `noise`,
`step`, `periodic` (including sine/square/sawtooth partials), `spline`,
`sines`, `arma`, `prbs`, `beta`, `beta_walk_mean`, and
`beta_walk_max_step`. Common signatures are:

```python
step(nsim, d, min=0., max=1., randsteps=30, values=None, rng=...)
periodic(nsim, d, min=0., max=1., periods=30, form='sin', phase_offset=False, rng=...)
noise(nsim, d, min=0., max=1., sigma=0.05, bound=True, rng=...)
```

Each returns a floating NumPy array of shape `(nsim, d)` when inputs are valid.
Use a local `np.random.default_rng(seed)` for reproducibility, and pass
per-dimension 1-D bounds when channels differ. Verify `min <= values <= max`
for bounded signals. `neuromancer.psl.perturb` contains older profile helpers
with different naming and seeding conventions; do not mix their APIs with the
preferred lower-case signal registry without checking shape and reproducibility.

## 7. Normalization

`StandardScaler(stats)` expects `stats` with `mean` and `std`. `normalize` and
`denormalize` accept either a NumPy/Torch value plus one scaler, or a dictionary
plus `{key: scaler}`. Rank greater than two is flattened over leading dimensions
and reshaped back, preserving the value type. Dictionary keys absent from the
normalizer map pass through unchanged. Keep non-statistical time keys in
`exclude_norms`, and add a small epsilon to zero standard deviations before
transforming constant channels. Use matching CPU/device types; a scaler built
from CPU statistics is not evidence of GPU-safe normalization.

## 8. Local files and external models

`FileEmulator` accepts a local `.csv` or `.mat` path, or a registered external
system. CSV columns use exact prefixes `x<number>`, `y<number>`, `u<number>`,
`d<number>` and may include `Time` and `exp_id`; MAT files use corresponding
arrays. At least one of `X`, `Y`, `U`, or `D` must be present. Missing `X` or `Y`
is mirrored from the other. A local file is the safe boundary for a smoke;
validate its rows, feature widths, and episode IDs before constructing the
emulator.

`BuildingEnvelope` and registry-backed file systems may call a download helper
for parameter/data files and may allocate long default horizons. They also need
domain-specific `.mat`/recorded data. Do not invoke these paths in a no-network
or no-data run. State the required file, source permission, cache policy, and
short horizon first. The package imports `requests` from its PSL base module,
while some distribution metadata may not list it; treat a missing import as an
environment/version issue, not as a reason to add hidden network behavior.
