# Installation and Backend Notes

## Package Names

- Install name: `dive-into-graphs`.
- Import root: `dig`.
- Source package version captured for this skill: `1.0.0`.
- Core runtime family: PyTorch, PyTorch Geometric, RDKit, SciPy/NumPy/Pandas, and task-specific graph/chemistry packages.

## Recommended Setup Order

1. Create an isolated Python environment.
2. Install a PyTorch build for the target backend.
3. Install PyG and any PyG extension wheels that match the exact PyTorch/backend build.
4. Install RDKit.
5. Install DIG.
6. Run the bundled environment check.

Example CPU-oriented sequence:

```bash
python -m pip install torch torch-geometric
python -m pip install rdkit-pypi dive-into-graphs
python ../scripts/check_dig_environment.py --json
```

For PyG extension-heavy workflows, install matching wheels for `torch-scatter`, `torch-sparse`, `torch-cluster`, and `torch-spline-conv` from the appropriate PyG wheel index for the selected PyTorch version and backend. Do not mix CPU PyTorch with CUDA PyG extension wheels, and do not mix extension wheels from a different torch minor version.

## Core Dependencies by Surface

| Surface | Required packages beyond Python stdlib | Notes |
| --- | --- | --- |
| `dig.ggraph` | `torch`, `torch_geometric`, `rdkit`, `numpy`, `pandas`, `networkx`, `scipy` | 2D molecular generation and RDKit metrics. |
| `dig.ggraph3D` | `torch`, `torch_geometric`, `rdkit`, `numpy`, `networkx`, `scipy`, `pyscf` for property evaluation | G-SphereNet generation can run with CPU if model config disables GPU; PySCF property evaluation is expensive. |
| `dig.sslgraph` | `torch`, PyG extensions such as `torch-scatter`, `torch-sparse`, `torch-cluster`; `scikit-learn` for evaluators | Dataset loaders often download TU/Planetoid data. |
| `dig.xgraph` | `torch`, `torch_geometric`, `captum==0.2.0`, `shap`, `networkx`, `rdkit` for molecule datasets | Checkpoints and datasets are external; metrics can be tested on tiny local graphs. |
| `dig.threedgraph` | `torch`, `torch_geometric`, `torch-scatter`, `torch-sparse`, `scikit-learn`, `h5py`, `tensorboard` | QM9/MD17 download data; protein datasets require user-provided hdf5 layouts. |
| `dig.oodgraph` | `torch`, `torch_geometric`, `gdown`, `munch`, RDKit for molecule datasets | GOOD datasets download from Google Drive-style URLs. |
| `dig.auggraph` | `torch`, `torch_geometric`, `scikit-learn`, `pygmtools` for graph matching workflows | GraphAug chooses CPU or CUDA automatically; S-Mixup source hardcodes CUDA in several places. |
| `dig.fairgraph` | `torch`, `scipy`, `pandas`, `torch_geometric` | Dataset classes and Graphair methods hardcode `.cuda()`; use real CUDA for execution. |
| `dig.lsgraph` | `torch`, PyG extensions, `ogb`, and missing compiled `dig_ext` | Dataset/loader and async surfaces can fail without `dig_ext`; `FeatureMomentum` can additionally hit CPU pinned-memory backend errors. |

## Backend Criticality

- CPU is adequate for import checks, evaluator unit checks, most documentation-level guidance, small PyG fixture tests, and 2D/3D evaluator smoke checks.
- CUDA is required to truthfully validate Graphair execution because the dataset and model code call `.cuda()` directly.
- CUDA is required to truthfully validate S-Mixup training because the implementation calls `.cuda()` on models and batches without a CPU fallback.
- Large-scale graph async loaders require both PyG sparse extensions and a `dig_ext` compiled extension. Missing `dig_ext` is a package/runtime limitation, not a generic Python import issue; `FeatureMomentum` may also fail in CPU-only builds due its pinned-memory allocation.
- G-SphereNet, GraphAF, and GraphDF have `use_gpu` switches in model configuration and can often fall back to CPU for small API checks, but full training/generation validation is still expensive and checkpoint-dependent.

## Data and Network Policy

Many DIG constructors trigger downloads during initialization. Before instantiating datasets in automation, determine whether the user accepts network and disk writes. Common download surfaces include:

- Molecular CSVs for `QM9`, `ZINC250k`, `ZINC800`, and `MOSES` in `dig.ggraph`.
- QM9/MD17 archives for `dig.threedgraph`.
- Google Drive-style GOOD dataset archives in `dig.oodgraph`.
- NBA/POKEC fairness data.
- TU Dortmund graph datasets and Planetoid datasets for `dig.sslgraph` and `dig.auggraph`.
- External xgraph checkpoints and datasets.

## Safe Validation Ladder

1. Run `python ../scripts/check_dig_environment.py --json` when reading from this `references/` directory, or run the same script from the skill root.
2. Run sub-skill smoke scripts that use tiny in-memory graphs or evaluators.
3. Only then run package dataset constructors that download data.
4. Only after data and backend are ready, run short native tests or examples.
5. Reserve full training, benchmark notebooks, PySCF property sweeps, and large OGB datasets for explicit user approval.
