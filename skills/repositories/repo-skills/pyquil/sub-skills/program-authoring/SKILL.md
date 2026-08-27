---
name: program-authoring
description: "Enables construction, inspection, transformation, serialization,
  and diagram generation for PyQuil Programs, Quil, and Quil-T without executing
  a quantum job."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Program authoring

Use this route when the task is about writing or understanding Quil rather than
submitting it: `Program`, standard gates, `DECLARE`, `MEASURE`, memory
references, placeholders, custom gates, classical labels/branches, `PRAGMA`,
Quil-T definitions, `out()`, parsing, or LaTeX diagrams.

This sub-skill constructs and validates program text locally. It does **not**
compile, submit, simulate, estimate noise, query a processor, or prove that a
QPU/QVM/service accepts a program.

## Route the task first

| Request | Use |
|---|---|
| Build, parse, compose, parameterize, address, inspect, or serialize Quil | This sub-skill |
| Compile, select a `QuantumComputer`, call QAM/QVM/QPU, or inspect job results | [`compile-execute`](../compile-execute/SKILL.md) |
| Obtain statevectors, probabilities, expectations, or local numerical dynamics | [`simulation`](../simulation/SKILL.md) |
| Build `NoiseModel`, Pauli, `Experiment`, calibration, or estimation workflows | [`noise-experiments`](../noise-experiments/SKILL.md) |
| Build or inspect topology, ISA, processor connectivity, or gate availability | [`processor-isa`](../processor-isa/SKILL.md) |

Read [`api-reference.md`](references/api-reference.md) before relying on a
signature or subtle mutability/serialization rule. Read
[`workflows.md`](references/workflows.md) for end-to-end authoring recipes.
Read [`quil-t-and-diagrams.md`](references/quil-t-and-diagrams.md) for pulse,
frame, calibration, waveform, or LaTeX work. Read
[`troubleshooting.md`](references/troubleshooting.md) after an exception or
when a program looks valid in Python but its Quil is suspect.

For a deterministic, service-free Bell construction and canonical Quil check,
run [`scripts/build_bell_program.py`](scripts/build_bell_program.py). It only
constructs and serializes a `Program`; it never calls a compiler, QVM, QPU, or
external service:

```bash
python scripts/build_bell_program.py --help
python scripts/build_bell_program.py --validate-only
python scripts/build_bell_program.py
```

## Authoring contract

1. Import `Program` from `pyquil`; import gates from `pyquil.gates`; use
   `pyquil.quilatom` for `MemoryReference`, `Parameter`, placeholders, labels,
   frames, and waveform invocations; use `pyquil.quilbase` for instruction and
   definition classes.
2. Construct from typed instructions where possible. `Program(...)`, `.inst`,
   `+=`, `+`, and Quil strings are supported. Keep the source `Program` when a
   second variant is needed: `+` and `.copy()` avoid accidental edits to the
   original, while `.inst`, `+=`, `.measure`, `.declare`, and
   `.wrap_in_numshots_loop` mutate it.
3. Declare every memory region intentionally and retain the returned base
   `MemoryReference`. Check offsets yourself, especially for parsed or manually
   created references whose declaration size is unknown.
4. Resolve every `QubitPlaceholder` and `LabelPlaceholder` before calling
   `out()` for submission-shaped Quil. Prefer `address_qubits(program, mapping)`
   when a physical mapping is part of the requirement; it returns a copy.
5. Treat `program.out()` as a local serialization observation. Round-trip with
   `Program(program.out()).out()` when a stable Quil representation is needed;
   this is parsing/serialization validation, not execution validation.
6. Use `wrap_in_numshots_loop(shots)` only to set `program.num_shots`; it does
   not add a Quil loop and does not run shots. For an actual Quil loop, use
   `with_loop` with an `INTEGER` counter and explicit labels.
7. Use `out(calibrations=False)` only to omit calibration definitions. It can
   still contain other Quil-T/global definitions such as frames and waveforms.
   Use `remove_quil_t_instructions()` only when a deliberately stripped,
   non-Quil-T variant is wanted; it is not a general compiler compatibility
   proof.
8. For custom gates, validate matrix shape/unitarity, parameter count, and
   qudit argument count explicitly before composing. For classical branches,
   declare and populate the condition memory, then resolve generated labels.
9. For LaTeX, prefer `to_latex(program)` when the required output is source
   text. `display(program)` additionally needs IPython plus `pdflatex`,
   ImageMagick `convert`, and a suitable LaTeX installation; neither function
   executes the program.

## Quick local skeleton

```python
from pyquil import Program
from pyquil.gates import CNOT, H, MEASURE

program = Program()
ro = program.declare("ro", "BIT", 2)
program += [H(0), CNOT(0, 1)]
program += [MEASURE(0, ro[0]), MEASURE(1, ro[1])]
quil_text = program.out()
assert Program(quil_text).out() == quil_text
```

The expected output is ordinary Quil beginning with `DECLARE ro BIT[2]`, then
`H 0`, `CNOT 0 1`, and the two measurements. This confirms construction and
round-trip parsing only. Hand the validated `Program` to
[`compile-execute`](../compile-execute/SKILL.md), [`simulation`](../simulation/SKILL.md),
or [`noise-experiments`](../noise-experiments/SKILL.md) only when that later
workflow is explicitly requested.
