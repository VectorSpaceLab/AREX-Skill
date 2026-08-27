---
name: deepchem
description: "Use DeepChem for molecular machine learning, data loading,
  featurization, model training, MoleculeNet, docking, and optional backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepChem

Use this skill when a task involves the DeepChem Python package: molecular machine learning, drug-discovery or life-science datasets, molecule featurization, MoleculeNet loaders, model training/evaluation, structure/docking workflows, or optional TensorFlow/PyTorch/JAX/DQC dependency issues.

DeepChem is broad. Start here for routing, installation checks, and cross-cutting troubleshooting, then open the focused sub-skill for the workflow.

## Quick Start

```python
import deepchem as dc
print(dc.__version__)
```

For a minimal core install, expect `numpy<2`, `pandas`, `scikit-learn`, `scipy>=1.10.1`, `sympy`, `joblib`, and `rdkit`. Neural, docking, materials, and quantum workflows often need optional extras or external binaries.

Read `references/installation.md` when the request mentions installation, optional extras, backend warnings, CUDA, Colab, conda, or from-source setup. Read `references/troubleshooting.md` when imports succeed but DeepChem prints missing optional dependency warnings.

## Route By Task

- Data loading, MoleculeNet, splitters, transformers, CSV/SDF/FASTA/image/numpy datasets: use `sub-skills/data-and-molnet/`.
- Featurizer selection, molecule fingerprints, graph features, RDKit descriptors, sequences, materials, polymers, or invalid SMILES diagnostics: use `sub-skills/featurization/`.
- Model fitting, metrics, predictions, save/restore, callbacks, hyperparameter search, or model-family selection: use `sub-skills/model-training/`.
- Protein-ligand structures, binding pockets, docking, PDB/PDBQT/SDF preparation, materials/DFT dependency triage, or external docking binaries: use `sub-skills/docking-and-structure/`.

If a user asks for an end-to-end molecular property workflow, combine the route order: `data-and-molnet` for loading/splitting, `featurization` for representation choice, then `model-training` for model/metric/evaluation. If a user asks for PDBBind, protein-ligand interactions, or docking scores, start in `docking-and-structure`, then route back to data/model sub-skills only after the structure-specific inputs are clear.

## Common Workflows

- **Tiny molecular ML baseline:** load a CSV with `CSVLoader`, choose `CircularFingerprint` or `RDKitDescriptors`, split with `RandomSplitter` or `ScaffoldSplitter`, train a `SklearnModel`, and evaluate with `Metric`.
- **MoleculeNet dataset:** use `dc.molnet.load_*` only when downloads/cache are acceptable; otherwise build a small local fixture and follow `data-and-molnet` to avoid network surprises.
- **Graph neural model plan:** use `featurization` to confirm `MolGraphConvFeaturizer` output and `model-training` to check whether torch/tensorflow/jax/DGL extras are installed before selecting a neural model.
- **Docking or pocket workflow:** use `docking-and-structure` to check file formats and optional Vina/GNINA/OpenMM/PDBFixer/MDTraj dependencies before promising executable docking.

## Bundled Checks

Run these skill-owned helpers from any environment where DeepChem is installed:

```bash
python sub-skills/data-and-molnet/scripts/load_tiny_csv_dataset.py
python sub-skills/data-and-molnet/scripts/split_tiny_dataset.py
python sub-skills/featurization/scripts/inspect_featurizer_outputs.py --smiles CCO c1ccccc1
python sub-skills/model-training/scripts/train_tiny_sklearn_model.py
python sub-skills/docking-and-structure/scripts/check_structure_dependencies.py
```

Use `scripts/deepchem_environment_report.py` for a cross-cutting import/version/optional dependency summary before debugging user environments.

## Important References

- `references/installation.md`: install modes, extras, and dependency expectations.
- `references/troubleshooting.md`: cross-cutting import, optional dependency, data, and workflow failures.
- `references/repo-provenance.md`: source snapshot and evidence paths used to generate this skill.

## Boundaries

This skill is for using DeepChem as a package, not for maintaining DeepChem releases, CI, Docker images, or legacy `contrib/` experiments. It intentionally treats large benchmarks, notebooks, remote dataset downloads, and GPU training as opt-in workflows rather than default verification paths.
