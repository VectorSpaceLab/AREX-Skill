# Global Tabular Workflows

## Purpose

Use this file to choose among Alibi's global tabular explanation methods and to remember the small set of inputs they expect.

## Method choice

| Method | Best for | Typical input | Main output |
| --- | --- | --- | --- |
| `ALE` | Correlated-feature-aware global effects | `numpy.ndarray` batches and a predictor that returns model outputs | ALE values, feature values, and deciles |
| `PartialDependence` | PD / ICE curves for tabular data | `numpy.ndarray` batches and a predictor | PD values and optional ICE values |
| `TreePartialDependence` | Faster PD for supported tree estimators | a tree estimator object | PD values from tree structure |
| `PartialDependenceVariance` | Feature importance or interaction strength from PD | a predictor or tree estimator | feature importance or interaction scores |
| `PermutationImportance` | Global feature importance by perturbing columns | data and labels plus a predictor | feature importance by metric |

## Workflow notes

### ALE

- Use ALE when correlated features make plain PD misleading.
- Pass `features=[...]` to focus on a subset of columns.
- Custom grid points must be monotonic for each feature.
- The result exposes ALE values, centering values, feature values, and deciles.

### Partial dependence

- Use `kind='average'`, `'individual'`, or `'both'` depending on whether you want PD, ICE, or both.
- Use `grid_resolution` to reduce dense numerical grids.
- Use `grid_points` when you need exact evaluation points.
- Tree-based PD uses the tree estimator directly and does not expose ICE.

### PD variance

- Use `method='importance'` for feature importance.
- Use `method='interaction'` for pairwise interaction strength.
- The method reuses PD calculations, so the same predictor and feature-layout rules apply.

### Permutation importance

- Use a predictor that is compatible with the metric you choose.
- `score_fns` works well with classifiers and metrics like accuracy or F1.
- `loss_fns` is better when you want the degradation to be framed as a loss increase.
- For `method='estimate'`, the helper returns a mean and spread over repeated perturbations.

## Safe usage pattern

1. Fit a tiny predictor on iris-sized data.
2. Run ALE or PD first to confirm the predictor contract.
3. Run PD variance or permutation importance only after the base smoke passes.
4. Treat plotting as an interpretation aid, not as proof that the model or data are valid.

## Read next

- `api-reference.md` for the exact signatures.
- `troubleshooting.md` for shape, grid, and plotting errors.
- `scripts/smoke_global_tabular.py` for a ready-made CPU smoke.
