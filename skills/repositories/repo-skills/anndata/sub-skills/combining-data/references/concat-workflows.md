# Concat Workflows

These recipes are self-contained patterns for combining `AnnData` objects and files. Construct and validate each individual object with `../data-model/SKILL.md`; use `../storage-io/SKILL.md` for H5AD/Zarr read/write details.

## 1. In-Memory Concat of Loaded Objects

Use `anndata.concat` when inputs are already loaded and the result should be a materialized `AnnData`.

```python
import anndata as ad

combined = ad.concat(
    {"control": control, "treated": treated},
    axis="obs",
    join="inner",
    label="batch",
    index_unique="-",
    merge="same",
    uns_merge="same",
)

assert combined.obs_names.is_unique
assert set(combined.obs["batch"].cat.categories) == {"control", "treated"}
```

Why this is a safe default:

- `axis="obs"` stacks observations/cells and aligns variables/genes.
- Mapping keys become provenance keys without needing a separate `keys` argument.
- `label="batch"` records the input source in `.obs`.
- `index_unique="-"` avoids duplicate observation names.
- `join="inner"` keeps only shared genes, avoiding silent sparse zero padding for absent genes.
- `merge="same"` and `uns_merge="same"` keep only metadata that matches across inputs.

## 2. Inner vs Outer Joins for Overlapping Genes

Use `join="inner"` when all retained genes must be measured in every batch.

```python
shared = ad.concat(adatas, axis="obs", join="inner", label="batch", keys=keys)
assert shared.n_vars <= min(a.n_vars for a in adatas)
```

Use `join="outer"` when retaining the union of genes is more important than a complete matrix.

```python
union = ad.concat(
    dict(zip(keys, adatas, strict=True)),
    axis="obs",
    join="outer",
    label="batch",
    index_unique="-",
    fill_value=None,
)
assert union.n_vars >= max(a.n_vars for a in adatas)
```

Outer-join checks:

- Sparse `.X` and sparse layers fill absent entries with zeros by default when `fill_value=None`.
- Dense arrays and DataFrames fill with missing values when `fill_value=None`.
- If zeros imply real measurements in the downstream method, prefer `join="inner"` or explicitly document the imputation meaning.

## 3. Batch Labels, Keys, and Duplicate Names

Use a mapping input when names are known:

```python
combined = ad.concat(
    {"donor_a": donor_a, "donor_b": donor_b, "donor_c": donor_c},
    label="donor",
    index_unique="-",
)
```

Use a sequence plus `keys` only when a mapping is inconvenient:

```python
combined = ad.concat(
    [donor_a, donor_b, donor_c],
    keys=["donor_a", "donor_b", "donor_c"],
    label="donor",
    index_unique="-",
)
```

Never pass `keys` with a mapping input. AnnData raises a `TypeError` because the mapping keys already define the categories.

Validation:

```python
assert combined.obs_names.is_unique
assert combined.obs["donor"].notna().all()
print(combined.obs["donor"].value_counts())
```

For `axis="var"`, the same pattern labels `.var` and makes variable names unique instead.

## 4. Merging `.uns` and Alternative-Axis Metadata

When stacking observations, directly observation-aligned elements are concatenated. Alternative-axis elements such as `.varm` are selected by `merge`; `.uns` is selected recursively by `uns_merge`.

```python
combined = ad.concat(
    batches,
    merge="unique",
    uns_merge="unique",
    label="batch",
    keys=batch_names,
)
```

Decision guide:

- Use `None` to drop metadata and avoid accidental conflict resolution.
- Use `"same"` for shared pipeline metadata, PCA loadings, or annotations expected to match after alignment.
- Use `"unique"` for non-conflicting metadata that may appear in only some inputs.
- Use `"only"` for metadata that is meaningful only when it appears in a single input.
- Use `"first"` only with an explicit first-input-wins policy.

Conflict check:

```python
for key in ["neighbors", "pca", "rank_genes_groups"]:
    values = [a.uns.get(key) for a in batches if key in a.uns]
    print(key, len(values), "candidate values")
print(sorted(combined.uns.keys()))
```

## 5. Pairwise Arrays and Graphs

Pairwise arrays on the concatenated axis are omitted by default because zero-padded cross-batch graph or distance entries can be misleading.

```python
without_graphs = ad.concat(batches, axis="obs")
with_graphs = ad.concat(batches, axis="obs", pairwise=True, label="batch", keys=keys)
```

Use `pairwise=True` only when a block-diagonal result is intended. For neighbor graphs, it is often better to concatenate without `.obsp`, normalize/process the combined data, and recompute neighbors.

Alternative-axis pairwise mappings are governed by `merge` rather than `pairwise`; for example, `.varp` while stacking observations can be retained with an appropriate `merge` strategy.

## 6. On-Disk Concat for Large Inputs

Use `anndata.experimental.concat_on_disk` when existing file/stores should be combined into a new output without loading all matrices together.

```python
import anndata as ad

ad.experimental.concat_on_disk(
    {"site_a": "site_a.h5ad", "site_b": "site_b.h5ad"},
    "combined.h5ad",
    axis="obs",
    join="inner",
    label="site",
    index_unique="-",
    merge="same",
    uns_merge="same",
    max_loaded_elems=50_000_000,
)
```

Operational checks:

- Ensure at least one input file/store exists.
- Ensure the output parent directory already exists.
- Do not request `pairwise=True`; on-disk pairwise concatenation raises `NotImplementedError`.
- Use storage guidance for choosing `.h5ad` vs Zarr and for safe backed reads.
- After writing, inspect the result cheaply before loading fully:

```python
combined = ad.read_h5ad("combined.h5ad", backed="r")
print(combined.shape)
print(combined.obs["site"].value_counts())
combined.file.close()
```

## 7. Lazy Multi-Object Access with AnnCollection

Use `AnnCollection` when the task needs lazy observation-axis access across objects without materializing a combined `.X`.

```python
from anndata.experimental import AnnCollection

collection = AnnCollection(
    {"batch_a": adata_a, "batch_b": adata_b},
    join_vars="inner",
    join_obs="inner",
    join_obsm="inner",
    label="batch",
    index_unique="-",
)

view = collection[:128, :]
mini_batch_x = view.X
mini_batch_obs = view.obs
```

Key constraints:

- `AnnCollection` lazily concatenates along observations.
- If variables differ, pass `join_vars="inner"`; otherwise construction raises an error.
- `join_obs="inner"` or `"outer"` copies joined `.obs` annotations into the collection. `join_obs=None` leaves views to access original `.obs` with reindexing.
- `join_obsm="inner"` copies shared `.obsm` keys.
- `convert` can transform `.X`, `.obs`, `.obsm`, or `.layers` values on access, such as encoding labels.
- `to_adata()` is not a full materialization of `.X`; use `anndata.concat` if a complete in-memory `AnnData.X` is required.

`AnnLoader` is deprecated and requires optional PyTorch. Prefer `annbatch.Loader` for new loader-style workflows and use `AnnCollection` for the lazy combined data model.

## 8. Difficult Case: Overlapping Genes and Conflicting `.uns`

For three batches with partially overlapping genes and conflicting `.uns` keys:

```python
combined = ad.concat(
    {"a": a, "b": b, "c": c},
    axis="obs",
    join="outer",
    label="batch",
    index_unique="-",
    merge="same",
    uns_merge="unique",
)
```

Explain the tradeoff:

- `join="outer"` keeps all genes but introduces zeros for sparse missing measurements.
- `merge="same"` avoids retaining variable-level metadata that disagrees after alignment.
- `uns_merge="unique"` recursively keeps nested entries with one possible value and drops true conflicts.
- If conflicting `.uns` entries encode analysis state such as neighbors, drop them or recompute after concat rather than using `"first"`.

## 9. Difficult Case: Memory-Heavy Request with Pairwise Graphs

If a user asks to combine many large `.h5ad` files with `pairwise=True`, split the plan:

1. Use `concat_on_disk(..., pairwise=False)` to create the combined file.
2. Open the output in backed/lazy mode for structural validation.
3. Recompute pairwise graphs after loading or processing the combined data in an environment that can handle the memory footprint.

Do not promise `concat_on_disk(..., pairwise=True)`: that mode is not implemented.
