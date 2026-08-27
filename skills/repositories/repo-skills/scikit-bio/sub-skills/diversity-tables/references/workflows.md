# Diversity and Table Workflows

## Prepare Count Inputs

1. Decide the row/column meaning before calling scikit-bio: rows are samples, columns are features/taxa.
2. Use `ids=` for sample IDs when the input does not carry row labels, such as a NumPy array or nested list.
3. Use `taxa=` for feature/taxon IDs when computing Faith PD or UniFrac, unless a `Table` or DataFrame already carries feature IDs and you trust their order.
4. Validate non-negative numeric counts before analysis. Leave `validate=True` unless the data were already checked by the same workflow.
5. For BIOM-style `Table` construction, pass `data` as observations/features by samples: `Table(data, observation_ids, sample_ids)`. When feeding arrays directly to diversity drivers, pass samples by features.

Minimal dense count setup:

```python
import numpy as np

counts = np.array([
    [1, 5],
    [2, 3],
    [0, 1],
])
sample_ids = ["A", "B", "C"]
taxa = ["O1", "O2"]
```

## Compute Alpha Diversity

Use `alpha_diversity` for one or more samples. The result is a `pandas.Series`.

```python
from skbio.diversity import alpha_diversity

richness = alpha_diversity("sobs", counts, ids=sample_ids)
```

Operational checks:

- `len(richness)` must equal number of samples.
- `list(richness.index)` should equal `sample_ids` when provided or extractable.
- Unknown metric strings raise `ValueError`; discover names with `get_alpha_diversity_metrics()`.
- Extra metric kwargs raise `TypeError` when the metric does not accept them.

## Compute Faith PD

Faith PD routes through `alpha_diversity("faith_pd", ...)` and requires a rooted branch-length tree plus taxa in feature-column order.

```python
from skbio import TreeNode
from skbio.diversity import alpha_diversity

tree = TreeNode.read(["((O1:0.25,O2:0.50):0.25,O3:0.75)root;"])
faith = alpha_diversity("faith_pd", counts, ids=sample_ids, taxa=taxa, tree=tree)
```

If the task involves creating, rooting, pruning, or repairing the tree, use `../trees-phylogeny/SKILL.md`. This sub-skill owns only the diversity-driver call and input alignment.

## Compute Beta Diversity

Use `beta_diversity` for a full all-by-all distance matrix. The result is a `DistanceMatrix` that can be routed to statistics/ordination workflows.

```python
from skbio.diversity import beta_diversity

bray = beta_diversity("braycurtis", counts, ids=sample_ids)
```

Check:

- `bray.shape == (n_samples, n_samples)`.
- The diagonal is zero.
- `bray.ids` are the sample IDs.
- Route PERMANOVA, ANOSIM, ordination, clustering, and plotting to `../statistics-ordination/SKILL.md`.

## Compute UniFrac

UniFrac is beta diversity with phylogenetic context.

```python
unweighted = beta_diversity(
    "unweighted_unifrac",
    counts,
    ids=sample_ids,
    taxa=taxa,
    tree=tree,
)
weighted = beta_diversity(
    "weighted_unifrac",
    counts,
    ids=sample_ids,
    taxa=taxa,
    tree=tree,
    normalized=True,
)
```

Use string metric names unless there is a strong reason to call lower-level functions. The string path uses optimized setup and avoids the slow-callable warning for UniFrac.

## Partial Pairwise Distances

Use `partial_beta_diversity` only when a downstream process explicitly needs selected ID pairs and can tolerate zero-filled uncomputed entries.

```python
from skbio.diversity import partial_beta_diversity

partial = partial_beta_diversity(
    "unweighted_unifrac",
    counts,
    ids=sample_ids,
    id_pairs=[("B", "C")],
    taxa=taxa,
    tree=tree,
)
```

Rules:

- `ids` is required.
- `id_pairs` must be unique, non-self pairs, and all IDs must be a subset of `ids`.
- Do not interpret zeros as evidence of equality unless that pair was explicitly computed.

## Large Beta Diversity with Blocks

Use `block_beta_diversity` when the matrix is large enough that block decomposition or external parallel map/reduce is useful.

```python
from skbio.diversity import block_beta_diversity

large_dm = block_beta_diversity("braycurtis", counts, ids=sample_ids, k=64)
```

Guidance:

- For a few hundred samples or fewer, prefer `beta_diversity` first.
- `k` controls block size; larger blocks reduce overhead but increase per-block memory.
- `map_f` must call the provided block function with keyword arguments; map APIs that cannot pass `**kwargs` are not compatible.
- `reduce_f` combines partial distance matrices into a final `DistanceMatrix`.
- Pass `tree=` and `taxa=` exactly as for `beta_diversity` when using UniFrac.

## Convert BIOM-Style Tables Safely

A `skbio.table.Table` is a BIOM table. BIOM data are observation by sample at construction time.

```python
import numpy as np
from skbio.table import Table

biom_data = np.array([
    [1, 2, 0],  # O1 across A, B, C
    [5, 3, 1],  # O2 across A, B, C
])
table = Table(biom_data, observation_ids=["O1", "O2"], sample_ids=["A", "B", "C"])

sample_ids = list(table.ids())
taxa = list(table.ids(axis="observation"))
counts = table.matrix_data.T.toarray()
```

The transpose in `table.matrix_data.T.toarray()` is intentional: it converts BIOM observation-by-sample storage into diversity-driver sample-by-feature rows. If avoiding direct matrix access, pass `table` directly to `alpha_diversity` or `beta_diversity` and let scikit-bio ingest IDs.

## Use Pandas Table-Like Inputs

Pandas is often the safest explicit table-like bridge because index and columns preserve IDs.

```python
import pandas as pd
from skbio.diversity import beta_diversity

df = pd.DataFrame(counts, index=sample_ids, columns=taxa)
dm = beta_diversity("braycurtis", df)
```

Do not transpose a DataFrame unless its rows are currently features and columns are samples. After any transpose, re-check that row labels are sample IDs and column labels are taxa.

## Run Table Augmentation

Use augmentation functions to produce synthetic samples for machine-learning workflows, not to replace diversity metrics.

```python
from skbio.table import mixup, aitchison_mixup, compos_cutmix

labels = [0, 1, 0]
aug_counts, aug_labels = mixup(counts, n=4, labels=labels, seed=42)
aug_comp, aug_comp_labels = aitchison_mixup(counts, n=4, labels=labels, seed=42)
cutmix_comp, cutmix_labels = compos_cutmix(counts, n=4, labels=labels, seed=42)
```

For `phylomix`, provide a tree and taxa aligned to feature columns:

```python
from skbio.table import phylomix

phylo_aug, phylo_labels = phylomix(
    counts,
    n=4,
    tree=tree,
    taxa=taxa,
    labels=labels,
    seed=42,
)
```

## Smoke Check Script

Run the bundled script from the `diversity-tables` sub-skill directory:

```bash
python scripts/diversity_table_smoke.py
```

It prints JSON containing observed richness, Bray-Curtis distances, Faith PD, UniFrac, and `Table` conversion details. Use `--help` for options.
