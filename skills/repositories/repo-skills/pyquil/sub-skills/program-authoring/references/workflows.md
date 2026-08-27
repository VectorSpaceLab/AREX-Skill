# Program authoring workflows

Read this file for concrete, service-free construction recipes. Every example
ends in Python-object or Quil-text validation; none compiles, simulates, or
submits a job.

## 1. Build, parse, compose, and serialize a measured program

1. Create `Program()`.
2. Declare memory and retain its returned reference.
3. Append typed gates and measurements.
4. Call `out()` and assert the expected canonical text.
5. Parse the text with `Program(text)` and compare the second `out()`.

```python
from pyquil import Program
from pyquil.gates import CNOT, H, MEASURE

p = Program()
ro = p.declare("ro", "BIT", 2)
p += H(0)
p += CNOT(0, 1)
p.measure(0, ro[0]).measure(1, ro[1])
# Note: measure() returns Program, while declare() returns MemoryReference.
quil = p.out()
assert quil == (
    "DECLARE ro BIT[2]\n"
    "H 0\n"
    "CNOT 0 1\n"
    "MEASURE 0 ro[0]\n"
    "MEASURE 1 ro[1]\n"
)
assert Program(quil).out() == quil
```

For independent variants, use `p.copy()` before mutation. `p + q` returns a new
composition; `p += q` mutates `p`. To inspect all definitions as well as body
instructions, use `get_all_instructions()` rather than `instructions`.

## 2. Parameterize a gate with classical memory

Declare `theta` as `REAL`, then use `RX(theta, q)` or `RZ(theta, q)`. The
program contains a symbolic memory reference; choosing a numeric value is a
later execution/compiler concern. Locally validate the declaration and text:

```python
import numpy as np
from pyquil import Program
from pyquil.gates import MEASURE, RX, RZ

p = Program()
ro = p.declare("ro", "BIT")
theta = p.declare("theta", "REAL")
p += RX(np.pi / 2, 0)
p += RZ(theta, 0)
p += RX(-np.pi / 2, 0)
p += MEASURE(0, ro)
assert "RZ(theta) 0" in p.out() or "RZ(theta[0]) 0" in p.out()
assert p.declarations["theta"].memory_type == "REAL"
```

Do not put a Python float into a memory map here: memory maps and compiled
executables belong to [`compile-execute`](../../compile-execute/SKILL.md).

## 3. Reusable placeholder subroutine with explicit physical addressing

Build a function that returns a fresh program and its placeholder handles.
Keep all classical addresses explicit, then address a copy for each physical
placement:

```python
from pyquil import Program
from pyquil.gates import CNOT, H, MEASURE, X
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder


def branchable_bell():
    q0, q1 = QubitPlaceholder.register(2)
    p = Program()
    ro = p.declare("ro", "BIT", 2)
    flag = p.declare("flag", "BIT")
    p += [H(q0), CNOT(q0, q1), MEASURE(q0, ro[0])]
    # Branching is a Quil construction, not a Python conditional.
    p.if_then(flag, Program(X(q1)))
    p += MEASURE(q1, ro[1])
    return p, (q0, q1)

unaddressed, (q0, q1) = branchable_bell()
physical = address_qubits(unaddressed, {q0: 5, q1: 9})
physical.resolve_label_placeholders()
quil = physical.out()
assert "H 5" in quil and "CNOT 5 9" in quil
assert "MEASURE 0" not in quil
assert Program(quil).out() == quil
# The template is untouched and can be addressed again.
other = address_qubits(unaddressed, {q0: 2, q1: 3})
assert "CNOT 2 3" in other.out()
```

If a resolver intentionally returns `None`, do not call this a complete
program. `get_qubit_indices()` and `out()` should remain blocked until every
placeholder needed by the target serialization is resolved.

## 4. Classical loops and branches

Use a declared memory reference as the condition. Build branch bodies as
`Program` objects, append them with `if_then`/`while_do`, then resolve labels.
The helper methods generate `JUMP-WHEN`, `JUMP-UNLESS`, `JUMP`, and `LABEL`.

```python
from pyquil import Program
from pyquil.gates import H, MEASURE, MOVE, X

p = Program()
flag = p.declare("flag", "BIT")
ro = p.declare("ro", "BIT")
p += MOVE(flag, 1)
p.if_then(flag, Program(X(0)), Program(H(0)))
p += MEASURE(0, ro)
p.resolve_label_placeholders()
text = p.out()
assert "JUMP-WHEN" in text and "LABEL @" in text
```

For a program-level fixed loop, declare `count` as `INTEGER` and call
`with_loop(iterations, count, Label("start"), Label("end"))`. It returns a
new program and emits `MOVE`, `SUB`, and jumps. For executor metadata only,
call `wrap_in_numshots_loop(n)` and confirm `p.num_shots == n`; the serialized
Quil must remain unchanged.

A classical control condition is an address, not a numeric Python value. The
authoring layer can serialize a condition in any declared scalar region, but
that does not establish that a selected backend accepts the type or dynamic
control. Route backend acceptance to [`compile-execute`](../../compile-execute/SKILL.md).

## 5. Custom static and parameterized gates

Use a unitary matrix and obtain the constructor from the definition:

```python
import numpy as np
from pyquil import Program
from pyquil.quilbase import DefGate

sqrt_x = np.array([[0.5 + 0.5j, 0.5 - 0.5j],
                   [0.5 - 0.5j, 0.5 + 0.5j]])
definition = DefGate("SQRT-X", sqrt_x)
SQRT_X = definition.get_constructor()
p = Program(definition, SQRT_X(0))
assert "DEFGATE SQRT-X AS MATRIX:" in p.out()
assert "SQRT-X 0" in p.out()
```

For a parameterized definition, make a `Parameter`, use Quil expression
functions such as `quil_sin`/`quil_cos` in the matrix, and call
`DefGate(name, matrix, [parameter])`. Its constructor is staged:
`GATE(theta_value)(qubits)`. Before serializing, check matrix dimensions,
unitarity for static matrices, expected parameter count, and expected qubit
arity. A malformed generic `Gate` can still produce text that is not a valid
application of your definition.

## 6. Authoring-level noise pragmas

Use `define_noisy_gate` only when the desired artifact is a program containing
`PRAGMA ADD-KRAUS`; use `define_noisy_readout` for `PRAGMA READOUT-POVM` and
`no_noise()` for `PRAGMA NO-NOISE`. Validate deterministic values locally:

```python
from pyquil import Program
from pyquil.gates import X

p = Program(X(0))
p.define_noisy_readout(0, 0.9, 0.8)
p.no_noise().inst(X(0))
text = p.out()
assert "PRAGMA READOUT-POVM 0" in text
assert "PRAGMA NO-NOISE" in text
```

This proves only pragma construction. Model composition, channel semantics,
Pauli algebra, and experiment execution route to
[`noise-experiments`](../../noise-experiments/SKILL.md).

## 7. Inspect and transform Quil-T without a service

Construct `Frame`, `DefFrame`, `DefWaveform`, and `DefCalibration` objects,
combine them with ordinary gates, and compare the two serialization views:

```python
from pyquil import Program
from pyquil.gates import PULSE, X
from pyquil.quilatom import Frame, Qubit, WaveformInvocation
from pyquil.quilbase import DefCalibration, DefFrame, DefWaveform

frame = Frame([0], "rf")
frame_def = DefFrame(frame, direction="tx", sample_rate=1e9)
waveform_def = DefWaveform("flat", [], [0.25 + 0j, 0.25 + 0j])
cal = DefCalibration("X", [], [Qubit(0)], [PULSE(frame, WaveformInvocation("flat"))])
p = Program(frame_def, waveform_def, cal, X(0))
with_cals = p.out()
without_cals = p.out(calibrations=False)
assert "DEFCAL X 0:" in with_cals
assert "DEFCAL X 0:" not in without_cals
assert "DEFFRAME" in without_cals and "DEFWAVEFORM" in without_cals
```

Use `remove_quil_t_instructions()` for a copy without Quil-T instructions when
that exact transformation is wanted. Do not call the result a backend-validated
program. Quil-T instructions are not accepted by QVM/quilc according to the
assigned package evidence; actual compiler/QAM/QPU handling is routed away.

## 8. Generate LaTeX source or request optional display

`to_latex(program)` returns a complete LaTeX document string containing a
TikZ/Quantikz diagram. It is suitable for writing to a user-selected file, but
PyQuil does not compile the text. `display(program)` invokes external
`pdflatex` and `convert` in a temporary directory and returns an IPython image;
those binaries, LaTeX packages, and IPython are optional and environment
specific.

```python
from pyquil import Program
from pyquil.gates import CNOT, H
from pyquil.latex import to_latex

latex_text = to_latex(Program(H(0), CNOT(0, 1)))
assert "\\begin{tikzcd}" in latex_text
```

If a program includes unsupported control/classical instructions, forked gates,
or unbalanced `LATEX_GATE_GROUP` pragmas, `to_latex` can raise `ValueError`.
Generate source text first; only ask for `display` after separately checking
optional binaries and accepting that external rendering is a different step.
