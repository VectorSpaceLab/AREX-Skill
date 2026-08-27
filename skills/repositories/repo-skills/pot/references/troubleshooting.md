# POT cross-cutting troubleshooting

Use this reference for install/import, optional dependency, compiled extension, and package-wide validation issues before entering a workflow-specific sub-skill.

## Import and package-name confusion

Symptoms:

- `ModuleNotFoundError: No module named 'pot'`.
- `pip install pot` succeeds but code imports the wrong name.

Fix:

```python
import ot
print(ot.__version__)
```

The distribution is named `POT`, but the Python import package is `ot`.

## Base installation fails from source

Symptoms:

- Compiler errors while building `ot.lp.emd_wrap`, `ot.partial.partial_cython`, or `ot.bsp.bsp_wrap`.
- Missing `Eigen/Dense` during BSP-OT compilation.
- Cython or NumPy header errors.

Likely causes and fixes:

1. Prefer a released wheel or conda-forge package when possible: `pip install POT` or `conda install -c conda-forge pot`.
2. For source builds, install build tools, Cython, and NumPy headers before building.
3. BSP-OT uses Eigen headers. If building an editable checkout, ensure Eigen headers are present through the repository's documented submodule or a system/conda package.
4. Run the root helper after installation:

```bash
python scripts/check_pot_install.py --json
```

If compiled extension imports fail, do not trust exact EMD, partial, or BSP routes until the base install is repaired.

## Optional dependency missing

Symptoms:

- `import ot.dr` raises an error mentioning `autograd`, `pymanopt`, and `scikit-learn`.
- `import ot.plot` fails with missing `matplotlib`.
- `import ot.gnn` fails with missing `torch` or `torch_geometric`.
- GeomLoss lazy methods fail with missing `geomloss` or `pykeops`.

Fixes:

- Install only the optional surface the task needs: `POT[dr]`, `POT[plot]`, `POT[backend-torch]`, `POT[backend-jax]`, `POT[backend-tf]`, `POT[gnn]`, or `POT[geomloss]`.
- Avoid `POT[all]` unless the user wants every optional surface; it can install GPL-sensitive `cvxopt` and large ML frameworks.
- Verify optional imports explicitly:

```bash
python scripts/check_pot_install.py --include-optional --json
```

## Mixed backend arrays

Symptoms:

- `ValueError` says all arrays should come from the same type/backend.
- A NumPy cost matrix is passed with Torch/JAX/TF/CuPy weights.
- Gradients are missing after converting with `to_numpy`.

Fix:

- Convert all arrays in one POT call to the same backend before calling the solver.
- Use `ot.backend.get_backend(*arrays)` to confirm the inferred backend.
- Use `ot.backend.to_numpy` only when leaving differentiable computation.
- For backend-specific troubleshooting, read `sub-skills/backend-and-batch/references/troubleshooting.md`.

## Numerical scale and convergence

Symptoms:

- Sinkhorn warnings, NaNs/Infs, or very slow convergence.
- Results change dramatically when `reg`, `reg_m`, or `alpha` changes.

Fixes:

1. Check input arrays are finite, nonnegative where required, and correctly shaped.
2. Normalize cost matrices or feature scales before choosing regularization.
3. Use log-domain variants such as `method="sinkhorn_log"` when underflow is likely.
4. Increase `reg` for smoother/stabler plans; reduce only after a tiny fixture passes.
5. Compare against a tiny exact EMD or dense baseline when feasible.

## Dense memory blowups

Symptoms:

- Memory errors when building `M = ot.dist(Xs, Xt)` or a dense plan.
- Large graph/GW or all-pixel image workflows run out of memory.

Fixes:

- Estimate matrix size before solving: dense cost/plan memory is roughly `n_source * n_target * dtype_size`.
- For many small problems, use `backend-and-batch` batch solvers.
- For high-dimensional samples, consider sliced, low-rank, Nystroem, GeomLoss/lazy, semidiscrete, stochastic, or Gaussian/GMM routes under `sliced-gaussian-large-scale`.
- For image/color tasks, subsample or cluster pixels before fitting dense couplings.

## Backend/GPU expectations

A visible GPU does not mean POT's optional backend path is installed or verified. Base POT numerical checks can pass with only NumPy. If the task requires CUDA/CuPy/PyTorch/JAX/TensorFlow, verify the framework import and a tiny device operation in that environment before claiming GPU support.

## Quick triage command

```bash
python scripts/check_pot_install.py --include-optional --json
```

Use failures from this command to route:

- Base import or compiled extension failure: fix install first.
- Optional dependency missing: install only the requested optional extra or choose a CPU/NumPy route.
- Tiny solve failure: inspect NumPy/SciPy/POT version compatibility before running workflow scripts.
