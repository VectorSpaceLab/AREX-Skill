# Modeling troubleshooting

Use the smallest explicit `Network` and a zero-duration run to localize model
construction failures. Brian2 may defer equation, namespace, threshold, reset,
event, and code-generation checks until `run`; constructor success is not full
validation.

## Install and import

- `ModuleNotFoundError: brian2`: install Brian2 2.9.0 (or a compatible newer
  version) into the active Python >=3.12 environment and verify with
  `python -c "import brian2; print(brian2.__version__)"`.
- An error naming Cython, a compiled extension, or an ABI-specific artifact
  means the package install is incomplete or was built for a different Python
  ABI. Repair/reinstall Brian2 in the active environment; do not modify model
  strings to hide an import failure.
- Core modeling and the bundled smoke use the NumPy runtime and do not need
  plotting, Pandas, Jupyter, GSL, or a compiler. Optional GSL/state-updater
  dependencies are not required for `euler`/`exact`; compiler and device issues
  belong to the code-generation route.
- Check the interpreter that will run the script (`python --version`,
  `python -c "import brian2; print(brian2.__version__, brian2.__file__)"`). A
  different interpreter can make a correct model appear unavailable.

## Invalid equations and identifiers

**Symptoms:** an equation parser error, `KeyError`, `BrianObjectException`, or
an unknown identifier during construction or the first run.

1. Check identifiers in the model, threshold, reset, refractory, event, and
   state-assignment strings. Each must be declared, a Brian built-in, or in a
   deliberate namespace.
2. Declare heterogeneous values in the model. Put scalar external values in a
   group `namespace={...}` or the explicit `Network.run` namespace.
3. Run `Network(group).run(0*ms, namespace=...)` before a positive run. An
   explicit namespace may be completed after construction, but not after the
   validation run.
4. Avoid redefining `t`, `dt`, `i`, or `N`, and avoid neuron names ending in
   `_pre` or `_post`, which have synaptic meaning.

Brian resolves internal variables before external namespaces. If a name exists
in multiple namespaces, remove the conflict or make the selected owner
explicit; do not rely on a warning's precedence for a reproducible model.

## Invalid abstract code and API syntax

**Symptoms:** `SyntaxError`, `ValueError`, or a code-object failure for a model,
threshold, reset, event body, or `run_regularly` string.

- Model strings are Brian abstract code, not arbitrary Python. Use supported
  arithmetic, assignments, comparisons, and Brian functions only. Do not use
  imports, list/dict comprehensions, object methods, filesystem/network calls,
  or general Python `if`/loops.
- A threshold/event condition must be a boolean expression. Reset/event bodies
  must contain valid assignments/statements, not a bare literal.
- `run_on_event` and `set_event_schedule` require an event already present in
  `events` or the default `spike` event from `threshold`.
- A valid Python function still needs Brian unit metadata and compatible
  vector/scalar behavior when called from a model. Replace it temporarily with
  a built-in to isolate the failure. Target-specific implementations and
  dependencies are code-generation concerns.

## Threshold, reset, and custom event failures

- No `threshold` means no default `spike` event. Add a boolean threshold or
  define a named `events` entry if the group should emit model events.
- A threshold without reset is legal but does not reset state. Make it explicit
  with `reset=''` when intentional, or provide a reset when the state would
  otherwise remain above threshold. A refractory condition also suppresses the
  warning but should reflect intended behavior.
- `events` keys must be valid identifiers. When `threshold` is supplied,
  `events` must not redefine `spike`, because the threshold creates that event.
  Event conditions must be boolean and dimensionally valid. Conditions are
  checked on every scheduled timestep while true; custom events are
  level-triggered, not automatic edge detectors. Use a latch, a state reset,
  or a narrow time window when the model needs one action per crossing.
- An event can run its own state-side effect once via `run_on_event`; adding a
  second side effect to the same event is an API error. Event checks default to
  `after_thresholds` and attached code to `after_resets`; only change schedule
  when same-step ordering is tested.
- Event recording and synaptic pathways are separate objects. Route monitor or
  `on_event` questions out rather than adding hidden state to this route.

## Units, assignments, data, and configuration

**Symptoms:** `DimensionMismatchError`, an invalid refractory type, or a state
assignment failure.

- Check derivative units, threshold comparisons, reset right-hand sides, event
  conditions, refractory values, and function metadata. Do not strip units to
  silence a mismatch; detailed unit/parser recovery belongs elsewhere.
- `G.v = -65*mV` is unit-aware. `G.v_ = -0.065` intentionally supplies raw
  values. String assignments are Brian expressions, not `eval`; validate with
  a zero-duration run. Array lengths must match the group or selected view.
- `get_states`/`set_states` should preserve compatible units by default. Use
  `units=False` only when the serialization contract explicitly uses raw
  values, and do not restore read-only/internal variables as ordinary state.
- `(shared)` stores one scalar. Do not treat it as a per-neuron array or write
  it in a subset-only reset. A shared subexpression may refer only to scalar
  values.
- `(linked)` must be declared on the receiving variable and bound with
  `linked_var`. Source/target dimensions must match. For unequal fixed-size
  groups, use a one-dimensional integer in-range mapping with target length;
  a dynamic-size owner such as `Synapses` requires an owner-side integer index
  variable rather than an index array. Floating, wrong-shaped, out-of-range,
  or missing mappings are API errors.
- Configuration is data, not code: validate loaded scalar values, units, array
  shapes, dtype, and namespace keys before putting them into a model. Do not
  fetch configuration or data from the network inside model strings.

## Refractory-specific failures

- `(unless refractory)` without a `refractory` argument usually means the
  constructor forgot its refractory setting. Add a duration/condition or
  remove the flag.
- A duration is compared with timestep-safe timing. If one spike differs from
  expectation, inspect `defaultclock.dt`/group `dt` and compare in timestep
  units instead of binary floating-point times.
- A boolean refractory expression means “remain refractory while true”; it is
  not a one-time permission predicate.
- Refractoriness suppresses threshold events, while only derivatives marked
  `(unless refractory)` are clamped. Check whether each state should continue
  updating or freeze.

## Shared/linked misuse and magic-network invisibility

**Symptoms:** a model constructs but does not update, a link is unset, or a
`run` reports a mixed/empty magic network.

- Create `net = Network(group, other_objects...)` and call `net.run(...)`.
  Objects hidden in containers, created before a scope reset, or created after a
  previous magic `run` can be absent or cause a mixed-network error.
- An explicit `Network` owns all objects that must execute; a subgroup is a view
  and a `run_regularly` operation declared on it must still be reachable through
  its source group. Use `start_scope()` for isolated scripts.
- A linked target cannot be read before its link is bound. Binding the wrong
  source type, size, dimension, or index gives an API error; inspect the target
  view before running.
- A state change assertion can fail simply because duration is zero, the object
  is not in the network, a `run_regularly` clock has not fired, or the event
  condition is never reached. Add a tiny counter/state assertion rather than a
  plot.
- If the model succeeds in NumPy but fails in Cython/C++, treat NumPy success as
  model/API validation only. Remove unsupported Python syntax and route compiler,
  device, and target-specific function diagnostics out.
