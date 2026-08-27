# POT package overview

POT (Python Optimal Transport) is a scientific Python library for optimal transport (OT) and machine-learning workflows. It installs from the distribution `POT` and imports as `ot`.

## Core concepts

- **Discrete OT / Wasserstein distance** compares histograms or empirical distributions with a ground-cost matrix.
- **Transport plan** is a nonnegative matrix whose entries describe moved mass between source and target supports.
- **Exact OT** uses network-simplex/LP-style solvers and is accurate for small to medium dense problems.
- **Regularized OT** adds entropy, KL, L2, or custom regularization; Sinkhorn-style methods are often smoother and faster but depend on `reg` scale.
- **Unbalanced and partial OT** relax mass conservation or transport a fixed amount of mass.
- **Gromov-Wasserstein** aligns relational structures when samples do not live in the same feature space.
- **Barycenters** summarize multiple distributions on fixed supports, learned/free supports, sample clouds, GW/FGW structures, or Gaussian/GMM families.
- **Backends** let many POT APIs operate on NumPy, PyTorch, JAX, TensorFlow, or CuPy arrays when those optional libraries are installed.

## Public install routes

```bash
pip install POT
python - <<'PY'
import ot
print(ot.__version__)
PY
```

Conda users can install from conda-forge:

```bash
conda install -c conda-forge pot
```

For a local editable checkout, POT builds compiled extensions for exact EMD, partial OT, and BSP-OT. Ensure a working C/C++ compiler, Cython, NumPy headers, and the Eigen submodule or equivalent Eigen headers are available before building from source.

## Optional extras and dependency surfaces

POT's base install requires NumPy and SciPy. Optional extras are workflow-specific:

| Extra/surface | Purpose | Notes |
| --- | --- | --- |
| `backend-torch` | PyTorch arrays, gradients, differentiable OT examples | CPU or CUDA wheel choice is external to POT. |
| `backend-jax` | JAX arrays and autodiff | Enable/verify 64-bit behavior when tests or numerical comparisons need it. |
| `backend-tf` | TensorFlow tensors | TensorFlow NumPy behavior may need `np_config.enable_numpy_behavior()`. |
| `backend-cupy` | CuPy arrays on CUDA | CuPy package must match the user's CUDA runtime. |
| `cvxopt` | Some LP/barycenter paths | CVXOPT is GPL-licensed; do not install implicitly when licensing matters. |
| `dr` | `ot.dr` WDA/EWCA dimensionality-reduction workflows | Installs `scikit-learn`, `pymanopt`, and `autograd`. |
| `gnn` | OT graph neural-network layers | Requires PyTorch and PyTorch Geometric. |
| `plot` | Plotting helpers and example visualization | Needed for `ot.plot`, not for numerical solvers. |
| `geomloss` | Lazy large-sample empirical Sinkhorn via GeomLoss/PyKeOps | Useful for large empirical OT with PyTorch. |

Do not install `POT[all]` unless the user explicitly wants every optional surface and accepts licensing/runtime implications.

## Root checks

Use the bundled root helper after installing POT:

```bash
python scripts/check_pot_install.py --json
python scripts/check_pot_install.py --include-optional --json
```

The first command requires only the base package and verifies import, compiled solver extensions, and a tiny NumPy solve. The second reports optional dependency availability without requiring optional packages.

## Sub-skill route map

- `core-solvers`: exact OT, `ot.solve`, `ot.solve_sample`, EMD/EMD2, Sinkhorn, 1D/circle/sparse/lazy helpers, result objects.
- `barycenters`: fixed-support, free-support, sample-cloud, entropic/debiased/convolutional barycenters.
- `gromov`: GW/FGW, semirelaxed/partial/unbalanced/quantized GW, graph-structured alignment, GW barycenters and dictionary learning.
- `unbalanced-partial`: relaxed-marginal UOT, fixed transported-mass partial OT, UOT barycenters, regularization paths.
- `sliced-gaussian-large-scale`: sliced/spherical sliced OT, Gaussian/Bures/GMM OT, low-rank/factored/Nystroem/BSP/semidiscrete/SGOT/COOT/stochastic alternatives.
- `domain-adaptation`: OT domain adaptation estimators, mapping transport, JCPOT, optional WDA/EWCA and nearest Brenier potential routes.
- `backend-and-batch`: optional backends, mixed-array diagnostics, backend disable variables, and batch solvers.

## Choosing a solver family quickly

| User intent | Start here |
| --- | --- |
| "Compute Wasserstein distance / transport plan" | `core-solvers` |
| "Use samples directly, not a cost matrix" | `core-solvers` (`ot.solve_sample`) |
| "Average several distributions" | `barycenters` |
| "Align graphs or distance matrices" | `gromov` |
| "Mass differs or outliers should be ignored" | `unbalanced-partial` |
| "Need a faster approximation for many/high-dimensional samples" | `sliced-gaussian-large-scale` |
| "Adapt source data to a target domain" | `domain-adaptation` |
| "Use torch/JAX/TF/CuPy or solve a batch of OT problems" | `backend-and-batch` |

## Validation principles

Always validate more than just "no exception":

- Plan shape matches `(len(source), len(target))` or the documented batch shape.
- Entries are finite and nonnegative within tolerance.
- Marginal sums or transported mass match the selected balanced/unbalanced/partial semantics.
- Result objects expose the values the downstream task needs (`value`, `value_linear`, `value_quad`, `plan`, `potentials`, `X`, `b`, or `log`).
- Optional backend claims are verified in the actual active environment.
