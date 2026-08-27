---
name: visualization
description: "Guides agents drawing Qiskit circuits, histograms, distributions,
  states, backend maps, timelines, pass managers, and optional visualization
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit visualization workflows

Use this sub-skill when the task involves `qiskit.visualization`: circuit drawers, histograms, distributions, state plots, backend/device maps, pass-manager drawings, timelines, output formats, styles, or visualization optional dependencies.

## Read next

- `references/workflows.md` for output-mode, plot, and file-saving recipes.
- `references/troubleshooting.md` for missing `matplotlib`, Graphviz, Pillow, `pylatexenc`, `seaborn`, LaTeX, and style-file failures.
- `../../references/installation.md` for the `visualization` extra.
- `../../scripts/check_qiskit_environment.py --sections visualization` for a source-free plotting smoke check.

## Include here

- `circuit_drawer`, `QuantumCircuit.draw()`, output modes `text`, `mpl`, `latex`, and `latex_source`.
- Counts and distribution plots such as `plot_histogram` and `plot_distribution`.
- State visualizations such as Bloch, city, Hinton, Pauli-vector, and qsphere plots.
- Device/backend maps, circuit layout plots, pass-manager drawings, and timeline views.
- Visualization dependency, style, backend, and file-output troubleshooting.

## Exclude or route elsewhere

- Building the circuit before drawing belongs in `../circuit/SKILL.md`.
- Producing counts or expectation values belongs in `../primitives/SKILL.md` or `../providers/SKILL.md`.
- Mathematical state/operator construction belongs in `../quantum-info/SKILL.md`.
- Backend compilation before layout visualization belongs in `../transpiler/SKILL.md`.

## Default route

Start here when the user mentions drawing, plotting, output format, images, histograms, style JSON, LaTeX, Graphviz, `matplotlib`, or visualizing a backend/circuit layout.

## What to remember

- Qiskit's visualization module intentionally allows some user-controlled labels and external-tool calls; use trusted inputs for LaTeX and Graphviz modes.
- Text drawing is safest and dependency-light; `mpl` and `latex` modes need optional Python and system packages.
- A generated figure object often still needs `savefig()` or a `filename=` argument when the user wants an image file.
