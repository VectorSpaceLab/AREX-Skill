---
name: dgl-lifesci
description: "Use DGL-LifeSci and dgllife for molecular graph learning, molecule
  featurization, datasets, property prediction, reaction prediction, binding
  affinity, model-zoo/pretrained models, and molecular generation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL-LifeSci

Use this repo skill when a task involves DGL-LifeSci, the `dgllife` Python package, or DGL-based graph neural networks for chemistry and biology.

DGL-LifeSci builds on PyTorch, DGL, RDKit, NumPy/SciPy/Pandas, and scikit-learn. It covers molecule graph construction, featurization, datasets, property prediction, reaction prediction, protein-ligand binding affinity, pretrained/model-zoo architectures, molecule embeddings, link prediction, and molecular generative models.

## Quick Start

Install the public package for normal use:

```bash
pip install dgllife
```

For source checkouts, install from the package directory:

```bash
cd python
python setup.py install
```

Verify imports before deeper work:

```bash
python - <<'PY'
import dgllife
print(dgllife.__version__)
PY
```

For a broader local diagnostic, run:

```bash
python scripts/check_dgllife_environment.py
```

Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout. Read `references/troubleshooting.md` for package-wide import, dependency, data, download, and runtime issues.

## Route By Task

- `sub-skills/molecule-data-prep/SKILL.md`: use for SMILES/CSV/text inputs, RDKit molecule loading, DGL graph construction, atom/bond featurizers, built-in datasets, splits, metric helpers, and tiny fixture validation.
- `sub-skills/property-prediction/SKILL.md`: use for custom CSV supervised prediction, MoleculeNet, Alchemy, PubChem aromaticity, OGB graph property workflows, multitask labels/masks, metrics, and safe config generation.
- `sub-skills/model-zoo-pretraining/SKILL.md`: use for `dgllife.model` constructors, GNN/readout/model-zoo selection, pretrained model names, molecule embeddings, link prediction heads, and constructor signature inspection.
- `sub-skills/reaction-prediction/SKILL.md`: use for WLN reaction center prediction, candidate product ranking, USPTO datasets, atom-mapped reaction SMILES, candidate bond files, and rexgen-direct-style planning.
- `sub-skills/binding-affinity/SKILL.md`: use for PDBBind, local protein-ligand complexes, ACNN, PotentialNet, complex graph construction, ligand/protein file checks, and binding-affinity workflow troubleshooting.
- `sub-skills/generative-models/SKILL.md`: use for DGMG, JTVAE/JTNNVAE, molecular generation/reconstruction, SMILES/vocabulary validation, checkpoints, and generation-specific troubleshooting.

## Common Workflow

1. Classify the task by route above; start in `molecule-data-prep` if raw molecules, labels, or graphs are not yet validated.
2. Check package imports and optional dependencies with `scripts/check_dgllife_environment.py` or the nearest sub-skill helper.
3. Use bundled references for signatures, configs, data formats, and failure modes rather than relying on source checkout examples.
4. Run only tiny offline validations by default. Treat full training, dataset downloads, pretrained checkpoint downloads, PDBBind/USPTO/OGB downloads, benchmarks, and generative training as networked or long-running work that needs explicit user approval.
5. When a task crosses areas, validate inputs first, inspect constructors second, then plan workflow-specific training/evaluation in the owning sub-skill.

## Important Boundaries

- Do not route generic DGL graph operations here unless the task specifically involves DGL-LifeSci/dgllife or chemistry/biology graph workflows.
- Do not run original repository examples or tests as runtime instructions; use the distilled references and bundled helper scripts in this skill.
- Do not assume RDKit is optional for chemistry workflows. Many `dgllife.utils` and dataset paths require RDKit even when top-level import only prints a warning.
- Do not promise GPU execution. Most guidance supports CPU smoke checks; large training can use GPU but should be planned separately.
- Do not overpromise root exports. Verify constructor availability with `model-zoo-pretraining/scripts/inspect_model_constructors.py` when targeting a specific installed `dgllife` version.

## Bundled Repo-Level Resources

- `references/repo-provenance.md`: source snapshot, package version, evidence paths, and refresh checks.
- `references/repo-routing-metadata.json`: structured scenario placement for managed `repo-skills-router` import.
- `references/troubleshooting.md`: cross-cutting DGL-LifeSci install/import/runtime guidance shared by all sub-skills.
- `scripts/check_dgllife_environment.py`: safe import/signature smoke checker for package-wide prerequisites.
