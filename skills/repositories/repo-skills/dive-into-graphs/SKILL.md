---
name: dive-into-graphs
description: "Use DIG (Dive into Graphs) to load graph-learning datasets, run
  graph generation, self-supervised learning, GNN explainability, 3D graph
  learning, GOOD OOD datasets, graph augmentation, fair graph learning, and
  large-scale graph workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# DIG (Dive into Graphs)

Use this repo skill when a task names DIG, Dive into Graphs, `dive-into-graphs`, the `dig` Python package, or one of DIG's high-level graph-learning modules such as `dig.ggraph`, `dig.sslgraph`, `dig.xgraph`, `dig.threedgraph`, `dig.ggraph3D`, `dig.oodgraph`, `dig.auggraph`, `dig.fairgraph`, or `dig.lsgraph`.

DIG is a research-oriented graph deep learning library layered on PyTorch Geometric. It supplies turnkey datasets, method wrappers, evaluators, and example-style runners for graph generation, SSL, explainability, molecular/protein 3D learning, OOD graph benchmarks, augmentation, fairness, and large-scale graph experiments.

## First Checks

- Read `references/repo-provenance.md` when deciding whether this skill matches a checkout or whether the skill should be refreshed.
- Read `references/verification-record.md` for the generated graph, smoke-check outcomes, and verification boundaries.
- Read `references/installation-and-backends.md` before installing DIG, selecting PyTorch/PyG wheels, deciding CPU vs CUDA coverage, or diagnosing optional dependencies.
- Read `references/capability-map.md` to map DIG package namespaces, datasets, models, evaluators, and examples to the right sub-skill.
- Read `references/troubleshooting.md` for cross-cutting install/import, dataset download, CUDA, RDKit/PySCF, PyG extension, config, and stale-cache problems.
- Run `scripts/check_dig_environment.py --json` for a safe package/import diagnostic that does not download datasets or run training.

## Minimal Install Pattern

DIG uses the PyPI distribution name `dive-into-graphs` and the import package `dig`:

```bash
python -m pip install torch torch-geometric
python -m pip install dive-into-graphs
python - <<'PY'
from dig.version import __version__
import dig.ggraph, dig.sslgraph, dig.xgraph
print(__version__)
PY
```

For most workflows also install RDKit and the PyG extension wheels (`torch-scatter`, `torch-sparse`, `torch-cluster`, `torch-spline-conv`) that match the installed `torch` build. Several DIG modules are importable on CPU; Graphair, S-Mixup, and parts of large-scale graph learning contain CUDA-oriented code paths and need explicit backend planning.

## Route by Task

- **Molecular graph generation**: use `sub-skills/molecular-graph-generation/SKILL.md` for `dig.ggraph`, 2D molecular generation datasets, GraphAF, GraphDF, GraphEBM, JTVAE, one-shot molecule tensors, RDKit validity, random generation, property optimization, and constrained optimization.
- **3D graph learning and 3D molecule generation**: use `sub-skills/three-d-graphs/SKILL.md` for `dig.threedgraph`, QM93D, MD17, EC/FOLD protein datasets, SchNet, DimeNet++, SphereNet, ComENet, ProNet, the 3D runner, and `dig.ggraph3D` / G-SphereNet geometry generation.
- **Self-supervised graph learning**: use `sub-skills/self-supervised-learning/SKILL.md` for `dig.sslgraph`, Contrastive, GraphCL, GRACE, InfoGraph, MVGRL, pGRACE, view functions, TUDataset/Planetoid loaders, and SSL evaluators.
- **GNN explainability**: use `sub-skills/graph-explainability/SKILL.md` for `dig.xgraph`, GNNExplainer, PGExplainer, SubgraphX, GNN-LRP, DeepLIFT, GradCAM, FlowX, synthetic/molecule/sentiment explainability datasets, checkpoint compatibility, and fidelity/sparsity metrics.
- **GOOD OOD graph datasets**: use `sub-skills/good-ood-datasets/SKILL.md` for `dig.oodgraph` dataset loaders, domain/shift/subset choices, returned split dictionaries, metadata, and OOD benchmark dataset troubleshooting.
- **Graph augmentation**: use `sub-skills/graph-augmentation/SKILL.md` for `dig.auggraph`, GraphAug reward/generator/classifier runners, S-Mixup, augmentation configs, degree transforms, subset/triplet datasets, and TUDataset augmentation workflows.
- **Fair graph learning**: use `sub-skills/fair-graph-learning/SKILL.md` for `dig.fairgraph`, NBA/POKEC sensitive-attribute datasets, Graphair training/evaluation, fairness metrics, and CUDA-specific limitations.
- **Large-scale graph workflows**: use `sub-skills/large-scale-graphs/SKILL.md` for `dig.lsgraph`, GraphFMOB / GraphFMIB patterns, large node-classification datasets, METIS partitioning, subgraph loaders, feature momentum, and the `dig_ext` extension gap.

## Shared Decision Rules

- Prefer tiny synthetic PyG `Data` fixtures, evaluator unit checks, and import diagnostics before invoking dataset downloads, long training loops, pretrained checkpoints, or benchmark notebooks.
- Treat `examples/` and notebooks from DIG as evidence for recipes, not as runtime dependencies. Use the bundled scripts in this skill or recreate a small public-API snippet.
- DIG dataset constructors commonly download data during initialization. Ask before running anything that will fetch Google Drive, GitHub storage, TU Dortmund, OGB, QM9, MD17, GOOD, NBA/POKEC, or protein datasets.
- For molecular tasks, distinguish 2D molecule generation (`dig.ggraph`, RDKit molecules, SMILES, validity/novelty/property metrics) from 3D coordinate generation (`dig.ggraph3D`, atom numbers/positions, bond-length MMD, PySCF property evaluation).
- For CUDA-specific modules, do not claim CPU verification proves the selected GPU behavior. If a task uses Graphair, S-Mixup, or async large-scale loaders, require a real CUDA-compatible environment or route to documented limitations.
- When a task spans sub-skills, start with the data owner, then use the method/evaluation owner. Examples: GOOD dataset -> PyG model code; SSL pretraining -> graph generation augmentations; xgraph explanations -> base model/data shape checks.

## Safe Shared Command

```bash
python scripts/check_dig_environment.py --json
```

Use `--require-cuda`, `--check-optional`, or `--fail-on-large-scale-extension-missing` only when the user needs a hard pass/fail diagnostic for those surfaces.

## Avoid

- Do not assume pretrained checkpoints, Google Drive files, OGB data, QM9/MD17 archives, GOOD datasets, NBA/POKEC data, or protein hdf5 files are already available.
- Do not run long training examples or notebooks unless the user explicitly accepts runtime, downloads, result writes, and hardware usage.
- Do not use this skill for generic PyTorch Geometric API design when the task does not involve DIG-specific modules; a PyG-focused skill is usually a better route.
- Do not hide CUDA-only or missing-extension limitations. Surface them before recommending Graphair, S-Mixup, or `dig.lsgraph` execution.
