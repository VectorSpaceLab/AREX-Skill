# Program authoring API reference

Read this reference when an authoring task depends on exact signatures,
accepted designators, return values, defaults, or object ownership. The facts
below were checked against the installed PyQuil 4.18.0 API and the package
source assigned to this route.

## `Program` lifecycle and composition

| API | Signature/behavior | Authoring consequence |
|---|---|---|
| `Program` | `Program(*instructions)` | Accepts instructions, another `Program`, sequences, generators, tuples (legacy), Quil strings, and compatible Quil instruction objects. |
| `inst` | `program.inst(*instructions) -> Program` | Appends and returns `self`; accepts the same broad instruction designators. Prefer typed gate/instruction objects over legacy tuples. |
| `+` / `+=` | `program + other -> Program`; `program += other -> Program` | `+` creates a concatenated program; `+=` appends in place. Do not assume either operation preserves unresolved placeholders as physical addresses. |
| `copy` | `program.copy() -> Program` | Deep-copies the underlying program and preserves `num_shots`; use for an independently mutable variant. `native_quil_metadata` is assigned as-is by the current implementation. |
| `copy_everything_except_instructions` | `-> Program` | Copies global definitions/metadata but starts with no body instructions. It is useful for rebuilding a body, not for making a full program clone. |
| `instructions` | getter/setter | The getter includes declarations plus body instructions, not every global definition. The setter rebuilds the body while retaining supported global state. |
| `filter_instructions(predicate)` | `-> Program` | Returns a new program retaining instructions for which `predicate(instruction)` is true. Inspect instruction classes before filtering. |
| `get_all_instructions()` | `-> list[AbstractInstruction]` | Includes global definitions and all instructions; use when auditing complete program content. |
| `dagger()` | `-> Program` | Returns the conjugate-transpose program only for gate applications. Do not use on measurements, classical control, or Quil-T bodies. |

`Program` normalizes and may reorder declarations/global definitions during
serialization. Compare `out()` rather than Python insertion order when the
contract is Quil text. Global definitions such as `DEFGATE`, `DEFFRAME`, and
`DEFWAVEFORM` are semantically treated differently from ordinary body order.

## Gates and instructions

The standard constructors live in `pyquil.gates`. Common verified signatures
include:

```text
I/X/Y/Z/H/S/T(qubit)
PHASE/RX/RY/RZ(angle, qubit)
U(theta, phi, lam, qubit)
CZ/CNOT(control, target)
CCNOT(control1, control2, target)
CPHASE/CPHASE00/CPHASE01/CPHASE10(angle, control, target)
SWAP/ISWAP(q1, q2)
PSWAP/XY/RZZ/RXX/RYY(angle, q1, q2)
RESET(qubit_index=None)
DECLARE(name, memory_type='BIT', memory_size=1, shared_region=None, offsets=None)
MEASURE(qubit, classical_reg)
```

Parameterized gate arguments can be numeric values, `Parameter`, Quil
`Expression`, or a declared `MemoryReference`. Gate methods are:

- `gate.controlled(control_qubit)`; a sequence may provide multiple controls.
- `gate.forked(fork_qubit, alt_params)`; the alternate parameter list must
  represent the second parameter choice for the same gate.
- `gate.dagger()`; returns a modified gate object.
- `gate.out()`; returns Quil for that instruction.

Do not infer that a gate's spelling conveys semantics: for example, controlled
`Y` is `X( target ).controlled(control)`, not a hypothetical `CY` constructor.
`PRAGMA` is authoring-level metadata/instruction syntax; compiler rewiring and
backend interpretation belong to [`compile-execute`](../../compile-execute/SKILL.md).

The low-level classes in `pyquil.quilbase` include `Gate(name, params, qubits,
modifiers=[])`, `Measurement(qubit, classical_reg)`, `Declare(name,
memory_type, memory_size=1, shared_region=None, offsets=None)`, and
`Pragma(command, args=(), freeform_string='')`. Use them when a constructor is
not exposed by `pyquil.gates`, but validate their exact operands before
serialization.

## Memory and classical references

`Program.declare(name, memory_type='BIT', memory_size=1, shared_region=None,
offsets=None) -> MemoryReference`. Current valid scalar types include `BIT`,
`REAL`, `INTEGER`, and `OCTET`; the method adds a `DECLARE` and returns the base
reference. It does **not** return the `Program`, so this is incorrect:

```python
program.declare("ro", "BIT").inst(...)  # wrong: result is MemoryReference
```

Use the returned reference as `ro[0]`, `ro[1]`, or directly for a one-element
region. `MemoryReference(name, offset=0, declared_size=None)` rejects negative
or non-integer offsets. Indexing a base reference with a known `declared_size`
checks bounds and returns a new reference; indexing a non-base reference raises.
Parsed/manual references with no `declared_size` cannot provide Python-side
bounds checks, and PyQuil can serialize an undeclared or out-of-range reference.
Validate declarations and all referenced `(name, offset)` pairs yourself.

`MEASURE(qubit, classical_reg)` accepts a `MemoryReference`, a string (treated
as offset zero), a `(name, offset)` pair/list, or `None` for measurement without
a target. `Program.measure_all()` with no pairs declares `ro` sized through the
largest fixed qubit and measures each used fixed qubit into the same offset;
provide explicit pairs for placeholders, non-contiguous layouts, or a custom
region.

`get_classical_addresses_from_program(program) -> dict[str, list[int]]` reports
sorted unique offsets found in targeted `MEASURE` instructions. It does not
validate declarations, memory types, or runtime memory-map values.

Classical constructors include `MOVE`, `NOT`, `NEG`, `AND`, `IOR`, `XOR`,
`EXCHANGE`, `LOAD`, `STORE`, `CONVERT`, `ADD`, `SUB`, `MUL`, `DIV`, `EQ`, `LT`,
`LE`, `GT`, and `GE`. A conditional or loop references a memory cell, not a
Python boolean. Ensure its declaration and type match the intended Quil
runtime semantics, initialize it where needed, and resolve labels before
calling `out()`.

## Placeholders, labels, and addressing

- `QubitPlaceholder()` creates an unresolved qubit token;
  `QubitPlaceholder.register(n) -> list[QubitPlaceholder]` creates a list.
- `Label(name)` is a concrete label; `LabelPlaceholder(prefix='L')` is an
  unresolved target token.
- `address_qubits(program, qubit_mapping=None) -> Program` returns a copy and
  resolves qubit and label placeholders. With no mapping it assigns available
  integer addresses deterministically within the program; with a mapping, map
  every placeholder that must be concrete. A partial map deliberately leaves
  unresolved placeholders.
- `Program.resolve_placeholders_with_custom_resolvers(*, label_resolver=None,
  qubit_resolver=None) -> None` mutates the program. A resolver returning `None`
  leaves that placeholder unresolved.
- `resolve_qubit_placeholders`, `resolve_qubit_placeholders_with_mapping`, and
  `resolve_label_placeholders` mutate in place.
- `Program.get_qubit_indices()` raises if any used qubit is unresolved. `out()`
  likewise raises instead of emitting submission-shaped Quil for unresolved
  placeholders.

`while_do(condition, q_program)` and `if_then(condition, if_program,
else_program=None)` append generated `JUMP*` and label instructions and return
`self`. The current API does not automatically make a label placeholder safe
for serialization; call `resolve_label_placeholders()` (or use
`address_qubits`, which also instantiates labels) before `out()`.

`with_loop(num_iterations, iteration_count_reference, start_label, end_label)
-> Program` returns a wrapped copy. It writes and decrements the supplied
`INTEGER` counter in the generated Quil. This is distinct from
`wrap_in_numshots_loop(shots)`, which only sets `num_shots` and leaves Quil text
unchanged.

## Custom definitions and authoring-level pragmas

`DefGate(name, matrix, parameters=None)` validates square matrices and, for
non-parametric definitions, unitary matrices. Matrix dimensions must be powers
of a prime qudit dimension (2, 3, 4, 5, 8, ...). `get_constructor()` returns a
constructor; for a parameterized definition it is staged as
`CONSTRUCTOR(*params)(*qubits)`. The definition's `num_args()` derives the
number of qudit arguments from the matrix dimension. Validate parameter count
and intended qubit arity yourself: the generic `Gate` layer may serialize a
malformed application even when it is not semantically valid for the
`DEFGATE`.

`DefPermutationGate(name, permutation)` represents a permutation definition.
`DefCircuit(name, parameters, qubits, instructions)` and `DefGateByPaulis` are
available for specialized definition forms; the latter is coupled to Pauli
workflows, so route Pauli algebra/experiments to
[`noise-experiments`](../../noise-experiments/SKILL.md).

`Program.define_noisy_gate(name, qubit_indices, kraus_ops)` and
`define_noisy_readout(qubit, p00, p11)` append authoring-level noise pragmas.
They validate Kraus shape/completeness or probability ranges, but they do not
execute noise. Full noise models, Pauli transformations, and experiments belong
to [`noise-experiments`](../../noise-experiments/SKILL.md).

## Inspection and serialization checklist

Use the following local checks before handing off:

```python
text = program.out(calibrations=True)      # default: include DefCalibration definitions
text_without_cals = program.out(calibrations=False)
round_tripped = Program(text).out()
assert round_tripped == text
qubits = program.get_qubit_indices()
regions = program.declarations
```

`out(calibrations=False)` excludes `DefCalibration` and
`DefMeasureCalibration`, but intentionally retains frames, waveforms, gate
definitions, declarations, ordinary gates, and other instructions. The default
is `calibrations=True`; `None` is accepted by the signature and is falsy in the
current implementation, so it follows the calibration-excluding branch. Use an
explicit `True` or `False` rather than relying on `None` for portable intent.
`str(program)` is useful for human debugging of unresolved placeholders; `out()`
is the strict valid-Quil serialization path.
