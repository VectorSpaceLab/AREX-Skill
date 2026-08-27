# Synapses and input API reference

This reference distills the Brian2 2.9.0 public user documentation and the
runtime implementation. It is an operating reference, not a mirror of package
source. Examples assume `from brian2 import *` and, where needed, `numpy as np`.
Use physical units on all dimensional values.

## `Synapses`

```python
S = Synapses(source, target=None, model=None, on_pre=None, on_post=None,
             delay=None, on_event="spike", multisynaptic_index=None,
             dt=None, clock=None, order=0, method=("exact", "euler", "heun"))
```

- `source` must emit the selected event and `target` defaults to `source`.
- `model` is an equation string or `Equations`; ordinary parameters and
  differential equations are synapse-specific (one value per connection).
- `on_pre` runs for every source event on the matching synapses. `on_post`
  runs for every target event. A string creates the default `pre`/`post`
  pathway; a dictionary creates named pathways, each with its own delay and
  `order`.
- A bare target variable in `on_pre` is interpreted as postsynaptic in the
  usual case; use `v_post`, `v_pre`, or another explicit suffix when clarity or
  self-connections require it. Synaptic variable names must not collide with
  pre/post variable names.
- `delay` accepts a scalar time for a pathway or a mapping from pathway names
  to scalar times. For per-synapse delays, connect first and assign
  `S.delay`/`S.pre.delay` (or a string expression) afterward. Delay values must
  have time units and are quantized to the source pathway clock.
- `on_event` can select a custom event name, or map pathway names to event
  names. The corresponding source/target group must define that event; setting
  `on_event` does not create the event. For example, map
  `{"pre": "spike", "gpath": "gspike"}` when `gspike` is an event declared
  by the source group. Define the event and any `run_on_event` side effects in
  the modeling route, then attach the matching synaptic pathway here.
- `multisynaptic_index="k"` adds `k`, which numbers parallel synapses for each
  `(i, j)` pair and enables third-axis indexing.

### Creating connections

`S.connect(...)` is separate from construction. Main forms:

```python
S.connect()                         # all pairs
S.connect(condition="i != j")      # conditional pair search
S.connect(i=[0, 1], j=[2, 0])       # paired arrays, broadcastable 1-D
S.connect(j="i")                   # one-to-one map from each source
S.connect(j="k for k in range(i+1)")
S.connect(condition="i != j", p=0.1)
S.connect(j="i", n=2)              # two parallel synapses per pair
```

- `condition` cannot be combined with explicit `i` or `j`. It may reference
  `i`, `j`, pre/post state, `N_pre`, and `N_post`.
- `p` is a dimensionless probability; use expressions for pair-dependent
  probabilities. `n` is the number of synapses per accepted pair and can be an
  integer expression for string/generator forms.
- Generator syntax is `j='EXPR for k in range(...) if COND'` or the analogous
  `i=...`. Supported iterators are `range` and `sample`; `skip_if_invalid=True`
  skips out-of-range generated indices rather than raising.
- For a one-to-one pattern, `j='i'` loops over sources and is valid whenever
  each source has a corresponding target; the reverse `i='j'` has the analogous
  target-driven constraint.
- Prefer paired arrays for a known sparse list, mapping/generator forms for
  structured sparse patterns, and condition forms when most pairs qualify.
  Probabilistic pair-dependent patterns can require work proportional to all
  candidate pairs.

### State, indices, and counts

After `connect`, the following are available per synapse: `i`, `j`, `N`,
`N_incoming`, `N_outgoing`, and any declared variables. The per-neuron views
`N_incoming_post` and `N_outgoing_pre` include zero for unconnected neurons;
the per-synapse `N_incoming` and `N_outgoing` views only have entries for
existing synapses. Synaptic equations and pathway code use the unsuffixed
per-synapse names. Examples:

```python
S.w = 0.5
S.w[0, :] = 0.25
S.w["i != j"] = "clip(w, 0, 1)"
S.w[S[0, :]] = 0.1
S.w[:, :, 1] = 0.2       # only with multisynaptic_index
```

Two-dimensional indexing uses source and target neuron indices; a one-index
form is a raw synapse index. A `SynapticSubgroup` is a snapshot of synapse
indices and must not be retained across later connection growth. State
assignments and delay assignments always address currently existing synapses.
`S.i[:]` and `S.j[:]` are useful for converting the sparse representation to a
matrix; absent pairs have no stored value.

## Event pathways and numerical updates

`on_pre`/`on_post` code can contain multiple statements, random draws, clipped
assignments, and references to synaptic or connected-group variables. Pre
pathways have default order `-1`, post pathways `+1`; explicitly set a named
pathway's `.order` when two same-delay pathways need a guaranteed order.

A differential synaptic equation without a flag is treated as clock-driven and
may emit a performance warning. Use `(clock-driven)` when continuous updates
are intended, or `(event-driven)` for independent one-dimensional linear
traces that only need updating when a pathway fires:

```python
model = """
    w : 1
    dApre/dt = -Apre/taupre : 1 (event-driven)
    dApost/dt = -Apost/taupost : 1 (event-driven)
"""
```

Brian updates event-driven traces analytically using elapsed time since the
last event (`lastupdate`) before running pathway code. Event-driven equations
must be independent of incompatible clock-driven or summed differential state;
otherwise use clock-driven equations or write an explicit elapsed-time update
in the event code with a declared `lastupdate : second`.

A summed equation connects a synaptic expression to a parameter in either
connected group. The suffix selects the side:

```python
post = NeuronGroup(2, "gtot : 1")
S = Synapses(pre, post, "g : 1\n gtot_post = g : 1 (summed)")
```

A `_pre` form writes a parameter on the source group instead. The selected
group parameter must already exist, have matching dimensions, and may not
already be the summed target of another `Synapses` object. A summed target is
updated from the current synaptic values each simulation step; it is not an
alternative to an `on_pre` event update. Use separate target parameters and
combine them in the target model when multiple synaptic sources must contribute.

## Inputs

### `PoissonGroup`

```python
P = PoissonGroup(N, rates, dt=None, clock=None, when="thresholds", order=0)
```

`rates` is a scalar, an `N`-element rate array, or a string expression
reevaluated each time step. Rates need Hz units and cannot safely represent a
substantial chance of multiple spikes per neuron per step: the threshold is
conceptually `rand() < rates*dt`. Split a very high aggregate rate across
multiple lower-rate units when individual events are needed. Use `Synapses(P,
...)` to deliver the events.

### `PoissonInput`

```python
P = PoissonInput(target, target_var, N, rate, weight,
                 when="synapses", order=0)
```

This directly adds a binomial/normal-approximated count of independent input
events to one target variable for every target neuron. `N` is the number of
identical independent inputs; `rate` is a nonnegative scalar Hz rate and
`weight` is a scalar quantity or a target-context expression with matching
units. It is more efficient than materializing a `PoissonGroup` when individual
spikes are not needed, but it does not provide per-input spike identities. A
single object uses one constant rate for every neuron in its target selection;
use target subgroups or multiple `PoissonInput` objects when rates or weights
must differ between populations. A string weight can still vary with target
context. It captures the target group's `dt` at construction; changing that
`dt` afterward is unsupported.

### `SpikeGeneratorGroup`

```python
G = SpikeGeneratorGroup(N, indices, times, period=0*second,
                        dt=None, clock=None, sorted=False)
G.set_spikes(indices, times, period=0*second, sorted=False)
```

`indices` and `times` must have equal length; indices are in `[0, N)`, times are
nonnegative and carry seconds. By default Brian sorts by time then neuron.
`sorted=True` promises that ordering and avoids a copy in runtime mode. A
nonzero `period` repeats the schedule, must exceed the largest spike time, and
must be an integer multiple of the group's `dt`. A neuron may not spike more
than once in one timestep, although different neurons may share a bin. A spike
at an exact timestep is binned into that step; events earlier than the current
run start are ignored with a warning. In C++ standalone, defer inspection that
depends on created synapse indices or runtime arrays until after the run; this
route's object-indexing conveniences are runtime-only.

### `TimedArray`

```python
stim = TimedArray(values, dt=sample_dt)
stim(t)          # 1-D values
stim(t, i)       # 2-D values, rows are time and columns are indices
```

Only one- and two-dimensional arrays are supported. The first dimension of a
2-D array is time. Values are held by sample interval (`x[k]` for `k*dt <= t <
(k+1)*dt`) and clamped to the first/last value outside the supplied interval.
The time argument has seconds; an indexed call requires a valid second-axis
index. Align sample `dt` with the consuming group's clock where possible. A
non-integer time-grid ratio can prevent constant-over-step optimization and
may change exact-integration assumptions.

### Other input operations

For explicit state changes, `Group.run_regularly(code, dt=...)` runs code on a
regular clock and `Group.run_at(code, times=...)` runs at specified times. A
`NetworkOperation` can express arbitrary Python logic in runtime modes, but
should be included explicitly in an explicit `Network` and is not compatible
with C++ standalone. These are input/execution boundaries; keep scheduling and
device policy with their owning routes.
