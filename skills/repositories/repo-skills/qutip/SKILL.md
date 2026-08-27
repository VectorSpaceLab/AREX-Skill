---
name: "qutip"
description: "Router for QuTiP quantum-object construction, solver, open-system,
  and visualization workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# QuTiP

QuTiP is the quantum toolbox for constructing quantum objects, evolving open and closed systems, and visualizing quantum states and processes in Python.

Use this skill when the task mentions QuTiP, `Qobj`, `mesolve`, `steadystate`, Bloch spheres, Wigner functions, PIQS, HEOM, `qsave`, or any other QuTiP API.

## Quick start

Install the package you want to use first:

```bash
python -m pip install qutip
```

For the most common interactive workflows, install the plotting and runtime-compilation extras too:

```bash
python -m pip install "qutip[graphics,runtime_compilation,extras]"
```

Minimal sanity check:

```bash
python -c "import qutip; print(qutip.__version__)"
```

If you want a fuller private smoke check, run `scripts/import_and_about.py` after installation.

## Choose a subskill

### `sub-skills/core-objects/`
Use this for `Qobj`, states, operators, tensor products, superoperators, random states, measurements, entropy, metrics, partial transpose, and basic quantum-object manipulation.

### `sub-skills/dynamics-and-solvers/`
Use this for `sesolve`, `mesolve`, `mcsolve`, steady-state solves, `QobjEvo`, time-dependent coefficients, propagators, correlation functions, spectra, Floquet workflows, and solver configuration.

### `sub-skills/specialized-open-systems/`
Use this for PIQS, HEOM, environment models, Bloch-Redfield, transfer-tensor, and other advanced open-system model families.

### `sub-skills/analysis-and-io/`
Use this for Bloch spheres, Hinton plots, Wigner and quasi-probability plots, tomography, animation, file I/O, `about()`, `cite()`, and notebook helper workflows.

## When workflows span multiple subskills

- Build `Qobj` inputs with `core-objects`, then route the evolution to `dynamics-and-solvers`.
- If a solver result must be plotted or saved, use `analysis-and-io` after the dynamics step.
- If the model starts with a bath, Dicke basis, or HEOM hierarchy, begin in `specialized-open-systems`, then return to `dynamics-and-solvers` only for generic solver mechanics.
- If a plotting failure is caused by a malformed `Qobj`, diagnose the object in `core-objects` before changing Matplotlib code.

## Do not use this skill when

- The task is only generic NumPy/SciPy array manipulation with no QuTiP objects or APIs.
- The task is source-repository maintenance, release engineering, or contributing to QuTiP internals rather than using the package.
- The task needs the external `qutip-qip` package specifically; treat that as a separate package dependency.

## Cross-cutting references

Read these when you need package-wide context rather than one workflow:

- `references/installation.md` for install variants, optional extras, and import checks.
- `references/api-index.md` for a compact map of the main public entry points.
- `references/workflows.md` for short end-to-end examples that show how the subskills fit together.
- `references/troubleshooting.md` for import, build, plotting, coefficient-compilation, and backend issues.
- `references/repo-provenance.md` for source revision details.

## Runtime conventions

- Use `qutip.about()` when you need a quick environment and dependency summary.
- Use `qutip.settings` when solver, cache, CPU-count, or plotting behavior looks surprising.
- Prefer the subskill that matches the primary workflow; do not dump every QuTiP topic into one answer.
- Keep generated instructions self-contained; do not rely on the original checkout remaining available.

## Bundled helper

- `scripts/import_and_about.py` — prints a quick import-and-version report with `qutip.about()`.
