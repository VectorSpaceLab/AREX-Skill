# Three-D Graph Troubleshooting

## Dataset Layout and Downloads

- `QM93D` and `MD17` download archives the first time they are instantiated.
- `ECdataset` and `FOLDdataset` require a specific local directory structure and hdf5 files; if the expected split files or protein files are missing, the dataset will fail before any model code runs.

## PySCF Property Evaluation

- `dig.ggraph3D.evaluation.PropOptEvaluator` uses PySCF DFT and can be slow even for small molecules.
- Use it only after confirming the geometry pipeline works and after the user accepts the runtime.

## GPU-Optional Configs

- `G_SphereNet` respects `use_gpu` in its config dictionary.
- If `use_gpu` is false, the model should stay on CPU for smoke checks, but full generation throughput is still much faster on GPU.

## Geometry and Validity Issues

- If `xyz2mol` or bond reconstruction fails, inspect atom counts, atomic numbers, and coordinate ordering.
- For generation workflows, ensure the collate function is used exactly as documented; a plain PyTorch collate function will not preserve the required keys.
