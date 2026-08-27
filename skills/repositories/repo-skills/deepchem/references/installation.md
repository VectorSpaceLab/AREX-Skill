# DeepChem Installation and Backend Notes

## Minimal Install

DeepChem's package metadata declares the base runtime dependencies as:

- `joblib`
- `numpy<2`
- `pandas`
- `scikit-learn`
- `sympy`
- `scipy>=1.10.1`
- `rdkit`

Typical public installs are:

```bash
pip install deepchem
conda install -c conda-forge deepchem
```

For source checkouts, use an isolated environment and install the local package in editable mode only when the user is working on DeepChem itself:

```bash
python -m pip install -e .
```

## Optional Extras

DeepChem exposes optional backend groups in package metadata:

```bash
pip install 'deepchem[torch]'
pip install 'deepchem[tensorflow]'
pip install 'deepchem[jax]'
pip install 'deepchem[dqc]'
```

Use optional extras only when the selected workflow requires them. Do not install all extras just to load CSV files, compute RDKit descriptors, train a scikit-learn baseline, or inspect MoleculeNet loader parameters.

## Backend Selection

- Use base dependencies for CSV/SDF loading, RDKit featurizers, splitters, transformers, metrics, and `SklearnModel` workflows.
- Use `deepchem[torch]` for PyTorch model families, DGL/DGLLife-dependent graph models, and some DFT/advanced examples.
- Use `deepchem[tensorflow]` for TensorFlow/Keras model families.
- Use `deepchem[jax]` for JAX model families.
- Use `deepchem[dqc]` for differentiable quantum chemistry surfaces that require DQC, xitorch, torch, and related compiled packages.

GPU support is controlled by the selected backend package, driver, CUDA runtime, and hardware. A machine can have GPUs while a base DeepChem install remains CPU-only.

## Colab and Setup Scripts

The original project contains Colab and conda setup helpers, but those scripts mutate environments and may perform network installs. This skill distills their intent instead of bundling them as executable defaults. Prefer explicit environment commands above, and only run notebook/Colab bootstrap logic in a disposable notebook runtime.

## Verification Snippets

Minimal import check:

```bash
python - <<'PY'
import deepchem as dc
print(dc.__version__)
print(dc.feat.CircularFingerprint(size=16).featurize(['CCO'])[0].shape)
PY
```

Base training smoke:

```bash
python sub-skills/model-training/scripts/train_tiny_sklearn_model.py
```

Optional structure dependency report:

```bash
python sub-skills/docking-and-structure/scripts/check_structure_dependencies.py
```
