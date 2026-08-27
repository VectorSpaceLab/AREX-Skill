# Training workflow troubleshooting

Start with the smallest reproducer: set the intended backend before import, build the same `data` and `net`, call `compile`, run 1-3 iterations with `display_every=1`, and verify that `model.predict` returns finite arrays. The bundled smoke script provides such a baseline for PyTorch CPU function approximation.

## Quick triage table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ValueError: No learning rate for adam/sgd/...` | Standard optimizers require `lr`. | Call `model.compile("adam", lr=1e-3)` or choose an external optimizer such as `"L-BFGS"` configured separately. |
| Warning that learning rate is ignored for `L-BFGS` or `NNCG` | PyTorch external optimizers ignore `lr` and `decay`. | Configure with `dde.optimizers.set_LBFGS_options(...)` or `dde.optimizers.set_NNCG_options(...)` before `compile`. |
| L-BFGS stops early, converges poorly, or behaves differently from Adam | External optimizer tolerance/history/float precision issue. | Try Adam warm-up first, tune `set_LBFGS_options(maxiter, ftol, gtol, maxcor, maxls)`, and consider `dde.config.set_default_float("float64")` before constructing objects. |
| `NNCG` is unavailable or very slow | NNCG is PyTorch-only and beta; Hessian-vector products are expensive. | Use Adam or L-BFGS first. If using NNCG, tune rank, damping `mu`, `cgmaxiter`, `cgtol`, and update frequency. |
| `NotImplementedError` mentioning an optimizer | Optimizer string is not implemented for the active backend. | Check the backend-specific optimizer set; for PyTorch use lower-case `"adam"`, `"adamw"`, `"sgd"`, `"rmsprop"`, or external `"L-BFGS"`/`"NNCG"`. |
| Training stops immediately after NaN appears | DeepXDE sets `stop_training=True` when train or test loss contains NaN. | Reduce learning rate, check target scaling, inspect PDE residuals/BCs, switch to float64 when appropriate, and run a tiny smoke case. |
| `PDEPointResampler` raises that `num_bcs` changed | Resampled BC points changed the number/order of BC losses. | Recompile after changing BC sampling structure; keep boundary sample counts stable when using loss weights. |
| `Model.predict(..., operator=...)` fails for auxiliary variables on PyTorch/JAX/Paddle | Three-argument auxiliary-variable operator prediction is not implemented for those backends in this version. | Use a two-argument operator, evaluate auxiliary logic outside `predict`, or verify a backend that supports the required path. |
| `torch.load` / checkpoint restore fails on CPU after GPU training | PyTorch checkpoint needs device remapping. | Compile an identical model, then call `model.restore(path, device="cpu")`. Device remapping is only supported by PyTorch. |
| Restore fails with missing/unexpected keys or optimizer state mismatch | Data/net architecture or optimizer differs from the saved model. | Recreate the same network architecture and compile with the same optimizer family before `restore`. |
| `dde.saveplot(..., isplot=True)` hangs or errors in CI/headless runs | Matplotlib display is unavailable. | Use `isplot=False`, set a noninteractive Matplotlib backend before importing pyplot, or save arrays and plot later. |
| `np.loadtxt` file data loads but target shape is wrong | `col_x`/`col_y` slices are wrong or scalar arrays were not kept 2-D. | Use list/tuple column indices such as `(0,)`, inspect loaded array shapes, and ensure target arrays are `(N, output_dim)`. |
| Standardized `DataSet` predictions look shifted | New inputs were not transformed with `data.transform_inputs`. | When `standardize=True`, call `model.predict(data.transform_inputs(x_new))`. |
| Multifidelity stacking fails | Low/high inputs or outputs have incompatible dimensions. | Check `X_lo_train`, `X_hi_train`, `y_lo_train`, `y_hi_train`, `X_hi_test`, and `y_hi_test` are all 2-D and compatible. |

## Optimizer decision path

1. Use `"adam"` with a conservative learning rate for most first runs.
2. If the loss is finite but plateaus, optionally warm-start L-BFGS:
   ```python
   dde.optimizers.set_LBFGS_options(maxiter=500, ftol=1e-12, gtol=1e-12)
   model.compile("L-BFGS")
   model.train(display_every=50)
   ```
3. Use `"NNCG"` only when the active backend is PyTorch and the problem justifies a beta second-order method:
   ```python
   dde.optimizers.set_NNCG_options(rank=20, mu=1e-2, cgmaxiter=100, verbose=False)
   model.compile("NNCG")
   model.train(iterations=50, display_every=10)
   ```
4. If using inverse variables, verify external variable handling under the backend. For PyTorch with L-BFGS and L2 regularization, DeepXDE warns that L2 also applies to external variables.

## Checkpoint protocol checklist

- Create checkpoint directories before training when using nested paths.
- Record the concrete path returned by `model.save(...)`; do not guess the suffix.
- With default `use_iteration_suffix=True`, pass the returned path to `restore`, not just the prefix.
- Rebuild `data`, `net`, and `model` with the same architecture; call `compile` before `restore` so optimizer state exists.
- Use `device="cpu"` only with PyTorch if moving a checkpoint to CPU.
- Use `protocol="backend"` for files you plan to restore through `Model.restore`.

## Convergence and accuracy triage

When losses are finite but accuracy is poor:

1. Confirm data shapes and target scale with a tiny subset.
2. Increase `display_every` frequency temporarily to see whether train and test losses diverge.
3. Check whether `loss_weights` are hiding a large component; print per-component losses from `losshistory.loss_train`.
4. For PDE workflows, route residual/BC ordering and sampling questions to the PINN sub-skill.
5. For function or tabular regression, try standardizing inputs, increasing network width/depth, changing activation, or increasing `num_train`.
6. Warm-start L-BFGS only after Adam produces finite losses.
7. For reproducibility debugging, set backend, random seed, and float precision before constructing data/net/model.

## Plotting safely in noninteractive environments

Preferred agent-safe pattern:

```python
losshistory, train_state = model.train(iterations=100, display_every=10)
dde.saveplot(
    losshistory,
    train_state,
    issave=True,
    isplot=False,
    output_dir="outputs",
)
```

If a user explicitly needs image files, configure Matplotlib's noninteractive backend before any pyplot import in the process, then save figures rather than calling an interactive display. The smoke script avoids plotting entirely to keep verification deterministic.
