---
name: three-d-graphs
description: "Use DIG for 3D graph learning and 3D molecular geometry
  generation: QM93D, MD17, ECdataset, FOLDdataset, SchNet, DimeNet++, SphereNet,
  ComENet, ProNet, and G-SphereNet."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Three-D Graphs

Use this sub-skill for DIG workflows that model 3D graph geometry, molecular properties, or protein structures.

## Include

- `dig.threedgraph.dataset`: `QM93D`, `MD17`, `ECdataset`, `FOLDdataset`.
- `dig.threedgraph.method`: `run`, `SchNet`, `DimeNetPP`, `SphereNet`, `ComENet`, `ProNet`.
- `dig.threedgraph.evaluation`: `ThreeDEvaluator`.
- `dig.threedgraph.utils`: `xyz_to_dat`.
- `dig.ggraph3D`: `QM93DGEN`, `collate_fn`, `G_SphereNet`, random generation, target-property optimization, and bond-length/geometry evaluation.

## Exclude

- 2D molecule generation, RDKit property optimization, or SMILES workflows: use `../molecular-graph-generation/SKILL.md`.
- SSL, explainability, OOD, augmentation, fairness, or large-scale graph workflows: route to sibling sub-skills.

## Start Here

- Read `references/workflows.md` for the 3D property-prediction and 3D-generation flows.
- Read `references/data-formats.md` for QM93D, MD17, EC/FOLD, and QM93DGEN input layouts.
- Read `references/troubleshooting.md` when hdf5 layouts are wrong, PySCF is slow, or a model config expects GPU.
- Run `scripts/three_d_smoke.py` for a safe import-and-evaluator smoke check.

## Core Workflows

- **3D property prediction**: load QM93D or MD17, split with the provided helper, and train `SchNet`, `DimeNetPP`, `SphereNet`, `ComENet`, or `ProNet` using the `run` wrapper and `ThreeDEvaluator`.
- **Protein graph classification**: use `ECdataset` or `FOLDdataset` with `ProNet` and the 3D runner.
- **3D molecule generation**: use `QM93DGEN`, `collate_fn`, and `G_SphereNet` to train or generate 3D molecular geometries.
- **3D generation evaluation**: use `dig.ggraph3D.evaluation.RandGenEvaluator` and `PropOptEvaluator` for validity and property summaries.

## Quick Validation

```bash
python scripts/three_d_smoke.py --help
python scripts/three_d_smoke.py
```

The smoke script only imports public APIs and evaluates a tiny MAE example plus a tiny 3D validity example.
