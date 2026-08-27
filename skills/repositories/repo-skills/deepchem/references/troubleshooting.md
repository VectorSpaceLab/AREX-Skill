# DeepChem Cross-Cutting Troubleshooting

## Import Prints Optional Dependency Warnings

DeepChem imports many optional modules opportunistically. Messages such as missing `torch`, `tensorflow`, `jax`, `pytorch-lightning`, `pytorch-geometric`, or `dqc` are not fatal for base workflows unless the selected model, featurizer, docking, or DFT path requires that backend.

Action:

1. Identify the workflow owner: data, featurization, model training, or docking/structure.
2. Check whether the selected API requires the missing package.
3. If not required, continue with base workflows.
4. If required, install the narrow extra or dependency for that workflow only.

## RDKit Descriptor Normalization Warnings

Warnings like `No normalization for SPS. Feature removed!` can appear when RDKit descriptor normalization tables do not include newer descriptors. This usually affects normalized descriptor sets, not all featurizers. See `sub-skills/featurization/references/troubleshooting.md` before changing the featurizer.

## NumPy Version Problems

DeepChem package metadata pins `numpy<2`. If import or compiled dependency errors mention NumPy ABI, downgrade NumPy below 2 and reinstall affected compiled packages in the same environment.

## Dataset Downloads and Cache Surprises

MoleculeNet loaders can download datasets and cache processed data when `reload=True`. For offline or deterministic tasks, use local CSV/SDF fixtures with `CSVLoader`/`SDFLoader`, or set explicit `data_dir`/`save_dir` after confirming network and storage policy.

## Metric and Shape Errors

Most model errors after fitting are shape or task-mode mismatches:

- Classification metrics often expect probabilities or one-hot labels depending on `Metric` mode and handling options.
- Regression metrics expect continuous predictions with compatible task dimensions.
- Multitask datasets need weights and labels shaped consistently with tasks.

Route detailed fixes to `sub-skills/model-training/references/troubleshooting.md`.

## Optional Docking and Structure Failures

Do not assume base DeepChem can execute docking. Vina/GNINA binaries, Python `vina`, MDTraj, OpenMM, PDBFixer, pymatgen, matminer, torch, DQC, and GPU-capable backend packages are all workflow-specific gates. Run:

```bash
python sub-skills/docking-and-structure/scripts/check_structure_dependencies.py
```

Then follow `sub-skills/docking-and-structure/references/troubleshooting.md`.

## Keep Runtime Workflows Self-Contained

When adapting old DeepChem examples, do not require the original repository checkout. Copy the relevant data schema, code pattern, or tiny fixture into the user's project or use the bundled skill scripts as starting points.
