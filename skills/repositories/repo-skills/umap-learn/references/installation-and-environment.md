# Installation and Environment Reference

Use this before setting up `umap-learn` or diagnosing optional extra imports.
This reference is public and intentionally omits private build or inspection
environment paths.

## Base Install

```bash
pip install umap-learn
```

Conda users can install from conda-forge:

```bash
conda install -c conda-forge umap-learn
```

The package metadata for this skill snapshot reports:

- Distribution: `umap-learn`.
- Version: `0.5.12`.
- Python: `>=3.10`.
- Import: `import umap`.
- Base dependencies: `numpy>=1.23`, `scipy>=1.3.1`, `scikit-learn>=1.6`,
  `numba>=0.51.2`, `pynndescent>=0.5`, and `tqdm`.
- Console entry points: none.

## Optional Extras

| Extra | Install command | Use |
| --- | --- | --- |
| `plot` | `pip install "umap-learn[plot]"` | Enables `umap.plot` static, datashaded, connectivity, diagnostic, and interactive plotting helpers. |
| `parametric_umap` | `pip install "umap-learn[parametric_umap]"` | Enables TensorFlow/Keras `ParametricUMAP` neural workflows. |
| `tbb` | `pip install "umap-learn[tbb]"` | Optional CPU optimization on compatible systems. |
| `test` | `pip install "umap-learn[test]"` | Installs pytest for package tests. Usually not needed for ordinary use. |

The plotting stack includes pandas, matplotlib, datashader, bokeh, holoviews,
colorcet, seaborn, scikit-image, and dask. ParametricUMAP imports TensorFlow
and Keras; ONNX-related paths also check torch/torchvision.

## Environment Check

Run the bundled checker from the generated skill root:

```bash
python scripts/check_umap_environment.py --json
python scripts/check_umap_environment.py --check-plot --check-parametric --json
```

For workflow-specific checks, use the sub-skill scripts:

```bash
python sub-skills/core-embedding/scripts/umap_core_smoke.py --transform --json
python sub-skills/plotting-diagnostics/scripts/check_plotting_stack.py --json
python sub-skills/parametric-umap/scripts/check_parametric_stack.py --json
```

## CPU/GPU Expectations

Base `umap-learn` is CPU-oriented and does not expose a package CUDA workflow.
Do not treat a visible GPU as proof that UMAP will use it. ParametricUMAP uses
TensorFlow/Keras; GPU use there depends on the TensorFlow installation and must
be verified separately in the target environment.

## Development or Editable Installs

For repository development, an editable install can be useful:

```bash
python -m pip install -e ".[test]"
```

For ordinary Researcher use, prefer the released package install unless the task
explicitly involves a local checkout.
