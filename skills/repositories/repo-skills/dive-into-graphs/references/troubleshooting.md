# Cross-Cutting Troubleshooting

## Import Fails for `dig` or Public Submodules

Symptoms:
- `ModuleNotFoundError: No module named 'dig'`.
- `ModuleNotFoundError` for `torch_geometric`, `torch_scatter`, `rdkit`, `captum`, `gdown`, `pygmtools`, `ogb`, `pyscf`, or `hydra`.

Actions:
1. Confirm the install package is `dive-into-graphs` but imports use `dig`.
2. Run `python ../scripts/check_dig_environment.py --json` when reading from this `references/` directory, or run the same script from the skill root.
3. Install PyTorch first, then PyG and extension wheels matching that PyTorch build, then DIG and workflow-specific packages.
4. If only one workflow is needed, install only that workflow's dependencies rather than every optional research package.

## PyG Extension Mismatch

Symptoms:
- Import errors mentioning `torch_scatter`, `torch_sparse`, `torch_cluster`, or `torch_spline_conv`.
- Shared object or undefined symbol errors after changing PyTorch versions.

Actions:
- Reinstall all PyG extension wheels from the same wheel index for the exact torch version and backend.
- Do not mix CUDA extension wheels with CPU-only PyTorch.
- Re-run the environment check after reinstalling.

## Dataset Constructor Downloads Unexpectedly

Many DIG dataset constructors download or process data during object initialization. If a task is only asking for code, shape checks, or routing, avoid constructing real datasets. Use tiny PyG fixtures or bundled smoke scripts first. If data is required, ask for a writable dataset root and network approval.

## CUDA Assumptions

Symptoms:
- `AssertionError: Torch not compiled with CUDA enabled`.
- `RuntimeError: Found no NVIDIA driver`.
- `.cuda()` failures in Graphair or S-Mixup.

Actions:
- For Graphair and S-Mixup, treat CUDA as required for execution because the source code directly calls `.cuda()`.
- For GraphAF, GraphDF, G-SphereNet, and some GraphAug runners, set model/config `use_gpu` false or run on CPU only for small checks when the code supports fallback.
- Do not report a CUDA-specific capability as verified from CPU-only imports.

## RDKit or Chemistry Validity Issues

Symptoms:
- RDKit sanitization warnings, invalid valence, `None` molecules, low validity ratios.
- Property optimization evaluator asserts because fewer than three valid molecules exist.

Actions:
- Disable noisy RDKit logs only after confirming errors are expected.
- Use `dig.ggraph.utils.check_chemical_validity`, `check_valency`, and `convert_radical_electrons_to_hydrogens` for diagnosis.
- Ensure evaluator input dictionaries use RDKit `Chem.Mol` objects, not SMILES strings.
- For `PropOptEvaluator`, provide at least three valid molecules.

## PySCF and 3D Property Evaluation Is Slow

`dig.ggraph3D.evaluation.PropOptEvaluator` computes HOMO-LUMO gap or polarizability through PySCF DFT. Treat this as expensive. For a fast smoke check, validate `xyz2mol` and bond validity first; run PySCF property evaluation only for very small molecules and only when the user accepts runtime.

## External Checkpoints Missing

Many generation and explainability recipes require pretrained checkpoints. If a checkpoint path is missing, route to the workflow reference and either train a tiny model for demonstration or ask the user to provide/download the checkpoint. Do not silently replace missing checkpoints with random weights for a claimed reproduction result.

## Large-Scale Graph `dig_ext` Missing

`dig.lsgraph.dataset` and async loader components import `dig_ext.relabel` or `dig_ext.sync`. If `dig_ext` is missing, dataset and loader verification remains blocked until the compiled extension is available. `FeatureMomentum` can be imported from `dig.lsgraph.method.FM`, but CPU-only PyTorch builds can still fail its pinned-memory allocation; report that separately from the missing-extension gap.

## Stale Processed Dataset Caches

DIG datasets use processed `.pt` caches under the chosen root. If a transform, property, task, or feature string changes but the same processed filename remains, remove or rename the processed cache so the dataset reprocesses with the intended settings. Keep destructive cache removal explicit and scoped to the dataset root.
