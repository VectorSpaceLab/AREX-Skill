# Statistics and Ordination API Reference

## Distance Matrix Objects

| API | Key signature | Return/object | Practical notes |
| --- | --- | --- | --- |
| `skbio.stats.distance.PairwiseMatrix` | `PairwiseMatrix(data, ids=None, validate=True)` | Square pairwise relationship matrix. | Does not require symmetry or hollowness. Use when values are directional or general pairwise relationships. |
| `skbio.stats.distance.SymmetricMatrix` | `SymmetricMatrix(data, ids=None, validate=True, condensed=False)` | Symmetric pairwise matrix. | Requires `D[i, j] == D[j, i]`; diagonal may be nonzero. |
| `skbio.DistanceMatrix` / `skbio.stats.distance.DistanceMatrix` | `DistanceMatrix(data, ids=None, validate=True, condensed=False)` | Symmetric hollow matrix with unique string IDs. | Requires symmetry and zero diagonal, but not metric non-negativity or triangle inequality. Accepts square form, condensed vector form, or another pairwise matrix. |
| `randdm` | `randdm(num_objects, ids=None, constructor=None, random_fn=None)` | Random `DistanceMatrix` by default. | Pass `random_fn=<int seed>` for deterministic random distances; default IDs start at `'1'`. |

Useful `DistanceMatrix` methods and properties:

- `.ids`: tuple of IDs; can be assigned a same-length unique string sequence.
- `.data`: square NumPy array view in redundant form unless constructed/stored as condensed internally.
- `.condensed_form()`: SciPy-style vector of upper-triangle distances.
- `.to_data_frame()`: full square `pandas.DataFrame` with IDs on both axes.
- `.to_series()`: condensed distances as a `pandas.Series` indexed by ID pairs.
- `DistanceMatrix.read(handle_or_path)` and `.write(handle_or_path)` use scikit-bio matrix I/O formats.

## Distance-Based Statistical Tests

| API | Key signature | Return | Use when |
| --- | --- | --- | --- |
| `permanova` | `permanova(distmat, grouping, column=None, permutations=999, seed=None)` | `pandas.Series` with method, pseudo-F, sample size, groups, p-value, permutations. | Test whether group centroids differ in distance space. |
| `anosim` | `anosim(distmat, grouping, column=None, permutations=999, seed=None)` | `pandas.Series` with ANOSIM R statistic and p-value. | Test whether between-group ranks exceed within-group ranks. |
| `permdisp` | `permdisp(distmat, grouping, column=None, test='median', permutations=999, method='eigh', dimensions=10, seed=None, warn_neg_eigval=0.01)` | `pandas.Series` with F-value and p-value. | Test homogeneity of multivariate dispersion; pair with PERMANOVA to distinguish location vs dispersion. |
| `mantel` | `mantel(x, y, method='pearson', permutations=999, alternative='two-sided', strict=True, lookup=None, seed=None)` | `(corr_coeff, p_value, n)` tuple. | Correlate two distance matrices, optionally reordering by IDs or mapping IDs with `lookup`. |
| `pwmantel` | `pwmantel(dms, labels=None, method='pearson', permutations=999, alternative='two-sided', strict=True, lookup=None, seed=None)` | `pandas.DataFrame` of pairwise Mantel results. | Compare three or more distance matrices. |
| `bioenv` | `bioenv(distmat, data_frame, columns=None)` | `pandas.DataFrame` with candidate variable subsets and correlations. | Search numeric environmental variables whose Euclidean distances best correlate with a biological distance matrix. |

`grouping` rules for `permanova`, `anosim`, and `permdisp`:

- A 1-D vector must be in the exact same order and length as `distmat.ids`.
- A `pandas.Series` or `pandas.DataFrame` is safer when IDs may be reordered; its index must include all distance-matrix IDs.
- Pass `column=` only for a `DataFrame` or to match a named `Series`; extra metadata rows are ignored, missing distance-matrix IDs fail.
- `permutations=0` computes the statistic and returns `NaN` p-value.
- `seed=` makes permutation p-values reproducible for scripts and examples.

## Ordination APIs

| API | Key signature | Return | Notes |
| --- | --- | --- | --- |
| `pcoa` | `pcoa(distmat, method='eigh', dimensions=0, inplace=False, seed=None, warn_neg_eigval=0.01, output_format=None)` | `OrdinationResults` | Principal coordinates from a `DistanceMatrix`. `dimensions=0` keeps all axes; integer keeps that many axes; float `(0, 1)` keeps enough axes to reach cumulative variance. |
| `pcoa_biplot` | `pcoa_biplot(ordination, y)` | `OrdinationResults` with biplot scores | Adds descriptors or features to an existing PCoA result. |
| `ca` | `ca(X, scaling=1, sample_ids=None, feature_ids=None, output_format=None)` | `OrdinationResults` | Correspondence analysis for non-negative sample-by-feature tables, useful for many zeros and chi-square distances. |
| `cca` | `cca(y, x, scaling=1, sample_ids=None, feature_ids=None, constraint_ids=None, output_format=None)` | `OrdinationResults` | Canonical correspondence analysis for non-negative community table `y` and explanatory table `x` with matching sample rows. |
| `rda` | `rda(y, x, scale_Y=False, scaling=1, sample_ids=None, feature_ids=None, constraint_ids=None, output_format=None)` | `OrdinationResults` | Redundancy analysis for linear relationships between response table `y` and explanatory variables `x`. |
| `mmvec` | `mmvec(X, Y, dimensions=3, optimizer='lbfgs', max_iter=1000, ..., seed=None, verbose=False, output_format=None)` | `MMvecResult` | Joint embeddings for two sample-aligned count/compositional modalities. Use small `max_iter` only for smoke checks. |

`OrdinationResults` fields commonly used by agents:

- `.samples`: sample coordinates as a table-like object, normally DataFrame-like with sample IDs.
- `.features`: feature coordinates when the method produces them.
- `.eigvals`: eigenvalues or singular values squared, indexed by axes.
- `.proportion_explained`: per-axis variance proportions when available.
- `.biplot_scores` and `.sample_constraints`: present for constrained/biplot workflows.
- `.short_method_name` and `.long_method_name`: method labels for reporting.

## Composition APIs

| API | Key signature | Return | Use when |
| --- | --- | --- | --- |
| `closure` | `closure(mat, axis=-1, validate=True)` | Closed composition summing to one along `axis`. | Convert non-negative data to proportions before Aitchison operations. |
| `multi_replace` | `multi_replace(mat, delta=None)` | Composition with zeros replaced by small positive values. | Prepare closed data containing zeros before log-ratio transforms. |
| `clr` | `clr(mat, axis=-1, validate=True)` | Centered log-ratio coordinates. | Transform strictly positive compositions for Euclidean methods or downstream modeling. |
| `ilr` | `ilr(mat, basis=None, axis=-1, validate=True)` | Isometric log-ratio coordinates. | Use orthonormal coordinates with an optional basis such as `sbp_basis` or `tree_basis`. |
| `alr` | `alr(mat, ref_idx=0, axis=-1, validate=True)` | Additive log-ratio coordinates. | Compare features to an explicit reference component. |
| `rclr` | `rclr(mat, axis=-1, validate=True)` | Robust CLR-like coordinates. | Work with count matrices containing zeros when robust centered log-ratio behavior is intended. |
| `vlr` / `pairwise_vlr` | `vlr(x, y, ddof=1, robust=False)` / `pairwise_vlr(mat, ids=None, ddof=1, robust=False, validate=True)` | Ratio variance scalar or distance-like matrix. | Summarize pairwise log-ratio variability. |
| `ancom` | `ancom(table, grouping, alpha=0.05, tau=0.02, theta=0.1, p_adjust='holm', sig_test='f_oneway', percentiles=None)` | `(ancom_df, percentile_df)` | Differential abundance for strictly positive sample-by-feature tables. |
| `ancombc` | `ancombc(table, metadata, formula, grouping=None, max_iter=100, tol=1e-5, alpha=0.05, p_adjust='holm')` | main result DataFrame; optionally global result DataFrame. | Bias-corrected differential abundance using metadata formula terms. |
| `struc_zero` | `struc_zero(table, metadata, grouping, neg_lb=False)` | Structural-zero result table. | Identify features absent in one or more groups before differential-abundance modeling. |
| `dirmult_ttest` | `dirmult_ttest(table, grouping, treatment=None, reference=None, pseudocount=0.5, draws=128, p_adjust='holm', seed=None)` | Feature-level differential-abundance DataFrame. | Two-group or treatment-vs-reference Dirichlet-multinomial analysis. |
| `dirmult_lme` | `dirmult_lme(table, metadata, formula, grouping, pseudocount=0.5, draws=128, p_adjust='holm', seed=None, ...)` | Feature/covariate result DataFrame. | Repeated-measures or mixed-effect Dirichlet-multinomial analysis. |

Composition orientation is rows = samples and columns = components/features for differential-abundance functions. Log-ratio transforms operate along `axis`, defaulting to the last axis.

## Embedding APIs

| API | Key signature | Return | Notes |
| --- | --- | --- | --- |
| `SequenceEmbedding` | `SequenceEmbedding(embedding, sequence, **kwargs)` | Per-character sequence embedding object. | `embedding.shape[0]` must match sequence length. |
| `ProteinEmbedding` | `ProteinEmbedding(embedding, sequence, clip_head=False, clip_tail=False, **kwargs)` | Protein sequence embedding object. | Validates protein sequence; clip start/end token rows when needed. |
| `SequenceVector` | `SequenceVector(vector, sequence, **kwargs)` | One vector for one sequence. | Vector may be 1-D or one-row 2-D. |
| `ProteinVector` | `ProteinVector(vector, sequence, **kwargs)` | One vector for one protein sequence. | Validates sequence with `skbio.sequence.Protein`. |
| `embed_vec_to_numpy` | `embed_vec_to_numpy(vectors, validate=True)` | `(n_objects, n_features)` NumPy array. | Requires same vector subclass and same length when validating. |
| `embed_vec_to_distances` | `embed_vec_to_distances(vectors, metric='euclidean', validate=True)` | `DistanceMatrix` with vector string IDs. | Distance metric follows SciPy `pdist`/diversity metric semantics. |
| `embed_vec_to_ordination` | `embed_vec_to_ordination(vectors, validate=True)` | `OrdinationResults` from SVD. | Samples are object IDs; features are latent dimensions. |
| `embed_vec_to_dataframe` | `embed_vec_to_dataframe(vectors, validate=True)` | `pandas.DataFrame` with vectors as rows. | Convenient bridge to ML or reporting code. |

Use embedding vectors when each biological object already has one fixed-length vector. Use embedding matrices when each character/residue has coordinates and the task needs sequence-level storage or serialization.
