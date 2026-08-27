# Units and equation API reference

This reference describes the Brian2 2.9.0 contracts that this route owns. It is
about model expressions and their validation, not about constructing a complete
neuron or synapse workflow.

## Physical quantities and dimensions

Import units from `brian2` (for example, `volt`, `mV`, `second`, `ms`, `amp`,
`Hz`, and `mM`). Brian's unit objects are multiplicative SI quantities:

```python
from brian2 import mV, ms, volt

rest = -65 * mV
tau = 10 * ms
assert rest / mV == -65
```

Use base units in equation declarations. The suffix on a declaration describes
the variable, not its derivative:

```text
dv/dt = -(v - v_rest) / tau : volt
v_rest : volt
```

The right-hand side of `dv/dt` must have units of `volt/second`. `1` means a
dimensionless floating-point variable; `boolean` and `integer` select the
corresponding dimensionless storage type. Use `mmolar` (also `mM`) for a
millimolar concentration in an equation declaration; `molar` has a different
SI scale. Prefer scaled units for values assigned from Python (`-65*mV`, not
`-0.065*volt` when readability matters).

State variables expose an underscore form containing values in base units and
without unit wrappers (`G.v_[:]`). Use it only at an explicit boundary such as
NumPy analysis or an assertion. Dividing by a unit (`G.v[:] / mV`) is clearer
when the scale matters. `asarray`/`array` remove wrappers in base units; do not
silently mix their results with scaled values.

Brian checks dimensional arithmetic and raises `DimensionMismatchError` for
addition, comparison, assignments, function arguments, or equation right-hand
sides with incompatible dimensions. A plain Python number has dimension `1`;
it is not an implicit millisecond, volt, or ampere.

## `Equations`

`Equations(text, **replacements)` parses and stores three declaration forms:

- `dx/dt = expression : unit` — a differential equation;
- `x = expression : unit` — an on-demand subexpression;
- `x : unit` — a parameter.

Comments beginning with `#` are accepted. `Equations` objects can be added to
combine model fragments. Keyword replacements are textual substitutions, not
late-bound namespace entries, so use them only for deliberate template
construction.

Construction performs syntax, duplicate-name, dependency-cycle, and basic
identifier checks. It does **not** prove that all identifiers, flags, or units
are valid for a particular owner. Instantiate the `NeuronGroup`, `Synapses`, or
`SpatialNeuron`, then validate with a zero-duration run in an explicit
`Network` and namespace. A successful `Equations(...)` call alone is not a
unit-check gate.

## `check_units`

Use `check_units` to declare a Python function's argument and result contracts:

```python
from brian2 import check_units, volt

@check_units(x=volt, result=volt)
def twice(x):
    return 2 * x
```

Use `1` for a dimensionless argument/result and `bool` for a Boolean argument
or result. A decorated function checks normal Python calls and supplies the
metadata Brian needs when the function appears in abstract code. Check every
argument that has a required dimension and specify `result=...` when the return
value is used by an equation or statement. Return a quantity with the declared
dimension; do not return a bare number for a dimensional result.

## `Function`

Wrap an existing Python callable when explicit metadata is more convenient:

```python
from brian2 import Function, volt

identity = Function(
    lambda x: x,
    arg_units=[volt],
    return_unit=volt,
)
```

`Function` accepts `arg_units`, `return_unit`, optional `arg_types` and
`return_type`, and options such as `stateless` and `auto_vectorise`. A callable
without complete unit metadata is rejected when wrapped. Use `arg_names` when
unit specifications are name-based or when building dynamic metadata. Function
calls in equations are vectorized over the owning group; write a vector-safe
Python implementation and do not assume a scalar unless the target contract
says so. `arg_types`/`return_type` use Brian's strings (`boolean`, `integer`,
`float`, `any`, or `highest` where supported), while `check_units` uses `bool`
for Boolean contracts.

## `implementation`

`@implementation(target, code, ...)` adds target-specific code for a prepared
function. The Python function plus `check_units` is sufficient for the NumPy
runtime target. Add `numpy` implementation metadata only when using options such
as `discard_units=True`; that option requires the implementation to use raw
base-unit numbers and forbids hidden references such as `brian2.mV` or imports
inside the function.

Non-Python targets need matching implementations (`cython` or `cpp`, as
appropriate). C/Cython source is not proof of a working compiler integration:
provide unit metadata, target code, and any dependencies explicitly. If target
code calls another Brian function, list it in `dependencies`. Headers,
libraries, include directories, and external sources belong to the target
implementation and should be verified separately by the code-generation route.
Apply `@implementation(...)` outside (above) `@check_units(...)`, as in the
Brian examples. The decorated object becomes a `Function`; keep a separate
plain Python call check if the implementation is target-specific. Do not add a
target implementation merely to silence a missing-implementation error; use
NumPy while recovering the Python behavior first.

## Namespaces and validation boundary

An external constant or function can be passed in a group's `namespace={...}`
or to `Network.run(..., namespace={...})`. Brian resolves default units/functions
first, then the group's explicit namespace, then the run namespace. An explicit
empty run namespace (`namespace={}`) disables implicit caller locals/globals and
is useful after all dependencies are supplied explicitly. If a name occurs in
multiple active namespaces, treat the warning as a reproducibility bug and
remove the duplicate.

Keep default function names bare (`exp`, `sqrt`, `sin`, `clip`, `rand`), not
`np.exp` or `numpy.exp`: equation strings are parsed abstract code, not Python
modules. See [equation syntax](equation-syntax.md) for parser restrictions and
[troubleshooting](troubleshooting.md) for recovery patterns.

## Evidence basis

This contract is distilled from the Brian2 2.9.0 user-guide topics **Physical
units**, **Equations**, **Namespaces**, and **Functions**, together with the
public APIs `brian2.Equations`, `brian2.check_units`, `brian2.Function`, and
`brian2.implementation`. The target-boundary statements follow the public
`FunctionImplementation` behavior: a NumPy runtime path and Cython/CPP target
implementations are separate verification gates.
