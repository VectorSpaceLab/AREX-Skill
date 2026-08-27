# Modeling workflows

These recipes are small, deterministic, and plotting-free. They assume Brian2
2.9.0 is installed in Python >=3.12. Use an explicit `Network` while
assembling a model so object ownership and validation are visible.

## 1. Define, initialize, validate, run

```python
from brian2 import Network, NeuronGroup, ms

model = '''
    dv/dt = (drive - v) / tau : 1
    tau : second
    drive : 1
'''
group = NeuronGroup(
    3, model, threshold='v > 1', reset='v = 0',
    refractory=1*ms, method='euler', dt=0.1*ms,
    namespace={},
)
group.tau = [5, 6, 7] * ms
group.drive = 1.4
group.v = 0
net = Network(group)
net.run(0*ms, namespace={})  # force early equation/namespace validation
net.run(2*ms, namespace={})
assert net.t == 2*ms
```

A zero-duration run checks deferred identifier, unit, threshold, reset, and
code-object setup without spending simulation time. Follow it with a tiny
positive run and assert a state change or event count.

## 2. Heterogeneous parameters and subgroup views

Declare per-neuron values in the model and assign arrays with matching length:

```python
from brian2 import NeuronGroup, ms

population = NeuronGroup(6, 'dv/dt = (drive-v)/tau : 1\n'
                         'drive : 1\n tau : second',
                         method='euler', dt=0.1*ms, namespace={})
population.drive = [1.2, 1.3, 1.4, 1.5, 1.6, 1.7]
fast = population[:3]
slow = population[3:]
fast.tau = 1*ms
slow.tau = 3*ms
fast.v = 0.1
slow.v = '0.2 + 0.01*i'
assert all(population.tau_[:3] == 0.001)
```

Views share storage. `fast.i` starts at zero and is subgroup-relative; do not
use it as a parent absolute index. A non-contiguous selection such as
`population[[0, 2]]` cannot be represented as a subgroup; use a parent
parameter and mask assignment instead.

## 3. Threshold, reset, and refractory behavior

Choose whether state continues evolving during refractoriness:

```python
model = '''
    dv/dt = (drive-v)/tau : 1 (unless refractory)
    dw/dt = -w/tau_w : 1
    drive : 1
    tau : second
    tau_w : second
'''
group = NeuronGroup(
    1, model, threshold='v > 1', reset='v = 0; w += 0.2',
    refractory=2*ms, method='euler', dt=0.1*ms,
    namespace={},
)
group.drive = 2
group.tau = 1*ms
group.tau_w = 10*ms
group.v = 0
group.w = 0
```

Without `(unless refractory)`, `v` continues to integrate but threshold
crossings are ignored. With it, only the marked derivative is clamped; `w`
continues to evolve. For heterogeneous intervals declare `ref : second`,
assign one value per neuron, and use `refractory='ref'`. A boolean condition
such as `refractory='v > 1'` means “remain refractory while true”.

## 4. Custom events and ordering

Use custom events for model-level state transitions that are not the default
spike:

```python
from brian2 import Network, NeuronGroup, ms

group = NeuronGroup(
    2, 'x : 1\n event_count : integer',
    events={'high': 'x > 0.8'}, namespace={},
)
group.x = [0.9, 0.0]
group.run_on_event('high', 'event_count += 1')
net = Network(group)
net.run(0*ms, namespace={})
```

A custom condition is checked by default after thresholds; attached code runs
after resets. Conditions are level-triggered, so a condition that stays true
can fire on every scheduled check; they are not edge detectors. Use a latch,
reset the condition, or a narrow time window when the intended behavior is one
side effect per crossing. `set_event_schedule` and
`run_on_event(..., when=..., order=...)` should be used only when same-timestep
ordering is part of the model contract. Keep event conditions boolean and make
state side effects explicit. Event monitors and synaptic `on_event` pathways
are separate concerns.

## 5. Periodic state updates

Use `run_regularly` for abstract code at a regular time:

```python
group.run_regularly(
    'drive = 1 + 0.1*sin(2*pi*t/(10*ms))',
    dt=1*ms, when='start', order=0,
)
```

This is compiled Brian code, not a Python callback. Use a compatible clock or
explicit `dt`; do not put imports, comprehensions, object methods, filesystem
operations, or network calls in the string. A group-wide runner can write a
shared variable; a per-spike reset cannot safely treat that same variable as a
vector.

## 6. Shared and linked data flow

Use `(shared)` for one live scalar consumed by all cells:

```python
from brian2 import NeuronGroup, ms

group = NeuronGroup(
    4,
    'input : 1 (shared)\n'
    'dv/dt = (input-v)/tau : 1\n'
    'tau : second',
    method='euler', dt=0.1*ms,
)
group.input = 0.5
group.tau = 10*ms
```

Use `(linked)` when a receiving group should see source storage live:

```python
import numpy as np
from brian2 import NeuronGroup
from brian2.core.variables import linked_var

source = NeuronGroup(2, 'x : 1', namespace={})
receiver = NeuronGroup(4, 'x_source : 1 (linked)', namespace={})
source.x = [0.2, 0.8]
receiver.x_source = linked_var(source.x, index=np.array([0, 0, 1, 1]))
assert np.allclose(receiver.x_source[:], [0.2, 0.2, 0.8, 0.8])
source.x = [0.3, 0.9]
assert np.allclose(receiver.x_source[:], [0.3, 0.3, 0.9, 0.9])
```

Same-size links map one-to-one and a size-one or shared source maps one-to-all.
For unequal non-scalar sizes, the index must be one-dimensional, integer,
receiver-length, and in range. Check dimensions before trying to debug an index.

## 7. Namespace-safe construction

Choose one deliberate owner for external names:

```python
from brian2 import Network, NeuronGroup, ms

# Group-owned external scalar
owned = NeuronGroup(1, 'dv/dt = -v/tau : 1',
                    namespace={'tau': 10*ms}, method='euler')
Network(owned).run(0*ms, namespace={})

# Run-owned external scalar
run_owned = NeuronGroup(1, 'dv/dt = -v/tau : 1', method='euler')
Network(run_owned).run(0*ms, namespace={'tau': 10*ms})

# Model-owned heterogeneous parameter
model_owned = NeuronGroup(1, 'dv/dt = -v/tau : 1\n tau : second',
                          method='euler', namespace={})
model_owned.tau = 10*ms
Network(model_owned).run(0*ms, namespace={})
```

Do not leave an incomplete explicit namespace at run time or silently depend on
caller locals. Competing group/run/implicit values can produce warnings; remove
the ambiguity unless precedence is an intentional part of the experiment.

## 8. Validation and handoff gate

1. Inspect equation names and flags; confirm all symbols have an owner.
2. Assign every state with compatible units and shapes; inspect subgroup views.
3. Run an explicit network for `0*ms` with a deliberate namespace.
4. Run a tiny positive duration and assert state, custom-event, spike, or
   refractory behavior without relying on a plot.
5. For a link, mutate the source and assert the receiver changes through the
   mapping. For a shared value, verify all cells consume one scalar.
6. Hand off synapses, monitors, run lifecycle, device choice, and target-specific
   compiler work to their owning routes after this gate passes.
