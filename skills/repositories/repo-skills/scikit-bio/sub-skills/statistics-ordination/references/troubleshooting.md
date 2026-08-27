# Statistics and Ordination Troubleshooting

## DistanceMatrix Construction Fails

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Data must be symmetric` | `data[i, j]` differs from `data[j, i]` or matrix contains `NaN`. | Recompute distances with a symmetric method, average mirrored cells only if scientifically justified, and remove/impute `NaN` before construction. |
| `Data must be hollow` | Diagonal contains nonzero self-distances. | Set true self-distances to zero only after confirming rows/columns represent identical IDs in the same order. |
| ID length error | Number of `ids` does not match matrix dimension. | Rebuild the ID list from the matrix rows/columns and assert `len(ids) == data.shape[0]`. |
| Duplicate ID error | IDs are not unique strings. | Deduplicate upstream sample labels before constructing the matrix; do not append suffixes silently if duplicates are biological replicates that need aggregation or separate metadata. |
| Unexpected default IDs | `ids=None` was used. | Pass explicit sample IDs before joining to metadata or reporting results. |

`validate=False` can bypass checks, but only use it when the same workflow already proved symmetry, hollowness, and unique IDs. Invalid distance matrices can produce misleading statistics and ordinations.

## Grouping and Metadata Mismatches

Distance tests often fail because distance IDs and metadata IDs are similar but not identical.

Checklist:

1. Compare `set(distmat.ids)` with `set(metadata.index)`.
2. Find missing IDs: `set(distmat.ids) - set(metadata.index)`.
3. Find extra metadata rows: `set(metadata.index) - set(distmat.ids)`; extras are acceptable for `DataFrame`/`Series` grouping.
4. Normalize only reversible differences such as whitespace, case, or known prefixes.
5. Use a metadata `DataFrame` indexed by sample ID rather than a positional vector when order is uncertain.

Common errors:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Must provide a column name if supplying a DataFrame` | `grouping` is a DataFrame and `column` is missing. | Pass `column="your_group_column"`. |
| `Must provide a DataFrame if supplying a column name` | `column` was passed with a list/array grouping. | Remove `column` or convert grouping to a DataFrame. |
| `Grouping vector size must match` | Positional grouping length differs from matrix size. | Use ID-indexed metadata or rebuild the vector in `distmat.ids` order. |
| `All values ... are unique` | Every sample has its own group. | Use a grouping variable with replicates or choose a different statistical method. |
| `All values ... are the same` | No between-group comparison exists. | Add/choose a grouping with at least two groups. |

## Recover from Metadata IDs Not Matching Distance IDs

Use this pattern for difficult mixed-source analyses:

```python
missing = sorted(set(dm.ids) - set(metadata.index))
if missing:
    raise ValueError(f"metadata is missing distance IDs: {missing}")
metadata_for_dm = metadata.loc[list(dm.ids)]
```

If IDs differ by a known mapping, build and audit the mapping explicitly:

```python
crosswalk = {"sample_001": "s1", "sample_002": "s2"}
renamed = metadata.rename(index=crosswalk)
assert set(dm.ids).issubset(renamed.index)
```

Do not use `strict=False` in `mantel` or silently drop samples in group tests unless the user explicitly accepts the reduced sample set and you report the final `n`.

## Permutation Count and Seed Confusion

| Issue | Explanation | Action |
| --- | --- | --- |
| P-value changes between runs | Permutation tests are stochastic when `seed` is omitted. | Pass `seed=<int>` or a stable generator in scripts and examples. |
| P-value looks coarse | Precision is limited by `1 / (1 + permutations)`. | Use at least 999 permutations for routine analysis; more for publication-grade p-values. |
| `permutations=0` gives `NaN` p-value | Scikit-bio skips significance calculation. | Use zero permutations only for statistic-only workflows or smoke checks. |
| Low-permutation smoke result is overinterpreted | A p-value from 9 or 99 permutations is not precise. | Label it as a runtime check, not inferential evidence. |

## PERMANOVA, ANOSIM, and PERMDISP Interpretation

- PERMANOVA tests group differences in distance space but can be sensitive to dispersion heterogeneity.
- ANOSIM uses rank differences and can be easier to communicate as R near 1 means stronger group separation.
- PERMDISP tests whether group dispersions differ; a significant PERMDISP result complicates PERMANOVA interpretation.
- Pair PERMANOVA with PERMDISP when the conclusion depends on centroid/location differences.
- Use the same grouping and seed across tests for reproducible method descriptions.

## Negative Eigenvalue Warnings in PCoA

PCoA may warn about negative eigenvalues when the distance matrix is non-Euclidean or violates metric assumptions.

Actions:

1. Check whether the distance metric is expected to be non-Euclidean, such as Bray-Curtis or some ecological dissimilarities.
2. Inspect the magnitude relative to the largest positive eigenvalue; small negatives often have limited practical impact.
3. Try a different distance transformation or metric if large negative eigenvalues dominate.
4. Report that PCoA axes approximate a non-Euclidean distance structure when warnings are material.
5. Do not suppress with `warn_neg_eigval=False` unless the warning has been evaluated.

For large matrices, specify `dimensions` explicitly. With `method="fsvd"`, `dimensions=0` can trigger a runtime warning because all axes are requested.

## Ordination Shape and Constraint Errors

| Method | Constraint | Typical fix |
| --- | --- | --- |
| `pcoa` | Input must be convertible to `DistanceMatrix`. | Validate symmetry/hollowness first. |
| `ca` | Table must be non-negative. | Remove invalid negative values or choose a method appropriate for signed data. |
| `cca` | Response table `y` must be non-negative and have no all-zero rows; `x` and `y` must share row count. | Filter empty samples, align rows by sample ID, and avoid collinear constraints. |
| `rda` | `x` and `y` must share row count; explanatory variables cannot have more columns than rows. | Drop redundant variables or reduce dimensionality. |
| `pcoa_biplot` | Descriptor rows must align to PCoA sample IDs. | Reindex descriptors with `ordination.samples.index` before calling. |

## Compositional Zeros Before Log-Ratio Transforms

`clr`, `ilr`, and `alr` require strictly positive compositions. Zeros cause invalid logarithms or validation errors.

Safe sequence:

```python
from skbio.stats.composition import closure, multi_replace, clr

closed = closure(counts)
positive = multi_replace(closed)
coords = clr(positive)
```

Scientific caution:

- Zero replacement assumes zeros are compatible with small positive imputation; this can be risky for structural zeros, detection-limit zeros, or treatment-exclusive taxa.
- Pseudocounts can change log-ratio magnitudes for rare features.
- For sensitivity, compare several plausible pseudocount/replacement choices or use methods designed for sparse compositional data.
- Document whether data were raw counts, proportions, closed compositions, or pseudocount-adjusted values.

## ANCOM and ANCOM-BC Issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Zero-count error or log failure | Table contains zeros. | Add a justified pseudocount or apply `multi_replace(closure(...))` and preserve DataFrame labels. |
| Grouping length mismatch | Group vector does not match sample count or sample IDs. | Use `pd.Series(..., index=table.index)` or reindex grouping to table rows. |
| Missing metadata rows in ANCOM-BC | `metadata.index` lacks table sample IDs. | Align metadata to table rows and assert completeness before calling. |
| Patsy formula error | Formula references a missing/invalid metadata column. | Check `metadata.columns` and escape/rename problematic column names. |
| Unexpected reference level | Categorical levels are sorted or encoded by formula handling. | Recode categorical variables with explicit categories or document the baseline. |
| Shape confusion | Table is feature-by-sample instead of sample-by-feature. | Route to `../diversity-tables/SKILL.md` to repair orientation. |

ANCOM returns two DataFrames: the first has feature W-statistics and `Signif`; the second has percentile abundances. ANCOM-BC may return a main table and, when `grouping` is used for a global test, a global table.

## Structural Zeros and Pseudocount Risk

Use `struc_zero` before differential-abundance analysis when a feature appears absent from an entire group. If structural zeros are present:

- Do not treat pseudocount replacement as a neutral technical fix.
- Report features flagged as structural zeros separately from log-ratio differential tests.
- Consider filtering, stratified reporting, or a method designed for structural absence.
- Ask the domain owner whether the zero pattern is biological, technical, or preprocessing-induced.

## Dirichlet-Multinomial Test Problems

- Prefer raw count tables over proportions; proportions remove sequencing-depth magnitude information used by the model.
- Set `seed` because posterior draws are stochastic.
- Increase `draws` for final analysis; small values are for runtime checks only.
- Mixed-effect models can fail to converge for some features or draws; inspect `Reps`, warnings, and missing values in the result.
- `treatment` and `reference` default to sorted group choices; pass them explicitly for clear interpretation.

## Embedding Conversion Failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Only one vector per sequence is allowed` | A `SequenceVector`/`ProteinVector` received a matrix with multiple rows. | Use one fixed-length vector per object or use `SequenceEmbedding`/`ProteinEmbedding` for per-residue matrices. |
| Protein validation error | Sequence contains invalid protein characters or spaces in unexpected locations. | Clean/validate sequences before constructing `ProteinVector`; spaces are removed by protein validation. |
| `All vectors must have the same length` | Embedding vectors have inconsistent dimensionality. | Project/pad upstream embeddings to a common dimension before using conversion utilities. |
| `All objects must be of the same type` | Mixed vector classes are passed with `validate=True`. | Use a homogeneous vector class or set `validate=False` only after manually checking compatibility. |
| Duplicate distance IDs | Two vectors stringify to the same sequence. | Keep a separate mapping of unique sample IDs to sequence strings before downstream joins. |

## Optional Array API and GPU Backend Limits

Some composition arithmetic and PCoA centering utilities can operate on array-API-compatible arrays, including GPU-backed arrays in suitable environments. Limitations:

- Not every downstream statistical function accepts GPU arrays; many table/statistics APIs convert to NumPy or pandas.
- PCoA eigendecomposition may move data to host for backends that lack required partial-eigenvalue support.
- Differential-abundance functions rely on pandas, SciPy, statsmodels, and patsy-style CPU workflows.
- For reproducible skills and scripts, default to NumPy/pandas unless the task explicitly asks for GPU arrays and the environment is verified.

## Hard Cases to Exercise Later

- Recover from metadata IDs that differ from distance IDs by prefixes/case/order, prove the final aligned sample set, and avoid silently dropping unmatched samples.
- Transform a sparse compositional table with treatment-exclusive zeros, explain why `multi_replace` or pseudocounts may be scientifically risky, and propose sensitivity checks before interpreting CLR/ANCOM results.
