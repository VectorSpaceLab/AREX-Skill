# Control simulation workflows

These procedures are intentionally short and explicit. Run the bundled smoke
first; only then substitute a real plant or training data. The examples below
are recipes, not a request to reproduce the repository's long experiments.

## A. Deterministic open-loop and closed-loop smoke

1. Choose a seed and generate a signal with a local NumPy generator. Record
   `(nsim, d)`, bounds, and the number of samples.
2. Make the state initial value rank-3 `(B, 1, nx)`. Make a time-varying input
   or reference rank-3 `(B, N, F)`.
3. Build a policy node and a plant node. The policy reads the current state and
   current reference; the plant reads the current state and action and emits
   the recurrent state key.
4. Use explicit names and either `nsteps=N` or `nstep_key` pointing at the
   time-bearing input. For a state initialized at one sample, expect `N+1`
   state samples and `N` action samples.
5. Assert keys, shapes, finiteness, and deterministic equality from two fresh
   graph instances. Do not call plotting or a trainer in this smoke.

The bundled `scripts/simulation_smoke.py --run` implements this contract with a
four-step signal, a CPU policy, and a two-node state update. It is safe to run
from any current directory and performs no download, training, or file write.

## B. Select and simulate a PSL system

Use this decision sequence:

1. **Autonomous open loop:** choose an entry from the autonomous registry and
   call `simulate(nsim=small, x0=...)`. There is no control sequence in the
   result. `Pendulum` or `UniversalOscillator` is a useful shape smoke.
2. **Non-autonomous plant:** choose a non-autonomous registry entry, inspect
   `nx`, `nu`, and `ts`, then provide `x0` and a control array with the package's
   extra initial sample convention. For a four-step run, build or slice a
   `(5, nu)` control array and check that `X`, `Y`, and `Time` each contain four
   rows.
3. **Coupled system:** choose `RCNet`, `Gravitational`, or `Boids` only after
   fixing graph size and state layout. Start with NumPy and a tiny `nx`; treat
   adjacency and multi-agent state dimensions as part of the model contract.
4. **Building or recorded data:** use only with a local parameter/data file and
   an explicit data permission. Set a short horizon and avoid constructor paths
   that trigger default statistics or downloads.
5. **Torch backend:** use it when the plant participates in a differentiable
   graph. Compare one short NumPy/Torch result when possible, then assert dtype,
   device, and shape. Do not infer CUDA support from an import alone.

For any plant, write down whether the returned `X` means state or observation,
which time sample is dropped, and whether `U`/`D` has an extra leading sample.
That prevents off-by-one errors when connecting a PSL result to a sequence
training route.

## C. Add a future-reference preview

Use preview when the policy is intentionally designed to consume future-known
values rather than only the current reference.

1. Prepare `r` as `(B, N+1, nr)` if the current value plus all N future values
   are known. If the deployed signal is shorter, decide a terminal padding
   policy instead of silently indexing past the sequence.
2. Build a policy whose input width is `nx + (L+1)*nr` (plus any current
   disturbances). Give it a name such as `policy`.
3. Construct `SystemPreview` with
   `preview_keys_map={'r': ['policy']}`, explicit
   `preview_length={'r': L}`, `nsteps=N`, and an explicit `pad_mode`.
4. Use `pad_mode='replicate'` for a held terminal reference,
   `'constant'` with a documented `pad_constant` for a known terminal target,
   or `'circular'` only for a genuinely periodic signal. Test `i=N-1` and
   `i=N`-adjacent windows.
5. Compare the preview policy's first-step input width with the node's module
   width. A preview window is flattened; it is not a third tensor axis passed
   through automatically.

Preview changes the policy input contract, not the plant contract. Keep loss
and constraint variables aligned with the unflattened trajectory keys returned
by the system.

## D. Add a moving history window

1. Create a `Node` whose callable can consume a dictionary-derived tensor with a
   leading history dimension `(ndelay, B, F)`.
2. Wrap it as `MovingHorizon(node, ndelay=L)` and call it with one-step
   `(B,F)` tensors. On the first call, the current sample is repeated to fill
   the history; subsequent calls shift in the newest sample.
3. Check the returned dictionary and leading dimension. If the downstream node
   expects one `(B,F)` result, explicitly reduce or select a slice in the
   wrapped callable; `MovingHorizon` itself does not promise a reduction.
4. Reset history between episodes. For batched episodes, ensure all history
   entries have the same batch size, dtype, device, and feature width.

## E. Recipe-level differentiable predictive control

DPC is a composition pattern. Keep symbolic objective/constraint construction
in the symbolic-problems route; this route supplies the rollout boundary.

### Training graph

1. Define a discrete differentiable plant
   `x_next = f(x, u[, d])`, or wrap an integrator/PSL-compatible plant. Expose
   `(B,nx)` state and `(B,nu)` action at each node call.
2. Define a bounded policy `u = pi(x, r[, d_obs])`. A policy bound is preferable
   to relying on a later penalty when physical action limits are known.
3. Create `Node(policy, ['x','r'], ['u'], name='policy')` followed by
   `Node(plant, ['x','u'], ['x'], name='plant')`. Add disturbance/observation
   nodes before policy or plant when needed, keeping their outputs explicit.
4. Create `System([policy, plant], nsteps=N, name='cl_system')`. Provide
   training scenarios with `x: (B,1,nx)` and `r: (B,N+1,nref)`; add `d` with
   the plant's required horizon and feature width. The state output is
   `(B,N+1,nx)` and action output `(B,N,nu)`.
5. Define a regulation/tracking objective over `x` and `r`, action magnitude or
   action differences as appropriate, and state/action constraints. Construct
   the `Problem` and trainer through the symbolic-problems/data-training routes.
   Use a tiny batch and a few steps for an integration smoke before any real
   optimization.
6. Train with a short prediction horizon first. Inspect finite losses,
   gradients on policy parameters, and bounds on `u`; then increase horizon or
   dataset size deliberately.

The conceptual DPC objective is to optimize policy parameters through the
unrolled closed-loop map:

```text
initial state/reference/disturbance
       -> policy action u_k
       -> differentiable plant x_{k+1}
       -> policy action u_{k+1}
       -> ... N steps
       -> tracking/action/constraint terms
       -> backpropagation through the rollout
```

### Preview and deployment

For preview DPC, replace `System` with `SystemPreview` and give the policy the
flattened future reference window. Preview training and no-preview training
are different policy input contracts; do not load one policy into the other
without matching its input width.

For deployment, use a longer evaluation rollout only after the short graph is
verified. In a receding-horizon interpretation, compute a horizon of actions
from the current measurement and apply only the first action before reading the
next measurement. The `System` rollout is useful for batched differentiable
training/evaluation; an external control loop is responsible for real-time
I/O, safety interlocks, and actuator timing.

## F. Normalize a PSL trajectory safely

1. Simulate a short representative trajectory before setting statistics.
2. Call the emulator's `set_stats(sim=data)` or construct compatible
   `StandardScaler` objects from mean/std arrays. Add an epsilon to constant
   channels.
3. Normalize a dictionary so `X`, `Y`, `U`, and `D` use their own feature
   statistics; leave `Time` excluded unless time normalization is intentional.
4. Assert that normalization preserves shape/type and that denormalization
   returns the original values within a tolerance. Repeat on the same backend
   and device used by the model.
5. Pass normalized values to a model only after deciding whether its output is
   normalized. Denormalize for physical plots, limits, and downstream plant
   interfaces.

## G. Local recorded-data boundary

For a no-network workflow, create or receive a local CSV/MAT file and validate
it before calling `FileEmulator`:

- columns/arrays use `x`, `y`, `u`, `d` prefixes with numeric suffixes;
- all present variables have equal row counts for one episode;
- `Time` is monotone if supplied; `exp_id` is consistent if episodes are
  interleaved;
- at least `X` or `Y` is present, and control/disturbance widths match the model;
- the requested `nsim` leaves enough rows after the selected starting index.

Use `FileEmulator(path=local_file)` for the smoke. A registry system without a
local path may download data, and building systems may need external parameter
files; stop and report that prerequisite rather than falling back to a hidden
network call.
