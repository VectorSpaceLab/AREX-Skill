---
name: transpiler
description: "Guides agents compiling circuits with transpile, Target,
  CouplingMap, Layout, PassManager, preset pass managers, and backend-specific
  pass routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit transpiler workflows

Use this sub-skill when the task is about compiling a circuit to a backend target or hardware topology with `qiskit.transpiler` or `qiskit.compiler.transpile`.

## Read next

- `references/workflows.md` for preset pass managers, targets, routing, and backend-driven recipes.
- `references/troubleshooting.md` for `TranspilerError`, basis-gate mismatches, layout/routing surprises, and missing optional pass dependencies.
- `../../references/module-map.md` for the package-level module map.
- `../../scripts/check_qiskit_environment.py --sections transpiler providers` for a source-free backend-transpile smoke check.

## Include here

- `transpile()` and `generate_preset_pass_manager()`.
- `Target`, `CouplingMap`, `Layout`, `PassManager`, `StagedPassManager`, `PropertySet`, and pass-plugin routing.
- Layout, routing, translation, optimization, scheduling, and seed/optimization-level selection.
- Hardware-driven compilation from a backend or fake backend.
- Basic control of backend-specific defaults, backend targets, and stage-method overrides.

## Exclude or route elsewhere

- Building the abstract circuit itself belongs in `../circuit/SKILL.md`.
- Sampler/estimator jobs and result access belong in `../primitives/SKILL.md`.
- Serialization to QASM/QPY belongs in `../serialization/SKILL.md`.
- State/operator analysis belongs in `../quantum-info/SKILL.md`.
- Visualization of the compiled output belongs in `../visualization/SKILL.md`.

## Default route

If the user mentions basis gates, coupling maps, backend targets, routing, or preset optimization levels, start here even if the input circuit was already valid. This sub-skill is also the right place to interpret a fake backend or `Target` object used as transpilation input.

## What to remember

- `target` takes precedence over loose backend constraints, and explicit loose constraints take precedence over backend defaults.
- `optimization_level` changes the preset stage mix; `0` is minimal runnable compilation and `3` is the most aggressive preset.
- Seed stochastic stages when the user wants reproducible output.
- Optional pass dependencies are part of the workflow surface. Check them before suggesting a pass that depends on `z3-solver`, `python-constraint`, or similar extras.
