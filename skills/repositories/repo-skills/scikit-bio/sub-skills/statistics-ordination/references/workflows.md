# Statistics and Ordination Workflows

## Build and Inspect a DistanceMatrix

Use explicit sample IDs whenever a matrix will be joined to metadata.

```python
from skbio import DistanceMatrix

dm = DistanceMatrix(
    [
        [0.0, 0.25, 0.75, 0.80],
        [0.25, 0.0, 0.70, 0.78],
        [0.75, 0.70, 0.0, 0.20],
        [0.80, 0.78, 0.20, 0.0],
    ],
    ids=["s1", "s2", "s3", "s4"],
)
assert dm.shape == (4, 4)
assert dm.ids == ("s1", "s2", "s3", "s4")
```

If distances come from count data, route count/table preparation and beta-diversity calculation to `../diversity-tables/SKILL.md`; return here with the resulting `DistanceMatrix`.

## Align Metadata to Distance IDs

Prefer a `pandas.Series` or `DataFrame` indexed by sample ID. Scikit-bio will reorder metadata rows to match `distmat.ids` and ignore extra metadata rows.

```python
import pandas as pd

metadata = pd.DataFrame(
    {"treatment": ["A", "B", "A", "B", "unused"]},
    index=["s2", "s4", "s1", "s3", "s_extra"],
)
# All IDs in dm.ids must be present in metadata.index.
assert set(dm.ids).issubset(metadata.index)
```

For a plain grouping vector, verify the order yourself:

```python
grouping = ["A", "A", "B", "B"]  # same order as dm.ids
assert len(grouping) == len(dm.ids)
```

## Test Group Differences and Dispersion

Run PERMANOVA or ANOSIM for location/group separation, then PERMDISP to check whether dispersion differences may explain the result.

```python
from skbio.stats.distance import permanova, anosim, permdisp

permanova_result = permanova(dm, metadata, column="treatment", permutations=999, seed=42)
anosim_result = anosim(dm, metadata, column="treatment", permutations=999, seed=42)
permdisp_result = permdisp(
    dm,
    metadata,
    column="treatment",
    permutations=999,
    seed=42,
    dimensions=dm.shape[0],
)

pseudo_f = float(permanova_result["test statistic"])
p_value = float(permanova_result["p-value"])
```

Reporting guidance:

- Report method name, statistic name, statistic, sample size, number of groups, p-value, and permutations.
- Include the random seed in reproducible methods sections.
- Treat low permutations as a smoke check only; p-value precision is `1 / (1 + permutations)`.
- If PERMANOVA is significant and PERMDISP is also significant, describe the result as potentially driven by heterogeneous dispersion rather than group centroids alone.

## Compare Distance Matrices

Use `mantel` for two matrices and `pwmantel` for multiple matrices.

```python
from skbio.stats.distance import mantel, pwmantel

coeff, p_value, n = mantel(dm, dm.copy(), method="pearson", permutations=99, seed=42)

pairwise = pwmantel(
    [dm, dm.copy(), dm.copy()],
    labels=["bray", "unifrac", "embedding"],
    method="spearman",
    permutations=99,
    seed=42,
)
```

When IDs differ but represent the same samples, prefer fixing IDs before analysis. Use `lookup=` only when there is a deliberate crosswalk between two naming systems:

```python
coeff, p_value, n = mantel(dm_a, dm_b, lookup={"sample-1": "s1"}, strict=False)
```

Check that `n` is still scientifically meaningful after any `strict=False` discard.

## Search Environmental Variables with BIOENV

`bioenv` takes a distance matrix and numeric metadata. It ranks subsets of variables by correlation between biological distances and Euclidean distances in the scaled metadata subset.

```python
from skbio.stats.distance import bioenv

numeric_metadata = metadata.assign(ph=7.0, temperature=[20.1, 21.0, 19.8, 22.2, 18.0])
result = bioenv(dm, numeric_metadata.loc[list(dm.ids)], columns=["ph", "temperature"])
```

Use BIOENV as exploratory evidence; it does not prove causality.

## Run PCoA on a DistanceMatrix

```python
from skbio.stats.ordination import pcoa

ordination = pcoa(dm, method="eigh", dimensions=2, warn_neg_eigval=0.01)
sample_coordinates = ordination.samples
variance = ordination.proportion_explained
```

Operational checks:

- `ordination.samples.index` should match `dm.ids`.
- Use `dimensions=2` or `3` when only plotting/reporting a few axes.
- Use `method="fsvd"` with an integer `dimensions` for large matrices when an approximate ordination is acceptable.
- Set `warn_neg_eigval=False` only after deciding that negative eigenvalues are expected and not material for the interpretation.

## Add Biplot Scores to PCoA

`pcoa_biplot` projects descriptors into an existing PCoA ordination. Rows must align to the PCoA sample IDs.

```python
import pandas as pd
from skbio.stats.ordination import pcoa_biplot

descriptors = pd.DataFrame(
    {"ph": [6.8, 7.1, 5.9, 6.2], "temperature": [20.1, 21.0, 19.8, 22.2]},
    index=list(dm.ids),
)
with_biplot = pcoa_biplot(ordination, descriptors)
```

## Run CA, CCA, or RDA on Tables

Use sample-by-feature tables. For table preparation and axis repairs, route to `../diversity-tables/SKILL.md`.

```python
import pandas as pd
from skbio.stats.ordination import ca, cca, rda

community = pd.DataFrame(
    [[10, 0, 2], [8, 1, 1], [0, 7, 3], [1, 6, 4]],
    index=["s1", "s2", "s3", "s4"],
    columns=["taxon_a", "taxon_b", "taxon_c"],
)
environment = pd.DataFrame(
    {"moisture": [0.2, 0.3, 0.8, 0.7], "treatment_B": [0, 0, 1, 1]},
    index=community.index,
)

ca_result = ca(community, scaling=1)
cca_result = cca(community, environment, scaling=2)
rda_result = rda(community, environment, scale_Y=True, scaling=1)
```

Guidance:

- CA/CCA require non-negative response data; CCA also rejects rows that are all zero.
- RDA expects explanatory variables to have no more columns than rows and is better for linear gradients.
- CCA is often more appropriate for sparse ecological abundance with unimodal responses.
- Avoid perfect collinearity in constraints, such as all one-hot levels plus an intercept-like column.

## Transform Compositional Data with Zeros

Aitchison log-ratio transforms require strictly positive compositions. Close the data first, then replace zeros, then transform.

```python
import numpy as np
from skbio.stats.composition import closure, multi_replace, clr, ilr, alr

counts = np.array(
    [
        [10, 0, 5],
        [4, 2, 0],
        [0, 3, 9],
    ],
    dtype=float,
)
composition = closure(counts)
positive = multi_replace(composition)
clr_coordinates = clr(positive)
ilr_coordinates = ilr(positive)
alr_coordinates = alr(positive, ref_idx=0)
```

Scientific caution:

- `multi_replace` is a practical zero replacement, not proof that zeros were false zeros.
- For structural zeros, treatment-exclusive features, or heavy sparsity, report the zero-handling choice and consider sensitivity analysis.
- Use `rclr` when robust CLR behavior on count data with zeros is specifically desired.

## Run ANCOM and ANCOM-BC

ANCOM and ANCOM-BC require strictly positive sample-by-feature tables. Preserve sample IDs with a DataFrame.

```python
import pandas as pd
from skbio.stats.composition import ancom, ancombc, multi_replace, closure

table = pd.DataFrame(
    [[12, 11, 10], [9, 11, 12], [22, 21, 9], [20, 22, 10]],
    index=["s1", "s2", "s3", "s4"],
    columns=["f1", "f2", "f3"],
)
grouping = pd.Series(["treatment", "treatment", "placebo", "placebo"], index=table.index)

positive_table = pd.DataFrame(
    multi_replace(closure(table.to_numpy(dtype=float))),
    index=table.index,
    columns=table.columns,
)
ancom_df, percentile_df = ancom(positive_table, grouping, p_adjust="holm")

metadata = pd.DataFrame({"group": grouping}, index=table.index)
ancombc_result = ancombc(positive_table, metadata, formula="group")
```

For count data, adding a domain-justified pseudocount can be more interpretable than closure plus replacement. State the choice.

## Identify Structural Zeros Before Differential Abundance

```python
from skbio.stats.composition import struc_zero

structural = struc_zero(table, metadata, grouping="group", neg_lb=True)
```

Use `struc_zero` to flag features that may be absent by design in a group. Treat flagged features carefully before ANCOM, ANCOM-BC, or Dirichlet-multinomial modeling.

## Run Dirichlet-Multinomial Differential Tests

Use raw counts when possible. These functions add/use pseudocounts and draw posterior samples, so set `seed` for reproducibility.

```python
from skbio.stats.composition import dirmult_ttest

result = dirmult_ttest(
    table,
    grouping,
    treatment="treatment",
    reference="placebo",
    pseudocount=0.5,
    draws=128,
    seed=42,
)
```

For repeated measures or random effects:

```python
from skbio.stats.composition import dirmult_lme

metadata = metadata.assign(subject=["p1", "p1", "p2", "p2"], time=[1, 2, 1, 2])
lme_result = dirmult_lme(
    table,
    metadata,
    formula="time + group",
    grouping="subject",
    draws=128,
    seed=42,
)
```

Expect mixed models to be slower and more sensitive to convergence than simple tests.

## Convert Protein Embeddings to Distances and Ordination

Use `ProteinVector` when each sequence has a single fixed-length vector.

```python
import numpy as np
from skbio.embedding import (
    ProteinVector,
    embed_vec_to_dataframe,
    embed_vec_to_distances,
    embed_vec_to_ordination,
)

vectors = [
    ProteinVector(np.array([0.1, 0.2, 0.3]), "ACDE"),
    ProteinVector(np.array([0.2, 0.1, 0.4]), "ACDF"),
    ProteinVector(np.array([0.9, 0.8, 0.7]), "WYVR"),
]
frame = embed_vec_to_dataframe(vectors)
embedding_dm = embed_vec_to_distances(vectors, metric="euclidean")
embedding_ord = embed_vec_to_ordination(vectors)
```

If vector IDs collide because two sequences have the same string representation, disambiguate before downstream joins by managing labels outside the vector objects or by storing a separate lookup table.

## Run the Bundled Smoke Check

```bash
python scripts/stats_ordination_smoke.py --strict
```

The script should print JSON with `ok: true`, PERMANOVA/PCoA summaries, CLR coordinates, and embedding-derived distance IDs. Use `--help` for options.
