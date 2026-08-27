# Installation

CausalNex supports Python 3.8, 3.9, and 3.10. The package exposes the public `causalnex` import and expects a working PyTorch installation for the NOTEARS-based structure-learning path.

## Base install

```bash
pip install causalnex
```

## Optional discretizer extra

The repo ships an optional MDLP-based discretizer path. Install it when you need `MDLPSupervisedDiscretiserMethod`:

```bash
pip install "causalnex[all]"
pip install mdlp-discretization~=0.3.3
```

## Backend notes

- The package is CPU-first and runs without a GPU.
- `use_gpu=True` only matters for the PyTorch NOTEARS path when your torch build sees CUDA.
- If you only need CPU verification, keep `use_gpu=False` in smoke checks and custom examples.

## After install

Run the bundled check script to confirm the major import surfaces:

```bash
python scripts/check_install.py
```

If that script fails on `causalnex.network` or `causalnex.inference`, read the troubleshooting notes about `pkg_resources` and `setuptools`.
