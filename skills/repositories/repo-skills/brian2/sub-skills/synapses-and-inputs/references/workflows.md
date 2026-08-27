# Synaptic and input workflows

## 1. Define, connect, initialize, run

Use this order for a normal event-delivery path:

```python
P = SpikeGeneratorGroup(2, [0], [1*ms])
G = NeuronGroup(2, "dv/dt = -v/(10*ms) : 1")
S = Synapses(P, G, model="w : 1", on_pre="v_post += w", delay=0.2*ms)
S.connect(i=[0], j=[1])
S.w = 0.5
run(2*ms)
```

The constructor validates the model/pathway and creates no edges. The
connection call creates the dynamic arrays and only then can `S.w`, `S.delay`,
`S.i`, or `S.j` be indexed. If edges are added in multiple calls, assign state
only after the final relevant connection call, or deliberately assign each
new range.

For a deterministic check, choose a `dt` that represents every intended delay,
make the source times and delay multiples of it, and assert target state or
spike times with a tolerance of less than one timestep. A delay smaller than
the source clock is rounded by the event queue and is not a way to obtain
sub-timestep timing.

## 2. Structured connectivity choices

- Known edge list: `connect(i=np.array(...), j=np.array(...))`.
- Dense graph or no-autapse graph: `connect()` or
  `connect(condition="i != j")`.
- One-to-one: `connect(j="i")`; verify source/target sizes and direction.
- Local/generator pattern: `connect(j="k for k in range(max(i-1, 0), min(i+2, N_post))", skip_if_invalid=True)`.
- Random graph: use `condition=...` and scalar or expression `p`, or use
  `sample(..., p=...)`/`sample(..., size=...)` generator syntax.

Seed the Brian/random state when reproducibility matters, and assert structural
properties (edge count, no self edge, incoming/outgoing count) before running.
For `n > 1`, declare `multisynaptic_index` if later indexing by connection
number or assigning distinct delays is required.

After the graph is complete, initialize state with synaptic indices or
pre/post state as needed:

```python
S.w["i > j"] = "exp(-(i-j)**2 / width**2) * w0"
S.w["i <= j"] = 0 * w0
```

For a matrix export, allocate an `(N_pre, N_post)` array, fill it with a
sentinel such as `np.nan`, and assign `W[S.i[:], S.j[:]] = S.w[:]`. This is a
sparse representation: absent pairs have no synaptic value. Do not retain a
`S[...]` subgroup across later `connect` calls; create it after all connection
growth. Keep the expression's units and namespace with the units/equations
route.

## 3. STDP with event-driven traces

A standard pair-based pattern is:

```python
S = Synapses(pre, post, """
    w : 1
    dApre/dt = -Apre/taupre : 1 (event-driven)
    dApost/dt = -Apost/taupost : 1 (event-driven)
""", on_pre="""
    v_post += w
    Apre += dApre
    w = clip(w + Apost, 0, wmax)
""", on_post="""
    Apost += dApost
    w = clip(w + Apre, 0, wmax)
""")
S.connect(...)
S.w = "rand() * wmax"
```

Keep trace units dimensionless or explicitly matched. Event-driven traces are
updated immediately before the pathway code at the event time; they are not
clocked traces suitable for reading every step. If a trace depends on a
clock-driven or summed differential variable, Brian rejects the dependency;
use a compatible clock-driven formulation or an explicit `lastupdate` rule.
Clamp weights after each update and test both pre-before-post and post-before-
pre timing. For recurrent networks, exclude autapses intentionally and test
that every pathway is attached to the intended event.

## 4. Replay output spikes as input

Use an explicit `Network` when the replay source and synapses are created after
an initial run; the magic network rejects a mixture of previously simulated and
new objects. For example:

```python
mon = SpikeMonitor(source)
net = Network(source, target, syn, mon)
net.run(trial)
replay = SpikeGeneratorGroup(source.N, mon.i, mon.t + trial, dt=defaultclock.dt)
R = Synapses(replay, target, on_pre="v_post += 1")
R.connect(j="i")
net.add(replay, R)
net.run(trial)
```

Use `mon.i` as integer indices and `mon.t + trial` as a seconds quantity.
Offset times into the next run; do not feed the original absolute times again,
or they will be in the past and ignored. If the replay group already exists,
call `set_spikes` between runs and ensure its schedule is changed before the
next `run`. Preserve sorting (default sorting is safest) and ensure no neuron
has two events in one replay bin. When comparing output, account for the
source threshold/synapse scheduling slot and the configured delay; use a
SpikeMonitor in the recording route rather than assuming same-step effects.

## 5. Poisson and sampled inputs

Choose the least detailed source that answers the experiment:

1. `PoissonGroup` + `Synapses` if event identities, delays, or plasticity matter.
2. `PoissonInput` if only independent aggregate drive matters and all inputs
   share one target, rate, and weight.
3. `TimedArray` inside equations or as a Poisson rate expression for a fixed
   sampled schedule.
4. `run_regularly`/`run_at` for explicit state changes.

For a time-varying Poisson rate, put a unit-correct `TimedArray` in the rate
expression, e.g. `PoissonGroup(2, rates="rate_schedule(t, i)")` for 2-D data.
Validate the array's time-first shape and sample interval before running. A
high rate relative to `dt` must be split over more Poisson units if individual
spikes are needed; `PoissonInput` is often preferable for aggregate drive.

## Validation checklist

- source/target events exist and target variables have matching units;
- `connect(...)` was called and `len(S)`/`S.i[:]`/`S.j[:]` are as expected;
- all state and delays were assigned after connection creation;
- delay, group `dt`, and input schedule use compatible time units;
- event-driven dependencies are independent and STDP order is tested;
- replay times are offset to the current run and sorted/binned safely;
- input choice preserves the required identity, rate variability, and timing;
- monitors and device/standalone behavior are handed to recording/codegen.
