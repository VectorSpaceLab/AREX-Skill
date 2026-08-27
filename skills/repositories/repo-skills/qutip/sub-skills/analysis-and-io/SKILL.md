---
name: "analysis-and-io"
description: "QuTiP visualization, phase-space analysis, tomography, file I/O,
  and reporting workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Analysis and I/O

Use this subskill when the task is about turning QuTiP objects or solver results into plots, saved artifacts, process tomography, environment summaries, or citation output.

## Read this subskill when the prompt mentions

- `Bloch`, Bloch sphere plots, vectors, arcs, points, or qubit-state visualization
- `hinton`, `matrix_histogram`, `plot_wigner`, `plot_qfunc`, `plot_fock_distribution`, `plot_expectation_values`
- `wigner`, `qfunc`, spin Wigner functions, quasi-probability distributions, or harmonic-oscillator probability functions
- `qpt`, process tomography, `qpt_plot`, or `qpt_plot_combined`
- `qsave`, `qload`, `file_data_store`, `file_data_read`
- `about()`, `cite()`, `ipynbtools.version_table`, or notebook/reporting helpers

## What to decide first

1. Is the user trying to visualize a state, an operator, a process, or solver result data?
2. Does the environment have Matplotlib, and is a headless backend needed?
3. Is the task about a saved QuTiP object (`.qu`) or plain numeric data?
4. Does the task need a reusable artifact or only a quick diagnostic plot?

## Core workflow

- Set a non-interactive Matplotlib backend before plotting in headless runs.
- Build or receive a valid `Qobj` first; plotting helpers do not fix object dimensions.
- Pass explicit `fig` and `ax` objects when embedding plots into a larger script.
- Use `qsave` / `qload` for QuTiP objects and `file_data_store` / `file_data_read` for raw numeric arrays.
- Use `about()` for environment summaries and `cite()` for publication reminders.

## Typical success signals

- Plot helpers return a Matplotlib `Figure` and `Axes` or an animation object.
- Saved `Qobj` objects round-trip through `qsave` and `qload`.
- Basis labels have the same length as the plotted matrix axes.
- `about()` reports the package and dependency versions from the active interpreter.

## Boundaries

Use this subskill for analysis artifacts after a valid object or result exists. Do not use it as the main route for:

- Building the Hamiltonian, state, or measurement operators; use `core-objects` first.
- Choosing a solver or fixing time-dependent coefficient logic; use `dynamics-and-solvers`.
- PIQS, HEOM, or bath-model construction; use `specialized-open-systems` before plotting or saving outputs.

## Answer shape

When responding from this subskill, give:

1. The correct plotting, phase-space, file I/O, or reporting API.
2. The minimal object/result shape expected by that API.
3. A headless-safe code snippet if figures are created.
4. The artifact path, file suffix, or return-object type to expect.
5. A cleanup step such as closing Matplotlib figures or using a temporary directory.

## Validation hints

- Use `matplotlib.use('Agg')` for non-interactive smoke checks.
- Use qubit states for Bloch examples unless the prompt explicitly requires another representation.
- Verify `qsave` / `qload` round trips in a scratch directory before relying on saved data.

## Reference files

- `references/api-reference.md` for plotting, phase-space, file I/O, and reporting entry points.
- `references/workflows.md` for compact plotting and save/load recipes.
- `references/troubleshooting.md` for Matplotlib, basis-label, Bloch-geometry, and `.qu` suffix issues.

## Helper script

- `scripts/visual_io_smoke.py` verifies Matplotlib plotting, Bloch rendering, Wigner calculation, and `qsave`/`qload` round-tripping.
