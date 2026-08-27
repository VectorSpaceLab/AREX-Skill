# POT domain-adaptation troubleshooting

Use this reference when a domain-adaptation estimator fails to fit, produces an unexpected coupling/map, or needs an optional dependency. For low-level solver numerical issues, also read the core solver and unbalanced/partial troubleshooting references.

## `fit()` receives missing or misnamed data

Symptoms:

- `Xs` or `Xt` is `None`.
- A method accepts the call but fitted attributes are missing or empty.
- Positional arguments seem to be interpreted incorrectly.

Likely causes and fixes:

1. Prefer keyword arguments: `fit(Xs=X_source, ys=y_source, Xt=X_target, yt=y_target)`.
2. Ensure source and target have the same feature dimension for ordinary vector-space OTDA.
3. For `JCPOTTransport`, pass `Xs` as a list of source arrays and `ys` as a list of source-label arrays.
4. Keep `ys` and `yt` one-dimensional label vectors; do not pass one-hot matrices unless a specific workflow transforms them first.

## Shape or feature-scale errors

Symptoms:

- `ot.dist` or a transport fit raises dimension errors.
- Coupling has the expected shape, but transformed samples are nonsensical.
- One feature dominates the transport map.

Fixes:

- Check `Xs.shape == (n_source, n_features)` and `Xt.shape == (n_target, n_features)`.
- Standardize or normalize features before fitting when units differ.
- Try a transport with `norm="median"` or `norm="max"` if the estimator exposes `norm`.
- Inspect `est.cost_` after fitting; it should be finite and have shape `(n_source, n_target)`.

## Label and semi-supervised failures

Symptoms:

- Semi-supervised transport sends mass across known incompatible classes.
- A target label marked as unknown is treated as an actual class.
- `SinkhornLpl1Transport`, `SinkhornL1l2Transport`, or JCPOT raises label-length errors.

Fixes:

- Use `-1` only for unknown target labels. Remap real class `-1` to another integer before calling POT.
- Ensure `len(ys) == len(Xs)` and, when provided, `len(yt) == len(Xt)`.
- For class-regularized transports, pass `ys`; these estimators need source labels.
- For JCPOT, every source domain needs labels and compatible class names/ids.

## Unexpected `out_of_sample_map` behavior

Symptoms:

- `transform(Xs=new_points)` differs from the fitted-point barycentric mapping.
- New samples fail because an out-of-sample strategy is unsupported.

Fixes:

- Understand the distinction: fitted source points can use the barycentric mapping induced by `coupling_`; new source points require an out-of-sample rule or a learned mapping.
- For EMD-style transports, review `out_of_sample_map="ferradans"` vs continuous variants.
- For true learned maps, use `MappingTransport`, `LinearTransport`, `LinearGWTransport`, or `ot.mapping` functions.
- Validate on a tiny held-out source point before applying to a large dataset.

## Convergence stalls or couplings contain bad values

Symptoms:

- Warnings about non-convergence.
- `coupling_` contains NaNs/Infs.
- Results are highly sensitive to `reg_e`, `reg_cl`, or cost scaling.

Fixes:

1. Confirm all inputs and costs are finite.
2. Normalize features or the cost matrix.
3. Increase `reg_e` for Sinkhorn-style transports to avoid near-zero kernels.
4. Increase `max_iter` or relax `tol` after the tiny fixture works.
5. Use `method="sinkhorn_log"` for Sinkhorn transports when underflow is suspected.
6. Compare against `EMDTransport` on a tiny subset to separate modeling issues from entropic numerical issues.

## Missing optional dependencies

Symptoms:

- Importing `ot.dr` raises an error about `autograd`, `pymanopt`, and `scikit-learn`.
- Nearest Brenier potential fails when it reaches a convex optimization call.
- GNN layers fail with missing `torch` or `torch_geometric`.

Fixes:

- For WDA/EWCA and other `ot.dr` workflows, install `POT[dr]` or the equivalent `autograd`, `pymanopt`, and `scikit-learn` packages.
- For nearest Brenier potential workflows, verify `cvxpy` before fitting; also choose a compatible CVXPY solver for the user's platform.
- For GNN layers, route to the `gromov` and `backend-and-batch` sub-skills; PyTorch Geometric is optional and not part of the minimum NumPy environment.
- Run `python scripts/domain_adaptation_smoke.py --case dependencies --json` to get a structured optional-dependency status.

## JCPOT source-list errors

Symptoms:

- JCPOT errors about list lengths or dimensions.
- `proportions_` is missing, non-finite, or not interpretable.

Fixes:

- Pass `Xs=[Xs1, Xs2, ...]` and `ys=[ys1, ys2, ...]` with the same list length.
- Each source array can have a different number of rows, but feature dimension should match the target.
- Keep source class labels compatible across domains.
- Start with `reg_e` large enough to stabilize tiny target-shift estimates.
- Validate each `coupling_[k].shape == (len(Xs[k]), len(Xt))`.

## Image/color transfer data issues

Symptoms:

- Memory explosion on image transfer.
- Mapped colors are outside expected range.
- Input arrays have unexpected channel order.

Fixes:

- Convert image arrays to `(n_pixels, channels)` samples and scale consistently, for example `float / 255.0`.
- Do not fit dense couplings on very large pixel counts. Subsample pixels, cluster colors, or learn a mapping from representative colors.
- Clip transformed colors before converting back to integer image dtype.
- Verify whether user data is RGB, BGR, grayscale, or has an alpha channel; POT only sees numeric feature vectors.

## Smoke helper failures

Run:

```bash
python scripts/domain_adaptation_smoke.py --case all --json
```

If `emd` or `sinkhorn` fails, the base POT install or NumPy/SciPy stack is not healthy for OTDA. If only `mapping` or `jcpot` fails, inspect the structured error and reduce the user's requested workflow to baseline EMD/Sinkhorn before escalating. Missing optional dependencies in the `dependencies` case are informational unless the user's task explicitly needs those optional routes.
