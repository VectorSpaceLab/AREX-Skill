# Directives, typed I/O, and standard library

## Pragmas and annotations

Directives carry implementation or tooling information without changing the
core language definition. They must be treated as an extension contract, not as
portable semantics.

A pragma starts with `pragma`, an optional dotted namespace/name sequence, and
continues to the end of the line:

```qasm
pragma vendor.option value;
pragma tool.hint schedule_late
```

Pragma text is interpreted by the consumer. Unsupported pragmas should be
ignored and preserved for later passes where the consumer follows the language
contract. The `openqasm` namespace is reserved; do not create a private meaning
under it. Some consumers accept legacy `#pragma`, but use `pragma` for portable
OpenQASM 3 source. Pragmas are global directives and should avoid hidden
stateful interactions across included text.

Annotations begin with `@`, use a dotted keyword/namespace form, and attach to
the next statement or declaration. Multiple annotations can precede one item:

```qasm
@tool.schedule_late
@vendor.classification calibrated
x q[0];
```

The language does not define annotation meanings, order, or interaction. A
consumer may preserve them, ignore them, or require a registered namespace.
When debugging, first establish that the parser attached the annotation to the
intended statement, then consult the target's directive contract.

## Typed input and output

`input` identifies a global parameter supplied to a quantum procedure; `output`
identifies a value explicitly returned:

```qasm
OPENQASM 3.1;
include "stdgates.inc";

input angle[32] rotation;
input array[float[32], 2] coefficients;
output bit result;

qubit q;
rz(rotation) q;
result = measure q;
```

A variable cannot be both input and output. Input/output declarations are
optional. Without input declarations, a consumer may expose no parameterized
interface; without output declarations, the compatibility rule treats declared
classical variables as outputs. Prefer explicit declarations for a stable
interface, especially when a program has scratch variables or arrays.

Typed I/O is an interface description, not a promise about a provider's
parameter binding, memory layout, or runtime support. Validate array shapes,
angle widths, and target-supported runtime types separately. Avoid naming a
scratch measurement variable `output` unless it is intended to be returned.

## Include contract

The standard library is the include file named `stdgates.inc`:

```qasm
include "stdgates.inc";
```

`include` is global-only and behaves as if the included declarations appeared
at that point in the global source. There is no language-level include
namespace. The consumer decides how to search for the file, whether it permits
other include names, and which versioned library it supplies. Therefore:

1. Put the version statement before the include.
2. Include each required library once in a controlled environment.
3. Do not duplicate or shadow `stdgates.inc` with a local file when portability
   matters.
4. Check that every gate used is actually available in the consumer's
   versioned library; an include line can parse while resolution fails.
5. Treat vendor includes as provider-specific and document their required
   definitions separately.

## Built-in and standard gates

`U(theta, phi, lambda)` and `gphase(gamma)` are language built-ins. The
standard library is defined as gate declarations with the mathematical actions
specified by the language; implementations may optimize them or supply
calibrations but must preserve their specified unitary meaning when accepted.

The standard set below is the compact authoring table. The standard library
baseline was introduced with OpenQASM 3.0; check the target's 3.1 library
contract rather than assuming an arbitrary older file is valid for every
consumer.

| Family | Names and signatures | Baseline |
|---|---|---|
| Phase/Pauli | `p(lambda)`, `x`, `y`, `z` | 3.0 |
| Clifford/root | `h`, `s`, `sdg`, `t`, `tdg`, `sx` | 3.0 |
| Rotations | `rx(theta)`, `ry(theta)`, `rz(lambda)` | 3.0 |
| Controlled 1-qubit | `cx`, `cy`, `cz`, `cp(lambda)`, `crx(theta)`, `cry(theta)`, `crz(theta)`, `ch` | 3.0 |
| Two-qubit | `swap` | 3.0 |
| Three-qubit | `ccx`, `cswap` | 3.0 |
| Controlled-U | `cu(theta, phi, lambda, gamma)` | 3.0 |
| Compatibility aliases | `CX`, `phase(lambda)`, `cphase(lambda)`, `id`, `u1(lambda)`, `u2(phi, lambda)`, `u3(theta, phi, lambda)` | 3.0 |

The compatibility names exist for migration convenience and may be discouraged
by a style or target policy. OpenQASM 3's `U` differs in global-phase convention
from OpenQASM 2's historical form; do not silently translate between language
versions while claiming identical source semantics.

## Choosing a standard gate

1. Use the mathematical operation needed by the algorithm (`rz`, `cx`, `swap`,
   and so on), not a guessed hardware-native instruction.
2. Verify parameter order and qubit order. For controlled gates, the first
   operand is conventionally the control and later operands are targets.
3. Include `stdgates.inc` before use and pin the OpenQASM version.
4. Use a custom `gate` only to express a unitary composition or parameterized
   family. Use `defcal` for a target-level implementation, not as a substitute
   for a mathematical gate definition.
5. Ask a compiler/provider whether the operation can be decomposed, calibrated,
   and executed. The standard table is not a hardware support matrix.

## Validation layers

- **Grammar:** directive spelling, placement, and statement termination are
  accepted.
- **Parser context:** global-only includes/pragmas and annotation attachment are
  respected.
- **Language semantics:** I/O variables have legal types, are not both input and
  output, and gate names/signatures resolve without collisions.
- **Include resolution:** the selected consumer finds the requested file and
  versioned gate definitions.
- **Compilation/execution:** the target supports the interface, operations,
  parameter widths, and any provider-specific directives.
