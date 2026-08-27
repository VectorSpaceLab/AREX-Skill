# Troubleshooting supervised UMAP, densMAP, and downstream interpretation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Length of x = ..., length of y = ..., while it must be equal` | Labels no longer align with feature rows. | Rebuild `y` from the same mask/split as `X`; check `len(y) == X.shape[0]`. |
| Labels seem ignored | `y` was omitted, `target_weight` is too low, or the target metric does not match the label type. | Confirm `fit(X, y)` or `fit_transform(X, y)` is used; set `target_metric="categorical"` for class labels; tune `target_weight`. |
| Classes are separated too aggressively | Labels dominate the embedding or noisy labels are over-weighted. | Lower `target_weight`, compare an unsupervised baseline, and validate against held-out labels or domain checks. |
| Partial labels behave oddly | `-1` was used with a non-categorical target metric, or label dtype/encoding is inconsistent. | Use `-1` only for unlabeled categorical targets; keep one dtype and one unknown-label convention. |
| `target_n_neighbors must be greater than 1` | `target_n_neighbors` is `0` or `1`. | Use `-1` to reuse `n_neighbors`, or choose a value `>= 2`. |
| Continuous targets form strange groups | Categorical metric was used for numeric/regression targets. | Try a numeric target metric such as `l1` or `l2`, and scale the target if needed. |
| `dens_lambda cannot be negative` | Invalid density regularization weight. | Use `dens_lambda >= 0`; `0` behaves like ordinary UMAP for the density term. |
| `dens_frac must be between 0.0 and 1.0` | Invalid density objective epoch fraction. | Choose a fraction in `[0.0, 1.0]`; defaults are a safer starting point. |
| `dens_var_shift cannot be negative` | Invalid density stabilizer. | Use a non-negative value; keep the default unless you have evidence to tune it. |
| densMAP is much slower | Density regularization adds work. | Prototype on a sample, reduce epochs during exploration, and only scale when density preservation is necessary. |
| `Transforming data into an existing embedding not supported for densMAP` | densMAP does not implement this transform path. | Use standard UMAP for metric-learning transform workflows, or refit densMAP with all rows included. |
| `Inverse transform not available for densMAP` | densMAP does not support inverse transform. | Use standard UMAP if inverse reconstruction is required. |
| `Updating supervised models is not currently supported` | `update` was called after fitting with `y`. | Refit on the combined data, or use an unsupervised model if incremental updates are required. |
| `output_dens=True` returns a tuple | Expected density-output behavior. | Unpack `embedding, rad_orig, rad_emb`; pass only `embedding` to clustering or plotting. |
| `rad_orig_` or `rad_emb_` is missing | The model was not fit with `output_dens=True`. | Refit with `output_dens=True` and then inspect the attributes or tuple outputs. |
| HDBSCAN import fails in clustering workflow | HDBSCAN is optional and not part of the required umap-learn dependency set. | Install `hdbscan` only if you need it, or use KMeans/sklearn methods for tiny smoke checks. |
| Clusters look convincing but scores are weak | UMAP can alter density and introduce false visual gaps. | Validate with ARI/AMI when labels exist, stability over seeds, original-space metrics, or domain review. |
| Outliers change across UMAP settings | Outlier detection on an embedding is sensitive to neighborhood graph choices. | Compare seeds, `n_neighbors`, `set_op_mix_ratio`, and original-space nearest neighbors before acting. |
| Large examples are too slow or try to download data | Some published examples use external datasets, image files, plotting, or optional packages. | Reproduce the pattern on the bundled tiny smoke workflow first; get explicit approval before downloads or long runs. |

## Recovery checklist

1. Fit an unsupervised UMAP baseline on the same `X`.
2. Verify label length, row order, dtype, class balance, and unknown-label
   encoding.
3. Sweep `target_weight` on a small sample before scaling.
4. Decide whether you need `transform` or `inverse_transform`; if yes, avoid
   densMAP.
5. If using `output_dens`, unpack the tuple and keep radii as diagnostics.
6. Validate clustering or outlier conclusions outside the 2D embedding plot.
