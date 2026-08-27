# TorchDrug Troubleshooting

## When To Read

Read this for cross-cutting TorchDrug install, import, dependency, backend, and runtime failures before diving into a workflow-specific sub-skill troubleshooting page.

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` while installing `torch-scatter` or `torch-cluster` | PyG extension build ran before PyTorch was installed | Install PyTorch first, then install matching `torch-scatter` / `torch-cluster` wheels for the exact PyTorch and CPU/CUDA tag, then install TorchDrug. |
| `ERROR: Failed building wheel for torch-scatter` | No compatible prebuilt wheel for the Python/PyTorch/CUDA platform, or build isolation cannot see PyTorch | Use Python `<3.11`, match the official PyG wheel index, or use conda channels that solve PyTorch/PyG together. Avoid Python 3.11+ for TorchDrug 0.2.1. |
| `ImportError`, `undefined symbol`, or segfault from PyG extensions | ABI mismatch between PyTorch and extension packages | Reinstall `torch-scatter` and `torch-cluster` for the installed PyTorch version and CUDA/CPU build. Verify with `python scripts/check_torchdrug_env.py --optional`. |
| NumPy/RDKit/PyTorch warning about modules compiled for NumPy 1.x | NumPy 2.x with older compiled packages | Pin `numpy<2` when using older TorchDrug/RDKit/PyTorch stacks. |
| `pkg_resources` missing from `torch.utils.cpp_extension` | Very new setuptools removed legacy import surface used by older PyTorch | Pin `setuptools<81` or use a PyTorch version that no longer imports `pkg_resources`. |
| Python version resolver failure | TorchDrug declares `python_requires >=3.7,<3.11` | Use Python 3.7-3.10. Python 3.10 is the safest modern choice for inspection and usage. |

## Backend And Hardware

- Use CPU for smoke tests unless the user specifically asks for GPU training. Most route, data, and planning checks do not need CUDA.
- If using CUDA, match PyTorch, CUDA runtime, `torch-scatter`, and `torch-cluster` as one stack. A visible NVIDIA GPU is not enough; the installed PyTorch wheel must be CUDA-enabled and compatible with the driver.
- On Apple silicon, use CPU. TorchDrug documentation says it does not support `mps` devices.
- On Windows, TorchDrug documentation expects Visual Studio build tools for JIT compilation; if extension builds fail, verify the compiler environment before debugging TorchDrug code.

## Data Downloads And External Assets

- Built-in datasets often download archives into the provided `path`; do not run dataset constructors unless network/storage is allowed.
- ESM workflows may need `fair-esm` and model weights. If weights are not already cached or provided, stop and ask before downloading.
- Benchmark and tutorial-scale training can be minutes to hours and may need GPUs. Use sub-skill planner scripts or tiny in-memory datasets for safe planning.

## Routing Failures

- If the user mentions SMILES, `MoleculeDataset`, `PackedGraph`, split helpers, or collators, start at `sub-skills/graph-data/`.
- If the user mentions `core.Engine`, checkpoints, config JSON, `Registry`, optimizer, or task methods, start at `sub-skills/training-engine/`.
- If the user mentions GIN/RGCN/GraphAF/GearNet architecture internals, message passing, or variadic functions, start at `sub-skills/layers-and-extensions/`.
- If the user mentions ClinTox, BACE, ZINC250k, USPTO50k, GCPN, GraphAF, or G2Gs, start at `sub-skills/molecular-workflows/`.
- If the user mentions triples, FB15k, WN18, RotatE, NeuralLP, KBGAT, or filtered ranking, start at `sub-skills/knowledge-graphs/`.
- If the user mentions ProteinNet, AlphaFoldDB, EnzymeCommission, contact prediction, GearNet protein geometry, ESM, or PPI, start at `sub-skills/protein-workflows/`.
