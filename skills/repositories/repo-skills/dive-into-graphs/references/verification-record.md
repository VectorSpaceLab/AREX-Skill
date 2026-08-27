# DIG Skill Verification Record

## Construction Summary

- Candidate skill id: `dive-into-graphs`.
- Canonical import namespace: `dig`.
- Source package version: `1.0.0`.
- Source commit: `21476b079c9226f38915dcd082b5c2ee0cddaac8` on branch `dig-stable`.
- User import policy: not imported after verification.
- Extraction scope: broad DIG operating guidance for 2D molecular generation, 3D graph learning and 3D generation, graph SSL, GNN explainability, GOOD OOD datasets, graph augmentation, fair graph learning, and large-scale graph workflows.

## Generated Graph

- Root skill: `SKILL.md`.
- Root references: provenance, capability map, installation/backend notes, troubleshooting, routing metadata, and this verification record.
- Root diagnostic script: `scripts/check_dig_environment.py`.
- Sub-skills:
  - `molecular-graph-generation`
  - `three-d-graphs`
  - `self-supervised-learning`
  - `graph-explainability`
  - `good-ood-datasets`
  - `graph-augmentation`
  - `fair-graph-learning`
  - `large-scale-graphs`

## Verification Environment

Verification used an isolated Python 3.8 CPU inspection environment with:

- `torch 2.1.0+cpu`
- `torch-geometric 2.5.3`
- `rdkit 2022.09.5`
- editable DIG source install for the inspected checkout
- CUDA unavailable (`cuda_available=False`)

The public skill deliberately avoids embedding local environment paths.

## Verification Commands and Outcomes

From the skill root:

```bash
python scripts/check_dig_environment.py --json
python sub-skills/molecular-graph-generation/scripts/molecule_generation_smoke.py
python sub-skills/three-d-graphs/scripts/three_d_smoke.py
python sub-skills/self-supervised-learning/scripts/sslgraph_smoke.py
python sub-skills/graph-explainability/scripts/xgraph_metric_smoke.py
python sub-skills/good-ood-datasets/scripts/good_metadata_check.py
python sub-skills/graph-augmentation/scripts/augmentation_config_smoke.py
python sub-skills/fair-graph-learning/scripts/fairgraph_smoke.py
python sub-skills/large-scale-graphs/scripts/lsgraph_feature_momentum_smoke.py
```

Observed results:

- Environment diagnostic exited successfully and imported primary `ggraph`, `ggraph3D`, `sslgraph`, `xgraph`, `threedgraph`, `oodgraph`, `auggraph`, and `fairgraph` surfaces.
- Molecular smoke passed with in-memory RDKit molecules and tiny one-shot tensors.
- 3D smoke passed with a tiny MAE evaluator check and one generated water geometry validity check.
- SSL smoke passed one tiny GraphCL pretraining epoch on synthetic PyG graphs.
- XGraph smoke passed a tiny edge-mask metric check.
- GOOD metadata smoke passed by importing all GOOD dataset classes and signatures without downloads.
- Augmentation smoke passed by applying `DegreeTrans` and `AUG_trans` to synthetic PyG graphs.
- Fairgraph smoke passed metric and sparse-conversion helper checks without constructing NBA/POKEC datasets.
- Large-scale smoke exited successfully while explicitly reporting the unresolved `dig_ext` import gap and a CPU pinned-memory allocation limitation for `FeatureMomentum` in the inspection backend.
- `references/repo-routing-metadata.json` parsed as valid JSON.
- All `SKILL.md` files include frontmatter and `disable-model-invocation: true`.

## Verification Boundaries

Not run by default:

- Dataset constructors that trigger downloads for QM9/ZINC/MOSES, QM93D/MD17, TU Dortmund, Planetoid, GOOD, NBA/POKEC, OGB, Reddit, Flickr, Yelp, or protein hdf5 inputs.
- Full training, generation, checkpoint loading, notebook, benchmark, or PySCF property sweeps.
- CUDA-specific Graphair and S-Mixup execution.
- Large-scale graph loaders requiring compiled `dig_ext`.

## Known Gaps

- `known-gap dig.lsgraph.dataset ModuleNotFoundError No module named 'dig_ext'`.
- `FeatureMomentum` may raise `RuntimeError: Pinned memory requires CUDA` in CPU-only PyTorch builds because the source allocates CPU pinned memory.
- Graphair and S-Mixup include hard-coded `.cuda()` paths; CPU smoke checks do not validate those execution paths.
- Native tests and examples were treated as source evidence only unless represented by a safe synthetic smoke script.
