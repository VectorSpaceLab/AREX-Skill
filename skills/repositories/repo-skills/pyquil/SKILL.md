---
name: pyquil
description: "Guides PyQuil and Quil quantum-programming workflows: author
  programs, simulate locally, compile and execute through QVM or QPU services,
  model noise and experiments, and inspect processor topologies and ISA
  metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyQuil

Use this repo skill when a task names PyQuil, `pyquil`, Quil, Rigetti Forest,
`Program`, `get_qc`, QVM, QPU, `quilc`, `QuantumComputer`, `PyQVM`, Pauli
experiments, noise models, or compiler ISA/topology metadata. It is a
versioned, self-contained operating guide for PyQuil 4.18.0; it is not a
replacement for QCS credentials, QVM/quilc binaries, a reservation, or a
physical processor.

## First decide the execution boundary

1. **Author or inspect Quil locally:** read
   [`program-authoring`](sub-skills/program-authoring/SKILL.md). It owns
   `Program`, gates, declarations, memory, placeholders, control flow, Quil-T,
   and serialization.
2. **Run numerical simulation without external services:** read
   [`simulation`](sub-skills/simulation/SKILL.md). Prefer `PyQVM` or the
   reference/NumPy simulators. Do not confuse them with the service-backed
   `WavefunctionSimulator`.
3. **Compile, submit, or inspect QAM results:** read
   [`compile-execute`](sub-skills/compile-execute/SKILL.md). It owns
   `QuantumComputer`, compiler/QVM/QPU selection, result maps, batching,
   endpoints, services, and QCS configuration.
4. **Model noise, Pauli observables, or experiments:** read
   [`noise-experiments`](sub-skills/noise-experiments/SKILL.md). It owns
   construction and validation; execution remains a separate backend step.
5. **Inspect connectivity or instruction-set metadata:** read
   [`processor-isa`](sub-skills/processor-isa/SKILL.md). It owns NetworkX
   topologies, `CompilerISA`, QCS ISA conversion, and processor compatibility.

For a task crossing routes, start with the first route that creates the
artifact, then follow its explicit handoff. Keep these distinctions visible:

| Local artifact or operation | What it proves | What it does not prove |
|---|---|---|
| `Program(...).out()` | Quil construction and serialization | Compiler acceptance or execution |
| `PyQVM` / reference simulator | In-process behavior on the selected simulator | QVM/quilc availability or QPU behavior |
| `qc.compile()` / `qc.run()` | Backend interaction only when the configured services respond | Physical correctness beyond the returned evidence |
| `NoiseModel`, `Experiment`, or ISA object | Model/metadata construction and validation | A run, calibration, reservation, or hardware result |

## Install and inspect

Use a supported Python version from the package metadata (Python 3.11 or 3.12
for this release) in an isolated environment:

```bash
python -m pip install pyquil
python -c "import pyquil; print(pyquil.__version__)"
```

The optional `latex` extra supplies IPython for interactive display helpers:

```bash
python -m pip install 'pyquil[latex]'
```

The package depends on compiled Rust-backed distributions on common platforms;
less common platforms may need a Rust toolchain. QVM/quilc are separate Forest
SDK services and are not installed by the Python package. QCS/QPU workflows
also require authorized configuration and access. Read
[`references/concepts-and-runtime-boundaries.md`](references/concepts-and-runtime-boundaries.md)
for the dependency and service boundary before installing broad extras.

Run the bundled, service-free installation check from any working directory:

```bash
python scripts/check_pyquil_install.py --help
python scripts/check_pyquil_install.py
```

It reports package metadata/imports and small local capability checks without
starting services, reading secrets, contacting QCS, or writing files. Read
[`references/troubleshooting.md`](references/troubleshooting.md) when the
import, optional dependency, configuration, compiler, service, or credential
boundary is unclear. Read
[`references/repo-provenance.md`](references/repo-provenance.md) before using
this skill against a changed checkout; a changed commit or public API surface
calls for `refresh-repo-skill`.

## Shared operating rules

- Build and validate a `Program` before handing it to a simulator or compiler.
- Declare memory deliberately; validate register names, dimensions, and shot
  counts before interpreting returned arrays.
- Resolve qubit and label placeholders before submission-shaped serialization.
- Use explicit finite timeouts for compiler/service calls and record whether a
  service or credential was actually used.
- Treat qubit order, Pauli sign conventions, readout-matrix orientation, and
  ISA dead-resource flags as data contracts, not presentation details.
- Stop rather than inventing a QPU result when QCS credentials, a reservation,
  `quilc`, or QVM is missing.

## Runtime files

All references and helpers linked by the routes above are bundled inside this
skill. Review/test records, native candidate maps, environment reports, and
verification notes live outside the runtime tree under the construction
artifact directory; do not make later Researcher runs depend on them.
