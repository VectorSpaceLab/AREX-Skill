# Equation syntax, flags, and namespaces

Brian2 model strings are a small, translated expression language. They are not
arbitrary Python and are evaluated in a per-neuron or per-synapse context.

## Declaration grammar

Each non-comment declaration has one of these forms:

```text
dx/dt = right_hand_side : variable_unit (flags)
x = expression : variable_unit (flags)
x : variable_unit (flags)
```

Use one declaration per logical line; a declaration may be continued for
readability. `#` starts a comment. The unit after `:` is a base unit or a
compound dimension (`volt`, `siemens/metre**2`, `1`, `boolean`, or `integer`).
Do not write `mV` as the declared unit. For a differential equation, the
right-hand side is checked against `variable_unit/second`.

Supported arithmetic includes `+`, `-`, `*`, `/`, `//`, `%`, and `**`, with
comparisons, `and`, `or`, and `not`. Standard Brian functions include `exp`,
`sqrt`, `log`, `abs`, trigonometric functions, `clip`, `floor`, `ceil`, `rand`,
`randn`, `poisson`, and `int`. Refer to them by their bare names. `np.sqrt`,
imports, object methods, comprehensions, arbitrary library calls, Python
indexing, and general Python control flow are not equation syntax.

Identifiers start with an ASCII letter and continue with ASCII letters, digits,
or underscores. Python keywords, names beginning with `_`, unit names, default
function names, default constants, and special symbols are unavailable as user
variable names. Avoid names ending in `_pre`/`_post` except in the synaptic code
contexts where Brian defines them.

A textbook integrated update such as `v(t+dt) = ...` must be converted to a
first-order derivative (`dv/dt = ...`) before passing it to `NeuronGroup` or
`Synapses`. Keep the conversion's time-scale and unit factors explicit.

## Flags and ownership

Flags are comma-separated in parentheses, for example
`dv/dt = -v/tau : 1 (unless refractory)`.

- `event-driven` is for `Synapses` differential equations only. It removes the
  variable from continuous updates and updates it at event code execution.
  Brian's automatic event-driven updater is limited to one-dimensional linear
  equations. An event-driven variable cannot feed a non-event-driven equation,
  directly or through a subexpression.
- `unless refractory` is for `NeuronGroup` differential equations. The state is
  held during the group's refractory period; it has no effect without a
  configured refractory rule.
- `constant` marks a parameter that will not change during a run and permits
  updater optimizations. Do not assign it in event code or between steps.
- `constant over dt` is for subexpressions. Brian evaluates it once per time
  step. It is required when a subexpression calls a stateful function such as
  `rand()` and is useful when approximating a term as constant for a linear
  updater.
- `shared` makes a parameter or subexpression one scalar for the whole owner.
  A shared subexpression may refer only to shared values.
- `linked` declares a live link to a variable in another `NeuronGroup` or
  `SpatialNeuron`; bind it with the appropriate `linked_var` API. Check shape,
  dimensions, and lifetime before running.

Multiple flags must be supported by the owner and compatible with one another;
parsing a flag string does not make an invalid combination legal.

## Special symbols and stochastic terms

Brian supplies these symbols in the abstract-code namespace:

- `t`, `dt`, and `t_in_timesteps` — current time and step information;
- `i`, `j`, `N`, `N_pre`, and `N_post` — owner or pre/post indices/counts;
- `lastspike` and `not_refractory` — refractory state;
- `lastupdate` — event-driven synapse update time;
- `xi` and suffixed `xi_*` — white-noise terms.

Do not declare variables with these names. `xi` has white-noise dimensions of
`second**-0.5`; make the complete right-hand side dimension
`variable_unit/second`. Suffixes identify noise streams: repeated `xi_1` means
the same stream, while `xi_1` and `xi_2` are distinct. More than one unsuffixed
plain `xi` in one equation set is rejected. Noise is independent across
neurons; shared correlated noise needs an explicit shared source or linked
variable instead.

## External namespaces

An equation can refer to a constant or prepared function that is not a state
variable. Supply it explicitly for reproducibility:

```python
G = NeuronGroup(
    1,
    "dv/dt = -v/tau + drive : volt",
    namespace={"tau": 10*ms, "drive": 1*mV/ms},
    method="euler",
)
net = Network(G)
net.run(0*ms, namespace={})
```

Resolution order is Brian's default units/functions/constants, the group's
namespace, then the run namespace. Implicit caller locals/globals are the last
fallback and are fragile in notebooks and helpers. A duplicate name across
explicit and run namespaces emits a warning and should be repaired by keeping
one authoritative value.

## Validation workflow

1. Parse the smallest `Equations` object.
2. Check that every derivative, subexpression, parameter, and external value
   has a written dimension.
3. Instantiate the owning group with a deliberate `method` and explicit
   namespace.
4. Run `Network.run(0*second, namespace={})` to force owner-level identifier,
   unit, flag, and code-generation validation.
5. Run one or two time steps before scaling up. If validation fails, read the
   exception's object and equation context rather than disabling unit checks.

See [the API reference](api-reference.md) for function metadata and
[numerical methods](numerical-methods.md) for updater selection. For concrete
recovery actions, use [troubleshooting](troubleshooting.md).

## Evidence basis

The grammar, flags, special symbols, namespace examples, and event-driven
limits here follow the Brian2 2.9.0 user-guide topic **Equations** and the
public `brian2.equations.Equations` parser contract. Owner-specific checks are
also reflected in the public `NeuronGroup` and `Synapses` model interfaces;
this is why the validation sequence includes both parsing and a tiny owner run.
