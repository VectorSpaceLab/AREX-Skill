# Modeling API reference

This reference covers the Brian2 2.9.0 modeling surface for Python >=3.12.
Examples assume Brian2 is installed and use imports such as
`from brian2 import Network, NeuronGroup, ms, mV, Hz, second`.

**Evidence basis:** The API and behavior notes below were checked against the
Brian2 2.9.0 public topics *Models*, *Refractoriness*, *Custom events*, and
*Functions*, plus the installed 2.9.0 runtime. The named public topics are
provenance only; they are not runtime dependencies.

## `NeuronGroup`

The constructor is:

```python
NeuronGroup(
    N, model, method=('exact', 'euler', 'heun'), method_options=None,
    threshold=None, reset=None, refractory=False, events=None,
    namespace=None, dtype=None, dt=None, clock=None, order=0,
    name='neurongroup*', codeobj_class=None,
)
```

- `N` is a positive integer. `model` is an equation string or an
  `Equations` object; a multiline string is usually clearest.
- `method` can be a registered updater name (`'euler'`, `'heun'`, `'exact'`,
  etc.) or a suitable callable. Let Brian choose for simple cases, but select
  and record a method when reproducing a result.
- `threshold` is a one-line boolean expression. It creates the default
  `spike` event. `reset` is abstract code, often one or more newline- or
  semicolon-separated assignments executed for neurons in that event.
- `refractory` is `False`, a duration, or a string yielding a duration or a
  boolean condition. `events` maps additional valid event names to condition
  strings.
- `namespace` is the group-specific mapping for external constants/functions.
  It can be populated after construction but must be complete before the run.
- `dt` selects a group clock. A supplied `clock` is an alternative; avoid
  mixing them. Device and code-generation target selection are outside this
  route.

A minimal spiking group is:

```python
model = '''
    dv/dt = (drive - v) / tau : 1
    tau : second
    drive : 1
'''
group = NeuronGroup(
    8, model, threshold='v > 1', reset='v = 0',
    refractory=2*ms, method='euler', dt=0.1*ms,
)
group.tau = 10*ms
group.drive = 1.4
group.v = 0
```

A group with no threshold has no default `spike` event. A threshold without a
reset is legal (and useful for counting or naturally escaping conditions), but
Brian warns unless a refractory condition or an explicit empty reset indicates
that this is intentional.

## Model declarations and state views

Common equation declarations are:

```python
model = '''
    dv/dt = (I - v) / tau : 1
    tau : second
    I : 1
    leak = -v / tau : Hz
    cell_id : integer
'''
```

- `dname/dt = expression : unit` declares a differential state; its right side
  has the state unit per second.
- `name : unit` declares a writable parameter. Declare a value here when it
  varies across neurons; an outer Python value is scalar.
- `name = expression : unit` declares a subexpression. By default it is
  reevaluated when used; `(constant over dt)` requests one value per time step,
  especially important for stateful random functions.
- `(constant)` prevents state changes during a run; `(shared)` stores one scalar
  for the complete group; `(linked)` reserves a live reference target.
- A differential equation may use `(unless refractory)` to clamp its update
  while the neuron is refractory. This flag requires a `refractory` argument.
- Boolean and integer parameters use `: boolean` and `: integer`. Stochastic
  equations use `xi`; multiple independent noise terms need distinct suffixed
  variables (`xi_1`, `xi_2`). Detailed unit/parser rules are intentionally
  outside this route.

Declared states are attributes. `group.v` is unit-aware and `group.v_` exposes
raw values without units. Brian also provides read-only `i` (neuron index) and
`N` (group size). Use `get_states()` and `set_states(...)` for compatible
snapshots; by default they use a dictionary and preserve units.

```python
group.v = '0.1 + 0.02*i'
group.tau = '5*ms + i/N*5*ms'
group.v['i < 2'] = 0.2
group.v_ = 0.0  # intentional raw, dimensionless assignment
states = group.get_states()
group.set_states({'v': [0.0] * len(group), 'tau': 10*ms})
```

String assignment is Brian abstract code evaluated over the selected state
view. It is not Python `eval`; use supported operators, variables, units, and
Brian functions only. Array shapes must match the group or selected view.

## Threshold, reset, refractory, and events

The default `spike` event is made by `threshold='...'`. Reset code is attached
to it automatically. A fixed duration is timestep-safe; a string can be
heterogeneous or state-dependent:

```python
group = NeuronGroup(
    4,
    '''
    dv/dt = -v/(10*ms) : 1 (unless refractory)
    ref : second
    ''',
    threshold='v > 1', reset='v = 0', refractory='ref',
    method='euler',
)
group.ref = [1, 2, 3, 4] * ms
```

A boolean refractory expression means **remain refractory while true**, for
example `refractory='v >= 1'`. With refractoriness enabled Brian exposes
`lastspike` and `not_refractory`. Only derivatives marked `(unless refractory)`
are clamped; other state variables continue to update. A fixed duration is
internally compared in timestep units to avoid floating-point boundary errors.

Define additional model events with `events={'high': 'x > 0.8'}`. Attach
state-side effects once with `run_on_event`:

```python
group = NeuronGroup(
    2, 'x : 1\n event_count : integer',
    events={'high': 'x > 0.8'},
    namespace={},
)
group.run_on_event('high', 'event_count += 1')
group.set_event_schedule('high', when='after_thresholds')
```

Custom event conditions default to checking after thresholds; attached code
defaults to after resets. Conditions are level-triggered: while a condition
remains true, the event can fire on every scheduled check. They are not
edge/crossing detectors. Add a latch or reset the condition when one-shot
crossing behavior is required. `run_on_event(event, code, when=..., order=...)`
and
`set_event_schedule(event, when=..., order=...)` change execution timing.
`events` keys must be valid identifiers. When `threshold` is supplied, do not
also pass an `events['spike']` entry because the threshold creates that event.
A custom event does not become a synaptic pathway or monitor automatically;
those are separate objects and routes.

## Subgroups

`group[:k]`, `group[k:]`, and `group[k]` produce contiguous views. Equivalent
contiguous integer lists are accepted; arbitrary non-contiguous or reversed
lists are not. Subgroup assignment changes parent storage:

```python
population = NeuronGroup(6, 'v : 1')
first = population[:3]
last = population[3:]
first.v = 0.1
last.v = '0.2 + 0.01*i'
```

Indices in a subgroup expression are relative to that subgroup. Subgroups can
be used as sources for model-side links, but they do not copy state and should
not be treated as independent populations for ownership or scheduling.

## Shared and linked variables

Use `(shared)` for one writable scalar:

```python
group = NeuronGroup(
    4,
    '''
    input : 1 (shared)
    dv/dt = (input - v)/tau : 1
    tau : second
    ''',
    method='euler',
)
group.input = 0.5
group.tau = 10*ms
```

A shared value cannot be written in a subset-only context such as an ordinary
per-spike reset. If code writes shared and vector variables in one group-wide
block, place shared writes first and verify that the context is group-wide.
Shared subexpressions may refer only to scalar/shared variables.

Use `(linked)` when a receiver should read source storage live rather than take
a copy:

```python
from brian2.core.variables import linked_var

source = NeuronGroup(2, 'x : 1')
receiver = NeuronGroup(4, 'x_source : 1 (linked)')
source.x = [0.2, 0.8]
receiver.x_source = linked_var(source.x, index=[0, 0, 1, 1])
```

The source and receiver dimensions must match. Same-size sources map one to
one. A size-one source or shared source maps one to all. Other size mismatches
require a one-dimensional integer index of receiver length, with all values in
range. The receiver declaration must include `(linked)`, and the link must be
assigned with `linked_var(source_or_view, name=None, index=...)`. Do not assign
a linked target an ordinary scalar or array; it is a reference, not a copy.
For a dynamic-size owner such as `Synapses`, an index array is unsupported;
bind with an owner-side integer index variable instead. Route dynamic synaptic
modeling and pathway behavior to `synapses-and-inputs`.

## Periodic code and functions

`group.run_regularly(code, dt=None, clock=None, when='start', order=0, ...)`
registers abstract code in the group and automatically owns the resulting
runner. Use it for periodic state updates, not arbitrary Python callbacks:

```python
group.run_regularly(
    'input = 0.5 + 0.1*sin(2*pi*t/(10*ms))',
    dt=1*ms, when='start',
)
```

Use `run_on_event` for event-triggered code. Built-in functions include
`exp`, `sqrt`, `clip`, `rand`, `randn`, `int`, and `timestep`; random values
inside a subexpression may need `(constant over dt)`. A user function must be
unit-declared (normally with `check_units`), placed in the model namespace,
and work with Brian's vector/scalar calling convention:

```python
import numpy as np
from brian2 import NeuronGroup, check_units, ms, prefs

prefs.codegen.target = 'numpy'  # this example is intentionally NumPy-only

@check_units(x=1, result=1)
def saturate(x):
    return np.minimum(x, 1.0)

group = NeuronGroup(
    2,
    'dx/dt = saturate(x) / tau : 1\n tau : second',
    method='euler',
    namespace={'saturate': saturate},
)
group.tau = 10*ms
```

Keep unit declarations and unit-aware function details with
[units-and-equations](../../units-and-equations/SKILL.md). C++/Cython
implementations, external libraries, and compiler dependencies are
code-generation concerns.

## Validation gate and common exceptions

Before scaling a model:

1. Confirm that every identifier is a declared state, Brian built-in, or an
   explicit namespace entry.
2. Check derivative, threshold, reset, event, refractory, and assignment
   dimensions. A constructor can defer some checks until `run`.
3. Construct an explicit `Network(group, ...)` and run `0*ms` with a deliberate
   namespace, then run a tiny positive duration and assert a state change,
   event count, or refractory gap.
4. For subgroups, assert parent values after view assignment. For links, assert
   the mapped receiver view before and after changing source state.
5. If the model is expected to be a spiking source, verify `threshold`, reset
   intent, and event ownership rather than assuming a magic network will find
   it.

Typical failures include unknown identifiers wrapped in `BrianObjectException`,
syntax errors for non-abstract code, `DimensionMismatchError` for incompatible
units, `ValueError` for missing events or invalid links, and `TypeError` for
non-integer or wrong-shaped link indices. Read the troubleshooting reference
for recovery rather than stripping units or adding arbitrary Python control
flow.
