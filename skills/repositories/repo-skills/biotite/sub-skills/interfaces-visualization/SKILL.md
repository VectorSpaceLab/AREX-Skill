---
name: interfaces-visualization
description: "Use Biotite optional interfaces for PyMOL, RDKit, OpenMM,
  Matplotlib-backed graphics, and visualization/export-oriented conversions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Biotite Interfaces and Visualization

Use this sub-skill when the task asks a future agent to move Biotite objects into optional visualization, cheminformatics, or simulation packages: `biotite.interface.pymol`, `biotite.interface.rdkit`, `biotite.interface.openmm`, `biotite.visualize`, `biotite.sequence.graphics`, or `biotite.structure.graphics`.

For preparing `AtomArray`/`AtomArrayStack` objects, bonds, filters, coordinates, boxes, or trajectories before export, route to `../structure-analysis/`. For loading PDB/PDBx/BinaryCIF, MOL/SDF, FASTA/alignment, or trajectory files before plotting/export, route to `../file-io-formats/`. For database downloads or external command wrappers, route to `../database-application/`.

## Start Here

- Read `references/api-reference.md` to choose PyMOL, RDKit, OpenMM, or Matplotlib-backed graphics APIs and understand conversion boundaries.
- Read `references/workflows.md` for safe recipes that avoid assuming optional packages, network access, GUI availability, or display backends.
- Read `references/troubleshooting.md` for missing optional dependencies, PyMOL startup modes, unsupported bond/coordinate conversions, OpenMM unit/template issues, and plotting backend problems.
- Run `scripts/check_optional_interfaces.py --help` to inspect the bundled diagnostic, or run it directly to report optional interface availability without launching GUI-heavy workflows.

## Core Routing Rules

- Treat PyMOL, RDKit, OpenMM, Matplotlib, IPython, ImageMagick, and ffmpeg as optional; check availability before using them.
- Prefer conversion functions over temporary files: `PyMOLObject.from_structure()`, `rdkit.to_mol()`, `rdkit.from_mol()`, `openmm.to_topology()`, `openmm.to_system()`, and `openmm.from_state()`/`from_states()`.
- Keep Matplotlib plotting headless-safe by selecting an appropriate backend before importing `matplotlib.pyplot` in non-interactive scripts.
- Do not bundle or run gallery, animation, network-fetching, or GUI examples by default; treat them as reference recipes to adapt with local inputs.

## Evidence Base

This sub-skill distills the interface tutorials for PyMOL, RDKit, and OpenMM; source modules under `src/biotite/interface/`; plotting helpers in `src/biotite/visualize.py`, `src/biotite/sequence/graphics/`, and `src/biotite/structure/graphics/`; behavior checks in `tests/interface/`; and visualization-heavy examples under `doc/examples/scripts/` used only as reference recipes.
