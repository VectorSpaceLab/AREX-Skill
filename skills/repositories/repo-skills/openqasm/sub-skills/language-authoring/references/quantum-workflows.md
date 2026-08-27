# Quantum workflows

Use this reference for circuit-level operations and classical feed-forward. It
covers what a source program means; parser acceptance and implementation
support remain separate checks.

## Standard gate calls and definitions

A gate call has optional angle parameters followed by quantum operands:

```qasm
h q[0];
rz(theta) q[0];
ctrl @ x q[0], q[1];
```

The language has built-in `U(theta, phi, lambda)` and `gphase(gamma)` gates.
Other familiar gates such as `x`, `h`, `cx`, `rz`, and `swap` normally come
from `stdgates.inc`; see the standard-library reference for the include
contract and version table. A gate name must be declared or included before use.

A hierarchical gate defines a unitary transformation, not a hardware
implementation:

```qasm
gate echo(theta) a, b {
  rz(theta) a;
  cx a, b;
  rz(-theta) a;
  cx a, b;
}
```

Gate parameters behave as angle-like values. Gate arguments are formal qubit
identifiers. The body may contain built-in or previously declared gate calls and
quantum loops, but not classical declarations, measurement, reset, timing
statements, subroutine calls, or arbitrary runtime state. Formal qubit
identifiers cannot be indexed inside the body. Definitions must precede calls
and cannot recurse. An empty body is the identity gate.

## Modifiers

Modifiers construct an anonymous modified gate and can be chained:

- `ctrl @ U` adds one positive-polarity control before the base operands.
- `negctrl @ U` adds a control active on `0`.
- `ctrl(n) @ U` or `negctrl(n) @ U` adds a compile-time constant number of
  controls.
- `inv @ U` applies the inverse; for a hierarchical gate this reverses the
  body and inverts each operation.
- `pow(k) @ U` applies the `k`th power where the form and target support the
  requested `k`.

Example:

```qasm
gate controlled_phase(angle[32] a) control, target {
  ctrl @ rz(a) control, target;
}

negctrl @ x q[0], q[1];
inv @ controlled_phase(pi / 4) q[0], q[1];
```

Count the resulting operands after every modifier. A modifier does not add
scratch qubits. Whether the target can decompose or execute the modified gate
is a compiler/provider question, not a language guarantee.

## Broadcasting and ordering

A gate call may use registers. All register operands participating in a
broadcast must have the same length; scalar qubits are repeated for each
expanded call. For example:

```qasm
qubit control;
qubit[3] target;
ctrl @ x control, target;  // three controlled-X operations
```

Broadcasting is a promise that the expanded operations commute sufficiently for
the compiler to reorder them. If order matters, write an explicit loop:

```qasm
for int i in [0:2] {
  cx control, target[i];
}
```

Do not use a register of a different length in a broadcast and do not infer a
sequence order from a broadcast expression.

## Reset, measurement, barrier, and nop

`reset q;` initializes virtual qubits to `|0>` by a non-unitary operation. It
can be applied to a qubit or register and should be explicit when a workflow
needs known initial state.

Measurement is in the Z basis and leaves the measured qubits available for
later operations. Prefer the assignment form:

```qasm
bit[2] result;
result = measure q;
bit one;
one = measure q[0];
```

The arrow form `measure q -> result;` is also supported. Register measurement
broadcasts elementwise only when source and destination register shapes match.
Do not confuse `bit` with `bit[1]` when choosing a destination. Measurement
outcomes are runtime classical values, so a branch depending on them is not a
compile-time constant.

`barrier operands;` imposes an ordering boundary on the selected qubits;
`barrier;` covers all qubits in scope. It is not a duration measurement. `nop`
marks selected qubits as used without changing their ideal state and is valid
where a gate call is valid. It is especially useful inside a `box` to synchronize
a qubit that has no explicit operation:

```qasm
box [100ns] {
  x q[0];
  nop q[1];
}
```

Whether a barrier, nop, or reset is accepted by a particular target must be
checked independently from parsing.

## Classical control flow

`if` accepts a Boolean-compatible scalar condition and either a single
statement or a braced block:

```qasm
bit flag;
flag = measure q[0];
if (flag) {
  x q[1];
} else {
  reset q[1];
}
```

`while (condition)` repeats until false and may modify the condition variables
inside its body. `for type name in values` iterates over an inclusive integer
range such as `[0:2:10]`, a set such as `{1, 4, 7}`, a bit/register alias, or a
one-dimensional array. The loop variable is local to the body and assigning it
does not alter the next iteration value.

Use `break;` to leave the closest `for`/`while`, and `continue;` to advance it.
Both are invalid outside a loop, including at top level or directly in a
subroutine. `end;` terminates the program immediately from any scope.

`switch (expression)` requires an integer-typed controlling expression; no
implicit conversion to integer is allowed. It contains at least one `case`,
optionally one final `default`, and no statements between the cases:

```qasm
uint[2] selector = 0;
switch (selector) {
  case 0, 1 {
    x q[0];
  }
  case 2 {
    z q[0];
  }
  default {
    reset q[0];
  }
}
```

Case labels are integer compile-time constants and cannot duplicate. A case or
default body has its own scope. A switch is not a loop and does not fall
through after the selected body.

## Subroutines (`def`)

Use `def` for a named procedure that may combine quantum operations, classical
values, measurements, and control flow. Quantum arguments are passed by
reference/name; classical scalar values are passed by value. A qubit may appear
at most once in one call, and distinct qubit arguments may not alias the same
underlying qubit.

```qasm
def measure_x(qubit q) -> bit {
  h q;
  return measure q;
}

qubit q;
bit outcome;
reset q;
outcome = measure_x(q);
```

A no-result subroutine omits the arrow, and `return;` exits it. A returning
subroutine returns at most one classical value. Qubits cannot be declared in a
subroutine. Arrays are passed by `readonly` or `mutable` reference and need a
shape or `#dim` contract; see the core-language reference.

Keep a subroutine's declaration before its call. A subroutine can call gates and
other visible subroutines according to the target's semantic rules, but a
`gate` is the narrower unitary construct and must not be used as a general
procedure.

## Extern signatures

Use `extern` to declare an operation implemented outside OpenQASM:

```qasm
extern classify(complex[float[32]] sample) -> bit;
extern log_value(int[32] value);
```

The argument and result types must be known at compile time. Inputs are passed
by value except array references, which carry their `readonly`/`mutable`
qualifier. The language does not define the external implementation, symbol
linkage, latency, side effects, or whether a provider can schedule it in real
time. A program with an extern declaration is therefore not a self-contained
executable workflow until its consumer supplies the matching implementation.

## Physical and virtual circuit design

Virtual qubits (`q`, `q[0]`) represent logical references. Physical operands
(`$0`, `$3`) identify fixed target topology locations and cannot be declared.
`defcal` parameters must be physical operands; ordinary `gate` definitions may
not use physical operands as their formal arguments.

A program containing both kinds can be useful as a partially constrained
intermediate form, but it is not automatically a physical circuit. Do not
assume a provider may remap `$n`; physical labels carry programmer-selected
identity. Conversely, a circuit using `$n` can still need decomposition if an
operation has no matching calibration. Validate the mixture and every operation
against the intended target rather than treating a parse result as execution
readiness.
