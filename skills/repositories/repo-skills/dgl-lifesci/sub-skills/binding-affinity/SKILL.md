---
name: binding-affinity
description: "Plan DGL-LifeSci protein-ligand binding affinity workflows with
  PDBBind, local complexes, ACNN, PotentialNet, complex graph construction, and
  safe input checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Binding Affinity

Use this sub-skill when a task involves protein-ligand binding affinity prediction with DGL-LifeSci structure-based workflows.

## Use This For

- Planning PDBBind `core` or `refined` workflows without immediately downloading or training on the full dataset.
- Preparing local protein-ligand complexes with ligand files, protein/pocket PDB files, 3D coordinates, and `load_molecule` flags.
- Choosing between `ACNN` and `PotentialNet` and matching each model to the graph object it expects.
- Constructing complex graphs with `ACNN_graph_construction_and_featurization` or `PN_graph_construction_and_featurization`.
- Running safe, local smoke checks on protein/ligand file paths before launching graph construction or training.

## Start Here

1. Read `references/data-formats.md` to validate protein/ligand file formats, PDBBind-style layout, coordinate expectations, and `load_molecule` flags.
2. Run `scripts/check_complex_inputs.py --help`, then check the user's local complex pair before constructing graphs.
3. Read `references/workflows.md` to pick ACNN or PotentialNet, build the PDBBind/local-complex plan, and map graph outputs into model inputs.
4. Use `references/troubleshooting.md` when imports, RDKit parsing, missing conformations, PDBBind paths, config choices, or resource limits fail.

## Quick Commands

Check only file presence and supported extensions:

```bash
python scripts/check_complex_inputs.py --protein pocket.pdb --ligand ligand.sdf
```

Inspect ligand metadata and require a usable 3D conformation for binding graph construction:

```bash
python scripts/check_complex_inputs.py \
  --protein pocket.pdb --ligand ligand.sdf --inspect-ligand --remove-hs
```

## Routing Boundaries

Stay in this sub-skill for PDBBind, local protein-ligand complexes, ACNN/PotentialNet binding models, complex graph construction, binding-specific splits, and safe input checks.

Route elsewhere when the task asks for:

- General SMILES/CSV featurizers, MoleculeNet datasets, splitters, or molecular graph validation: use `../molecule-data-prep/SKILL.md`.
- General model-zoo architecture catalogs, pretrained GIN checkpoints, molecule embeddings, or non-binding model constructors: use `../model-zoo-pretraining/SKILL.md`.
- Generic molecular property prediction loops, metrics, masking, or CSV train/eval workflows: use `../property-prediction/SKILL.md`.

## Bundled Resources

- `references/workflows.md`: PDBBind/local complex workflow planning, ACNN/PotentialNet selection, graph construction contracts, and training-smoke guidance.
- `references/data-formats.md`: supported protein/ligand file formats, coordinates, binding pockets, PDBBind local paths, and configuration flags.
- `references/troubleshooting.md`: import/install, optional dependency, data/config, CLI/API misuse, conformation, RDKit, layout, and resource-limit fixes.
- `scripts/check_complex_inputs.py`: offline helper for protein/ligand existence and extension checks, with optional ligand `load_molecule` metadata inspection.

## Safety Notes

The original binding-affinity example runner is long-running and can trigger PDBBind downloads, multiprocessing molecule loading, GPU/CPU training, and multi-epoch evaluation. Treat it as reference-only; adapt the distilled contracts in this sub-skill and run tiny local checks before any full PDBBind execution.
