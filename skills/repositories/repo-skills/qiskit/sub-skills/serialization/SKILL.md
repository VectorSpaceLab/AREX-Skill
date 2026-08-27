---
name: serialization
description: "Guides agents importing, exporting, and troubleshooting Qiskit
  OpenQASM 2, OpenQASM 3, and QPY serialization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit serialization workflows

Use this sub-skill when the task involves `qiskit.qasm2`, `qiskit.qasm3`, or `qiskit.qpy`: reading or writing circuits, choosing interchange formats, preserving circuit structure, or debugging parser/exporter/version errors.

## Read next

- `references/workflows.md` for QASM2, QASM3, and QPY recipes.
- `references/troubleshooting.md` for missing `qiskit_qasm3_import`, parse/export errors, unsupported features, and legacy QPY compatibility.
- `../../references/installation.md` for the `qasm3-import` and `qpy-compat` extras.
- `../../scripts/check_qiskit_environment.py --sections serialization` for a source-free serialization smoke check.

## Include here

- `qiskit.qasm2.load`, `loads`, `dump`, `dumps`, custom instructions, custom classical functions, and strict mode.
- `qiskit.qasm3.load`, `loads`, `dump`, `dumps`, `Exporter`, experimental features, and native experimental parser entry points.
- `qiskit.qpy.dump`, `load`, `get_qpy_version`, QPY target versions, and compatibility limitations.
- Choosing between text interchange and full-fidelity binary circuit persistence.

## Exclude or route elsewhere

- Constructing the circuit before serialization belongs in `../circuit/SKILL.md`.
- Running or sampling the circuit belongs in `../primitives/SKILL.md` or `../providers/SKILL.md`.
- Matrix/state equivalence after deserialization belongs in `../quantum-info/SKILL.md`.
- Rendering a circuit to an image belongs in `../visualization/SKILL.md`.

## Default route

Start here when the user names QASM, OpenQASM, QPY, `load`, `loads`, `dump`, `dumps`, `QASM2ParseError`, `QASM3ImporterError`, `QASM3ExporterError`, `QpyError`, or `UnsupportedFeatureForVersion`.

## What to remember

- OpenQASM 2 is useful but cannot represent the full Qiskit circuit model.
- OpenQASM 3 is the modern text path; import via `qasm3.load()`/`loads()` needs the optional importer for the compatibility path.
- QPY is the highest-fidelity Qiskit circuit persistence format, but version compatibility and legacy `symengine` choices matter.
