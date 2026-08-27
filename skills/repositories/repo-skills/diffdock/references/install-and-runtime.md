# Install And Runtime

## Purpose

Read this before running any DiffDock workflow. It distills the repository setup evidence into runtime prerequisites and safe checks without depending on source docs.

## Runtime Shape

DiffDock exposes script-style Python module entrypoints for core workflows:

- `python -m inference` for docking prediction.
- `python app/main.py` for the Gradio UI when operating inside a DiffDock runtime checkout.
- `python -m train` for score-model training.
- `python -m confidence.confidence_train` for confidence-model training.
- `python -m evaluate` for benchmark evaluation.
- `python -m spyrmsd` for vendored symmetry-aware RMSD checks when its dependencies are available.

Use this skill's bundled helper scripts to construct or validate commands before launching those entrypoints.

## Dependency Families

The documented environment is Python 3.9 with conda-managed scientific/chemistry packages and pip-installed ML packages. Important dependency families are:

| Family | Needed for | Notes |
| --- | --- | --- |
| Torch and PyTorch Geometric | Inference, training, evaluation, datasets, models | Repository pins old CUDA 11.7-era wheels in its environment files. Match wheels to the target hardware and driver. |
| RDKit | Ligand parsing, molecule writing, RMSD utilities | Needed for SDF/MOL2/SMILES handling and many data paths. |
| ProDy and Biopython | Protein parsing and sequence extraction | ProDy is documented as conda-installed; expect legacy version constraints. |
| ESM and OpenFold | Protein-sequence folding and ESM embedding generation | Sequence-mode inference and ESM prep are heavier than PDB input workflows. |
| e3nn and model dependencies | Score/confidence model construction | Required before importing model modules or running training/evaluation. |
| Gradio and requests | Web UI | Gradio is pinned to the 3.50 family in the app requirements. |
| GNINA executable | Optional minimization or docking metrics | External binary, not a Python dependency. Verify separately. |
| W&B | Training/evaluation logging when enabled | Avoid enabling `--wandb` unless the user configured it. |

## Setup Routes

- **Conda:** Use the repository environment file as the closest documented route for full runtime use. It installs Python 3.9, RDKit/ProDy/scipy, CUDA-oriented Torch/PyG wheels, ESM/OpenFold, Gradio, and requests.
- **Docker:** The repository documents a Docker image route for users who prefer containerized execution. GPU execution still depends on host NVIDIA runtime support.
- **CPU-only smoke checks:** PDB-input inference can run on CPU but is slow. Sequence folding, training, and benchmarks are not good CPU smoke tests unless heavily scoped.

## Preflight Helper

From the imported skill root, run:

```bash
python scripts/check_runtime_environment.py --repo-root /path/to/diffdock-runtime --check-gnina
```

The helper checks Python imports, optional CUDA facts, selected files, and GNINA availability without running inference, training, evaluation, downloads, or web services.

## Backend Guidance

- Do not require CUDA merely because the host has a GPU; command construction and input validation do not need it.
- For actual model execution, verify `torch.cuda.is_available()` and a tiny tensor allocation when GPU speed is expected.
- If CUDA is unavailable, lower `--batch_size`, `--samples_per_complex`, and test with PDB inputs before attempting large runs.
- Old pinned CUDA wheels may not work on very new GPUs or drivers; choose wheels compatible with the target environment rather than blindly copying pins.

## Data And Model Assets

This skill does not bundle large assets. Users must provide:

- Score and confidence model directories with `model_parameters.yml` plus configured checkpoint files, or network access for model download behavior.
- Protein/ligand inputs for inference.
- Processed benchmark/training datasets and split files for training/evaluation.
- ESM embedding files when workflows require cached receptor language-model features.
- GNINA executable when GNINA flags are enabled.
