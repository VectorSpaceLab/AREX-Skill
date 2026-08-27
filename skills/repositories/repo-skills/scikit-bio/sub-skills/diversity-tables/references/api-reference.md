# Diversity and Table API Reference

## Diversity Drivers

| API | Use | Key signature | Return | Notes |
| --- | --- | --- | --- | --- |
| `skbio.diversity.alpha_diversity` | Per-sample community diversity. | `alpha_diversity(metric, counts, ids=None, validate=True, **kwargs)` | `pandas.Series` indexed by sample IDs when supplied or extractable. | `counts` is one sample vector `(n_taxa,)` or a matrix `(n_samples, n_taxa)`. Prefer string metrics for optimized code paths. |
| `skbio.diversity.beta_diversity` | Pairwise sample distances. | `beta_diversity(metric, counts, ids=None, validate=True, pairwise_func=None, **kwargs)` | `skbio.DistanceMatrix` with rows/columns equal to sample IDs. | Uses SciPy `pdist` by default; supports scikit-bio beta metrics and many SciPy metric strings. |
| `skbio.diversity.partial_beta_diversity` | Compute only selected pairs. | `partial_beta_diversity(metric, counts, ids, id_pairs, validate=True, **kwargs)` | `DistanceMatrix` containing selected distances. | Deprecated/unstable return semantics: uncomputed pairs are zeros, which can be real distances. Requires explicit `ids`; string metrics are limited to optimized UniFrac names, otherwise pass a callable. |
| `skbio.diversity.block_beta_diversity` | Block-decomposed beta diversity for large matrices. | `block_beta_diversity(metric, counts, ids=None, validate=True, k=64, reduce_f=None, map_f=None, **kwargs)` | `DistanceMatrix` with the original sample IDs. | Designed for parallel map/reduce execution. For a few hundred samples or fewer, `beta_diversity` is usually faster. |
| `skbio.diversity.get_alpha_diversity_metrics` | Discover valid alpha metric strings. | `get_alpha_diversity_metrics()` | Alphabetically sorted `list[str]`. | Includes scikit-bio alpha functions such as `faith_pd`, `sobs`, and `chao1`. |
| `skbio.diversity.get_beta_diversity_metrics` | Discover valid beta metric strings. | `get_beta_diversity_metrics()` | Alphabetically sorted `list[str]`. | Includes SciPy `pdist` metric strings plus `unweighted_unifrac` and `weighted_unifrac`. |

## Table Orientation and IDs

Scikit-bio standardizes table data as rows = samples and columns = features. Diversity modules call features taxa when those columns represent organisms or sequence variants.

| Input format | Sample IDs | Feature/taxon IDs | Practical notes |
| --- | --- | --- | --- |
| `skbio.table.Table` / BIOM table | `table.ids()` | `table.ids(axis="observation")` | BIOM calls features observations; scikit-bio diversity treats them as taxa when using phylogenetic metrics. |
| `pandas.DataFrame` | DataFrame index | DataFrame columns | This is the safest table-like input when preserving labels in notebooks or scripts. |
| `numpy.ndarray` or nested lists | Provide `ids=` manually or get integer IDs | Provide `taxa=` manually for phylogenetic metrics | Shape must be `(n_samples, n_taxa)`; one vector is treated as one sample. |
| Polars DataFrame | integer sample IDs unless supplied separately | schema columns | Useful for table-like ingestion, but downstream outputs may still be pandas/NumPy/scikit-bio objects. |
| AnnData | `.obs.index` | `.var.index` | Optional dependency; do not assume installed unless the user environment has it. |

`Table` construction follows the BIOM convention: `Table(data, observation_ids, sample_ids, observation_metadata=None, sample_metadata=None, ...)`. The `data` matrix is feature/observation by sample for BIOM construction, while diversity driver matrices are sample by feature after ingestion. This is the common axis trap.

## Metric Selection

- Alpha richness: use `metric="sobs"` for observed features/taxa.
- Alpha phylogenetic diversity: use `metric="faith_pd"` with `tree=` and `taxa=`; the tree must be rooted and have branch lengths for all relevant nodes.
- Beta count distances: use `metric="braycurtis"` for abundance dissimilarity, `metric="jaccard"` for qualitative presence/absence behavior, or another value from `get_beta_diversity_metrics()`.
- Beta phylogenetic distances: use `metric="unweighted_unifrac"` for presence/absence phylogenetic distance and `metric="weighted_unifrac"` for abundance-weighted phylogenetic distance; both need `tree=` and `taxa=`.
- Prefer string metric names over callables for optimized Faith PD and UniFrac paths. Passing `weighted_unifrac` or `unweighted_unifrac` as a callable works but can trigger slower code paths.
- Custom callables are allowed: alpha callables receive one sample vector; beta callables receive two sample vectors. If a custom callable declares a `taxa` parameter, scikit-bio can pass `taxa` through.

## Phylogenetic Requirements

Faith PD and UniFrac require a `skbio.TreeNode` and a taxon list aligned to the feature columns in `counts`.

- `taxa` length must equal the number of feature columns.
- Taxon IDs must be unique.
- Required taxa must be present as tree tip names; the tree may contain extra tips.
- Branch lengths must be present for the relevant tree nodes.
- Faith PD expects a rooted tree; UniFrac validation also rejects unrooted or invalid trees in the optimized setup used by the drivers.
- If the input is a `Table` or DataFrame with feature IDs, `taxa` can often be omitted for phylogenetic drivers, but pass it explicitly when any axis or ID transformation is uncertain.

## Table Augmentation APIs

| API | Key signature | Output | When to use |
| --- | --- | --- | --- |
| `mixup` | `mixup(table, n, labels=None, intra_class=False, alpha=2.0, append=False, seed=None)` | `(aug_matrix, aug_labels)` | Vanilla linear interpolation between sample pairs. Labels may be integer or one-hot and are returned one-hot when provided. |
| `aitchison_mixup` | `aitchison_mixup(table, n, labels=None, intra_class=False, alpha=2.0, normalize=True, append=False, seed=None)` | `(aug_matrix, aug_labels)` | Mix compositions in Aitchison geometry; normalizes rows to sum to one when `normalize=True`. |
| `compos_cutmix` | `compos_cutmix(table, n, labels=None, normalize=True, append=False, seed=None)` | `(aug_matrix, aug_labels)` | Compositional cutmix, always effectively intra-class when labels are provided. |
| `phylomix` | `phylomix(table, n, tree, taxa=None, labels=None, intra_class=False, alpha=2.0, append=False, seed=None)` | `(aug_matrix, aug_labels)` | Phylogeny-aware augmentation. Requires taxa either from table feature IDs or `taxa=` and a tree whose tips contain those taxa. |

Augmentation helpers accept table-like inputs shaped as samples by features after ingestion. They need at least one valid pair of samples. Labels must match sample count, be zero-indexed consecutive integers when 1-D, or be valid one-hot rows when 2-D.
