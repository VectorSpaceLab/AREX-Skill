---
name: integrations-development
description: "Integrate DeePMD-kit with LAMMPS, i-PI, native APIs, dpdata, ASE,
  Node.js, and maintainer build/test workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Integrations Development

Use this sub-skill when the task is about connecting DeePMD-kit models to molecular-dynamics engines or native host applications, or when editing this repository's integration/build/test surfaces.

## Route First

- For package installation, backend dependency selection, and CLI availability, route to [installation-backends](../installation-backends/SKILL.md).
- For training, freezing, compressing, converting, or exporting a model before deployment, route to [training-models](../training-models/SKILL.md).
- For direct Python `DeepPot` array inference, descriptors, model deviation arrays, or `dp test`, route to [inference-model-ops](../inference-model-ops/SKILL.md).
- Stay here for LAMMPS input design, i-PI driver setup, C/C++/HPP/C API integration, Node.js wrappers, dpdata/ASE integration, C++ component builds, and maintainer validation plans.

## Core Responsibilities

- Translate user simulation intent into bounded LAMMPS or i-PI integration steps without running long MD unless explicitly requested.
- Select between LAMMPS plugin and built-in modes, and make the plugin load step explicit when it is needed.
- Keep type mapping, masses, units, ensemble settings, model deviation, and special model inputs visible before execution.
- Choose the right native API surface for C, C++, header-only C++, Node.js, ASE, or dpdata callers.
- Plan repository edits with targeted tests, timeouts, linting, and commit-message expectations from the maintainer guidance.

## Minimum Intake

For LAMMPS, collect or infer:

- Frozen model path or paths, including whether the first model is the production model and later models are deviation-only checks.
- LAMMPS data file, atom-style needs, element order, and whether the data file already defines masses.
- Unit style, ensemble, temperature, pressure when needed, timestep, run length, and output cadence.
- Whether the available LAMMPS build uses `plugin load` or a built-in USER-DEEPMD package.
- Whether the model expects `fparam`, `aparam`, `charge_spin`, spin atom style, long-range electrostatics, or tensor computes.

For native integration, collect:

- Target language/API: C++ library, C ABI, header-only C++ wrapper, Node.js, ASE, or dpdata.
- Model backend and artifact format, plus the backend runtime libraries that must be discoverable at link and run time.
- Array shape conventions, atom type mapping, cell/PBC assumptions, and whether the caller needs model deviation or custom neighbor lists.

For repository development, collect:

- Files or subsystem being changed, expected backend impact, and whether C++/LAMMPS/i-PI/Node.js components are in scope.
- Existing environment state and whether dependency installation or rebuilds are allowed.
- The smallest targeted validation that can cover the change without running the full suite.

## LAMMPS Workflow

1. Decide plugin vs built-in mode. Plugin mode needs `plugin load libdeepmd_lmp.so` or a configured plugin search path; built-in mode does not.
2. Prefer `units metal` unless the user has a reason to use another supported LAMMPS unit style. Do not use `lj` units.
3. Use `pair_style deepmd` for ordinary potential models and `pair_style deepspin` for spin models.
4. Put all production and deviation model files on the `pair_style` line. Only the first model drives forces; additional models support deviation output.
5. Use one `pair_coeff * * ...` line to map LAMMPS atom types to model element names, or intentionally omit names only when relying on a model type map.
6. Ensure masses are present in the data file or emitted with `mass` commands before velocity creation or thermostats.
7. Add `out_file`, `out_freq`, `atomic`, `relative`, `relative_v`, `fparam`, `fparam_from_compute`, `fparam_from_fix`, `aparam`, `aparam_from_compute`, or `charge_spin` only when the model was trained/exported for those inputs.
8. For spin simulations, use spin-aware LAMMPS atom styles and fixes; remember spin models do not support virial and atomic virial in the same way as standard `deepmd` models.
9. Review [LAMMPS and i-PI](references/lammps-ipi.md) for syntax details and [Troubleshooting](references/troubleshooting.md) before executing.

## Bundled LAMMPS Input Helper

Use [write_lammps_deepmd_input.py](scripts/write_lammps_deepmd_input.py) when the user asks for a conservative starter input:

```bash
python scripts/write_lammps_deepmd_input.py \
  --model graph_0.pb graph_1.pb \
  --data data.system \
  --elements O H \
  --masses O:15.999 H:1.008 \
  --ensemble nvt \
  --temp 330 \
  --timestep 0.0005 \
  --steps 1000 \
  --model-deviation-file md.out \
  --model-deviation-freq 10
```

The helper prints LAMMPS input to stdout only. It does not run LAMMPS, inspect model files, or mutate the working tree.

## i-PI Workflow

- Use i-PI when the server integrates path-integral replicas and DeePMD-kit supplies the client-side force/energy/virial evaluator.
- Plan two processes: the i-PI server with its XML input, then one or more `dp_ipi` clients using a JSON config.
- Match socket mode, host, and port between the XML server input and the DeePMD-kit client JSON.
- The client JSON needs a frozen model file, a coordinate XYZ file used for atom names, and an atom-name to DeePMD type-index map.
- If `dp_ipi` is unavailable, treat it as a build capability problem, not a user input problem; see [Troubleshooting](references/troubleshooting.md).

## Native APIs

Use [Native APIs](references/native-apis.md) for compact examples and compile/link patterns.

- Prefer the C++ `deepmd::DeepPot` API when ABI compatibility is under control and C++ integration is desired.
- Prefer the C ABI or header-only C++ wrapper when a stable ABI boundary matters.
- Use Node.js only when the Node wrapper is installed or when the task explicitly covers building that wrapper.
- Use ASE's `deepmd.calculator.DP` when the caller wants an ASE `Atoms` calculator.
- Use dpdata's `predict(..., driver="dp")` when the caller wants DeePMD-labeled systems from dpdata objects.
- Keep direct Python inference-array work in [inference-model-ops](../inference-model-ops/SKILL.md).

## Repository Development Workflow

Use [Repository Development](references/repo-development.md) for exact commands and timeouts.

- Start from a narrow impact analysis: CLI parser, Python backend, LAMMPS plugin, i-PI driver, C/C++ API, Node.js wrapper, docs, or tests.
- Install only the dependencies needed for the affected backend or component.
- Prefer single tests and subsystem tests over the full suite; the full test suite is intentionally avoided during normal development.
- For C++ component work, verify backend roots before building, then allow a long enough timeout for the C++ build.
- Run `ruff check .` and `ruff format .` before handoff when Python files changed.
- Use conventional commit wording if the user asks for a commit message or PR title.

## Execution Guardrails

- Do not launch long training, long MD, full test suites, or C++ builds unless the user has authorized the time/cost.
- If validating a simulation input, prefer syntax review or a very short smoke run before production-length runs.
- Do not guess cluster module names, MPI launchers, GPU binding, or LAMMPS executable names; ask or inspect local commands.
- Treat backend-missing errors as installation/build-routing issues rather than editing the generated input blindly.
- Keep model paths, data paths, library roots, and environment variables user-provided or locally discovered at run time; never bake machine-specific paths into reusable instructions.

## Troubleshooting Entry Points

- LAMMPS cannot find `deepmd` or `deepspin`: check plugin load, built-in package support, and library search paths.
- `units lj` rejected or results look scaled: switch to a supported unit style, usually `metal`.
- LAMMPS stops before running: check `Masses`, `mass` commands, atom type counts, and `pair_coeff` mapping.
- Native program links but fails at run time: check runtime library search paths for DeePMD-kit and backend libraries.
- i-PI client command missing: rebuild with i-PI support enabled.
- MPI/GPU performance or crashes vary by rank: verify the one-MPI-rank-per-GPU expectation and backend device mapping.

## Handoff Checklist

When returning integration work, include:

- Which integration surface was touched or planned.
- Generated input or code files and whether they were executed.
- Model/data/type-map assumptions that still need user confirmation.
- Targeted checks run, skipped checks, and why broader checks were deferred.
- Any routing recommendation to installation, training, or Python inference sub-skills.
