---
name: docking-and-structure
description: "Handle DeepChem protein-ligand docking, binding pocket discovery,
  complex structure featurization, material featurizers, DFT surfaces, and
  optional dependency triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepChem Docking and Structure

Use this sub-skill when a user asks about protein-ligand complexes, binding pockets, docking poses/scores, PDB/PDBQT/SDF structure inputs, complex featurizers, material/crystal featurizers, DFT/XC models, or missing optional structural dependencies.

## Route First

- For molecule fingerprints, graph featurizers, descriptors, or ordinary SMILES-only featurization, use `../featurization/` instead.
- For PDBBind, MolNet dataset loading, splits, transformers, or `DiskDataset` handling, use `../data-and-molnet/` unless the question is specifically about structure featurizers or docking inputs.
- For model training loops, metrics, hyperparameters, or checkpointing, use `../model-training/` after choosing the structure featurizer or docking output here.
- Do not promise docking in a base DeepChem install. Treat Vina, GNINA, `mdtraj`, `pymatgen`, `matminer`, `torch`, `dqc`, OpenMM/PDBFixer, CUDA, and docking binaries as environment gates.

## Fast Decisions

- Need candidate pockets only: use `deepchem.dock.ConvexHullPocketFinder(scoring_model=None, pad=5.0)` and validate a protein structure can be loaded.
- Need actual poses/scores: use `deepchem.dock.VinaPoseGenerator` or `deepchem.dock.GninaPoseGenerator`, then wrap with `deepchem.dock.Docker` only when a generic pose/scoring pipeline is needed.
- Need fixed complex features for ML: choose `AtomicConvFeaturizer`, `RdkitGridFeaturizer`, `ContactCircularFingerprint`, `SplifFingerprint`, or voxelizers based on the downstream model shape.
- Need pocket residue summaries: use `BindingPocketFeaturizer`, but require `mdtraj` and pockets from a pocket finder.
- Need crystal/material features: choose composition featurizers for formulas/compositions and structure featurizers for `pymatgen.core.Structure` objects.
- Need DFT/XC surfaces: confirm `torch` and DFT quantum chemistry extras before importing DFT modules or creating `XCNNSCF`/`XCModel` workflows.

## Required References

- `references/structure-workflows.md`: choose pocket finding, docking, complex featurization, material featurization, or DFT.
- `references/api-reference.md`: key DeepChem APIs, expected inputs, outputs, and dependency notes.
- `references/optional-dependencies.md`: dependency and binary gates before running structural workflows.
- `references/troubleshooting.md`: common failures for formats, hydrogens, sanitization, optional imports, GPU/CUDA, and DFT extras.

## Bundled Helper

Run `python scripts/check_structure_dependencies.py` from this sub-skill directory, or copy the script into any project, to report available Python packages and external `vina`/`gnina` commands without running docking.
