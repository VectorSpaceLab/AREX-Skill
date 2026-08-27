---
name: molecular-graph-generation
description: "Use DIG's 2D molecular graph generation stack for QM9/ZINC/MOSES
  datasets, GraphAF, GraphDF, GraphEBM, JTVAE, RDKit-based validity checks, and
  property-optimization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Molecular Graph Generation

Use this sub-skill for DIG workflows that generate or optimize 2D molecular graphs and RDKit molecules.

## Include

- `dig.ggraph.dataset`: `QM9`, `ZINC250k`, `ZINC800`, `MOSES`, `PygDataset`.
- `dig.ggraph.method`: `GraphAF`, `GraphDF`, `GraphEBM`, `JTVAE`, `Generator`.
- `dig.ggraph.evaluation`: `RandGenEvaluator`, `PropOptEvaluator`, `ConstPropOptEvaluator`.
- `dig.ggraph.utils`: `check_chemical_validity`, `check_valency`, `calculate_min_plogp`, `reward_target_molecule_similarity`, `gen_mol_from_one_shot_tensor`.
- 2D molecule generation, property optimization, and constrained optimization examples that use RDKit `Mol`/SMILES objects or one-shot atom/bond tensors.

## Exclude

- 3D geometry generation and property evaluation: use `../three-d-graphs/SKILL.md`.
- Self-supervised graph learning: use `../self-supervised-learning/SKILL.md`.
- Explainability: use `../graph-explainability/SKILL.md`.
- Graph OOD, augmentation, fairness, or large-scale loaders: route to sibling sub-skills.

## Start Here

- Read `references/workflows.md` for the three primary generation workflows.
- Read `references/api-reference.md` for constructor names, method names, and helper functions.
- Read `references/troubleshooting.md` when datasets download unexpectedly, RDKit validity is low, or property-evaluator inputs are malformed.
- Run `scripts/molecule_generation_smoke.py` for a safe import-and-evaluator smoke check.

## Core Workflows

- **Random generation**: load a QM9/ZINC250k dataset, train a generator with `train_rand_gen`, then generate molecules with `run_rand_gen` and evaluate with `RandGenEvaluator`.
- **Property optimization**: train or reuse a generator with `train_prop_optim`/`train_prop_opt` and score outputs with `PropOptEvaluator`.
- **Constrained optimization**: use `train_const_prop_opt` and `run_const_prop_opt` to optimize a source molecule while enforcing similarity thresholds with `ConstPropOptEvaluator`.
- **One-shot conversion**: use `gen_mol_from_one_shot_tensor` to convert model outputs back into RDKit molecules, then validate with the RDKit helpers.

## Quick Validation

```bash
python scripts/molecule_generation_smoke.py --help
python scripts/molecule_generation_smoke.py
```

The smoke script only uses tiny in-memory molecules and tensors. It does not download datasets or train models.
