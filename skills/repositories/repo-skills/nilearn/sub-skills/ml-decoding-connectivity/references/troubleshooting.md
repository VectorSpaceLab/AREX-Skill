# Troubleshooting

## Common Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Found input variables with inconsistent numbers of samples` | `y`, `groups`, confounds, or image samples do not have the same first dimension. | Count samples before fitting: number of 3D images or subject time-series arrays must equal target length; one confound row per sample/subject. |
| High CV score disappears on a clean split | Leakage from mask/feature/connectome fitting on all data before CV. | Put mask learning, decomposition, tangent `ConnectivityMeasure.fit`, feature scaling, and model fitting inside each training split or a scikit-learn pipeline. |
| `ConnectivityMeasure` rejects input dimensions | Subject signals are not a list/iterable of 2D arrays, or region counts differ. | Ensure each array is `(n_timepoints, n_regions)` and all arrays share `n_regions`; route extraction issues to `maskers-regions`. |
| `confounds` with connectomes raises an error | Confounds are only cleaned on vectorized matrices. | Set `vectorize=True`, align confound rows to subjects, or regress confounds outside Nilearn. |
| Tangent connectivity fails or gives suspicious features | Tangent space needs a group reference and is sensitive to fitting on all subjects. | Fit on training subjects, transform held-out subjects, and keep at least a meaningful group in `transform`; avoid one-subject tangent evaluations. |
| Searchlight or SpaceNet runs for too long | Large mask, many CV folds, large radius, high `n_jobs`, or structured optimization defaults. | Prototype with smaller `process_mask_img`, fewer folds, `n_jobs=1`, lower `max_iter`, and explicit runtime logging before scaling. |
| Labels/runs mismatch in searchlight or decoder | Labels are per event/run but images are per volume or vice versa. | Build a sample table first; each row should map image index, label, run/group, and confounds. |
| Empty or incompatible mask | Mask affine/shape does not match images, or mask has no selected voxels. | Route image resampling/mask creation to `data-io-signal` and `maskers-regions`; inspect mask voxel count before ML. |
| NaNs or infinities in connectome/decoder features | Constant signals, aggressive confound regression, zero-variance regions, or invalid standardization. | Drop/merge bad regions, verify masker output, use finite checks, and choose a `standardize` setting deliberately. |
| Correlation, partial correlation, and precision are confused | Different `kind` values answer different questions. | Use `correlation` for normalized pairwise association, `partial correlation` for conditional association, `precision` for inverse covariance, `tangent` for group features. |
| `permuted_ols` is slow or memory-heavy | Large target matrix, high `n_perm`, TFCE/cluster inference, or parallel chunks. | Smoke-test with low `n_perm`, then increase deliberately; use `n_jobs=1` first and only enable TFCE/threshold with a valid masker. |
| `n_jobs=0` or oversubscription errors | Invalid job count or nested parallelism with BLAS/sklearn. | Use `n_jobs=1` for debugging; use `-1` only when the machine and nested libraries are controlled. |

## CV and Leakage Checklist

- Are labels, groups, confounds, and sample images/time series aligned by the
  same sample table?
- Is every learned transformation fit only on training data: mask learning,
  decomposition/parcellation, tangent mean, scaling, feature selection, and
  classifier/regressor?
- Does the CV split respect subject/run/session boundaries when samples are
  temporally or hierarchically dependent?
- Are class imbalance and scoring compatible, for example `balanced_accuracy`
  rather than plain accuracy for imbalanced labels?
- Are final maps interpreted only after validating predictive performance on
  held-out data?

## Performance Triage

1. Replace full masks with a tiny process mask or a few regions.
2. Replace `cv=10` or `cv=30` defaults with a small explicit splitter during
   debugging.
3. Set `n_jobs=1` until correctness is established; parallel logs can obscure
   the first real error.
4. Disable expensive extras (`tfce`, cluster inference, high `n_perm`, high
   `max_iter`, large `radius`) until shape contracts pass.
5. Cache only stable expensive steps with a user-controlled cache; do not bake
   local cache paths into reusable skill content.

## Deprecation and Version Notes

- Nilearn source-checkout/dev versions may include deprecation notes not present
  in older releases. Prefer inspecting the installed signature before relying on
  a parameter.
- `ConnectivityMeasure.standardize=True` is documented as a compatibility path
  whose behavior is changing; choose an explicit standardization mode when a
  project requires reproducibility.
- Some estimators expose coefficient images only for linear models or supported
  image inputs. Check fitted attributes before promising maps.
