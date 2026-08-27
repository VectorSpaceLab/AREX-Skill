# scvi-tools Troubleshooting

Use this reference for cross-cutting failures before drilling into a workflow-specific sub-skill.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: scvi` | Package is not installed in the active Python environment | Install `scvi-tools` in the environment that runs the code; verify with `python -c "import scvi; print(scvi.__version__)"`. |
| `Requires-Python` or wheel errors | Python version is outside the supported range | Use Python 3.12+ for this repository snapshot, then reinstall. |
| Import succeeds in one shell but not another | Notebook/kernel/terminal use different Python environments | Print `sys.executable` in both contexts and reinstall or switch kernels. |
| `pip check` reports conflicts | Optional extras or backend wheels pulled incompatible dependency versions | Prefer a fresh environment and install only the extras required for the workflow. |

## PyTorch and Accelerator Issues

- GPU is optional for many APIs, but training performance depends on PyTorch backend support.
- If `torch.cuda.is_available()` is `False`, use `accelerator="cpu", devices=1` for portable examples or install a CUDA-compatible PyTorch wheel for the host driver.
- Do not install `cuda`, `rapids`, `tpu`, or `metal` extras unless the hardware/backend is explicitly needed.
- For multi-GPU training, route to `sub-skills/training-and-inference/` and verify Lightning strategy, devices, and batch sizes.

## Optional Extras

| Workflow | Typical extra or dependency family | Notes |
| --- | --- | --- |
| Hyperparameter tuning | `scvi-tools[autotune]` | Pulls Ray/HyperOpt-style dependencies; usually heavier than base install. |
| Hub workflows | `scvi-tools[hub]` | May require network, credentials, and storage metadata setup. |
| Custom dataloaders | `scvi-tools[dataloaders]` | LaminDB, CELLxGENE Census, TileDB-SOMA, AnnBatch, torchdata may be needed only for those routes. |
| DNA sequence / scBasset-style workflows | `scvi-tools[regseq]` or related packages | May download genomes or require sequence files. |
| MLflow logging | `scvi-tools[mlflow]` | Requires MLflow service or local tracking configuration. |

## Data Downloads and Network

Built-in dataset helpers can download data. For reproducible agent work, prefer user-provided local `AnnData`/`MuData` paths or create tiny synthetic fixtures with `sub-skills/data-setup/scripts/create_tiny_anndata.py`. If a helper needs network access, record the URL/source and provide a local fallback when possible.

## Version and Registry Mismatch

Saved models store registry and setup metadata. If loading fails after upgrading `scvi-tools`, check:

- The saved model version and current `scvi.__version__`.
- Whether the saved directory includes the expected model files and registry metadata.
- Whether the supplied `adata` has matching `var_names`, layers, `.obs` categories, and modality fields.

Use `sub-skills/model-io-and-hub/scripts/check_saved_model.py --help` for structural checks and read `sub-skills/model-io-and-hub/references/troubleshooting.md` for recovery patterns.

## Safe Debugging Order

1. Run `python scripts/check_scvi_environment.py --json` from the root skill directory.
2. Confirm the `AnnData`/`MuData` fields with the `data-setup` troubleshooting reference.
3. Confirm the selected model class and `setup_anndata` signature with the relevant model sub-skill.
4. Reduce training to a CPU-safe tiny run before debugging GPU, callbacks, or dataloaders.
5. Only then add optional extras, external services, or hardware-specific backends.
