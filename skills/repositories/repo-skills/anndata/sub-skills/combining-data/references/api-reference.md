# Combining Data API Reference

This reference summarizes the public combining APIs and the parameter choices most likely to affect correctness. Use storage-specific guidance in `../storage-io/SKILL.md` for file lifecycle, backed mode, and H5AD/Zarr details.

## Verified Signatures

```python
anndata.concat(
    adatas: Collection[AnnData] | Mapping[str, AnnData],
    *,
    axis: Literal["obs", 0, "var", 1] = "obs",
    join: Literal["inner", "outer"] = "inner",
    merge: Literal[None, "same", "unique", "first", "only"] | Callable | None = None,
    uns_merge: Literal[None, "same", "unique", "first", "only"] | Callable | None = None,
    label: str | None = None,
    keys: Collection | None = None,
    index_unique: str | None = None,
    fill_value: Any | None = None,
    pairwise: bool = False,
    force_lazy: bool = False,
) -> AnnData
```

```python
anndata.experimental.concat_on_disk(
    in_files: Collection[path_or_store] | Mapping[str, path_or_store],
    out_file: path_or_store,
    *,
    max_loaded_elems: int = 100_000_000,
    axis: Literal["obs", 0, "var", 1] = 0,
    join: Literal["inner", "outer"] = "inner",
    merge: Literal[None, "same", "unique", "first", "only"] | Callable | None = None,
    uns_merge: Literal[None, "same", "unique", "first", "only"] | Callable | None = None,
    label: str | None = None,
    keys: Collection[str] | None = None,
    index_unique: str | None = None,
    fill_value: Any | None = None,
    pairwise: bool = False,
) -> None
```

```python
anndata.experimental.AnnCollection(
    adatas: Sequence[AnnData] | dict[str, AnnData],
    *,
    join_obs: Literal["inner", "outer"] | None = "inner",
    join_obsm: Literal["inner"] | None = None,
    join_vars: Literal["inner"] | None = None,
    label: str | None = None,
    keys: Sequence[str] | None = None,
    index_unique: str | None = None,
    convert: Callable | Mapping | None = None,
    harmonize_dtypes: bool = True,
    indices_strict: bool = True,
)
```

`anndata.experimental.AnnLoader(*args, **kwargs)` is a PyTorch DataLoader wrapper for `AnnData`/`AnnCollection`, requires optional PyTorch, and is deprecated in favor of `annbatch.Loader`.

## API Selection

| Situation | Prefer | Why |
| --- | --- | --- |
| Loaded objects should become one materialized `AnnData` | `anndata.concat` | Full feature set, easiest to inspect, supports `pairwise=True` and `force_lazy`. |
| Existing `.h5ad` or Zarr inputs are too large to load together | `experimental.concat_on_disk` | Writes directly to an output store and limits sparse chunks with `max_loaded_elems`. |
| Multiple objects should be browsed or batched lazily along observations | `experimental.AnnCollection` | Avoids copying full matrices; subset returns `AnnCollectionView`. |
| Loader-style PyTorch batches are requested | Prefer `annbatch.Loader`; use `AnnLoader` only for legacy code | `AnnLoader` is deprecated and optional PyTorch-dependent. |

## Parameter Decision Table

| Parameter | Applies To | Choose When | Pitfall |
| --- | --- | --- | --- |
| `axis="obs"` or `0` | concat, on-disk | Stack cells/observations; align variables. | `label` writes to `.obs`; pairwise means `.obsp`. |
| `axis="var"` or `1` | concat, on-disk | Stack variables/features; align observations. | `label` writes to `.var`; pairwise means `.varp`. |
| `join="inner"` | concat, on-disk | Keep only labels shared by every input on the other axis. | Drops non-shared genes/cells silently unless validated. |
| `join="outer"` | concat, on-disk | Keep the union of labels on the other axis. | Sparse arrays fill absent entries with zeros by default; dense arrays and DataFrames get missing values. |
| `merge=None` | concat, on-disk | Drop alternative-axis metadata unless directly concatenated. | `.varm`, `.obsm`, `.layers`, or pairwise metadata may disappear. |
| `merge="same"` | concat, on-disk | Keep alternative-axis values identical in all inputs after alignment. | Values can be dropped if any input differs. |
| `merge="unique"` | concat, on-disk | Keep values with only one possible value per position. | May keep per-batch metadata that is non-conflicting but not universally present. |
| `merge="first"` | concat, on-disk | Trust the first value for conflicts. | Hides conflicts; document why first input should win. |
| `merge="only"` | concat, on-disk | Keep values present in exactly one input. | Usually not appropriate for shared metadata. |
| `uns_merge` | concat, on-disk | Apply the same strategies recursively to `.uns`. | Default `None` yields empty `.uns`; nested conflicts need explicit strategy. |
| `label` | concat, on-disk, AnnCollection | Add dataset/source labels to the concatenated axis annotation. | No provenance column is created when `label=None`. |
| `keys` | concat, on-disk, AnnCollection | Name each input when passing a sequence. | Do not pass `keys` with a mapping input; mapping keys already provide keys. |
| `index_unique` | concat, on-disk, AnnCollection | Make duplicated names unique as `{original}{delimiter}{key}`. | `None` preserves duplicates, which can confuse later indexing. |
| `fill_value` | concat, on-disk | Override fill values introduced by outer joins. | A single sentinel may not be meaningful for both matrix and annotation data. |
| `pairwise=True` | concat | Include block-diagonal pairwise arrays on the concatenated axis. | Cross-batch blocks are zero-filled and often not meaningful. |
| `pairwise=True` | concat_on_disk | Not supported. | Raises `NotImplementedError`; recompute pairwise graphs later or use in-memory concat if feasible. |
| `force_lazy=True` | concat | Request lazy dask concatenation where supported. | Currently affects `.obs`/`.var` and xarray Dataset elements in `.obsm`/`.varm`, not every matrix type. |
| `join_vars="inner"` | AnnCollection | Variables differ and observation-axis lazy collection is acceptable. | Without it, differing `var_names` raise an error. |
| `convert` | AnnCollection | Transform `.X`, `.obs`, `.obsm`, or `.layers` values on subset access. | Converters run during access; keep them deterministic and cheap. |

## Merge Strategy Semantics

`merge` controls elements not aligned to the concatenated axis. While stacking observations, this includes variable-aligned structures such as `.var`, `.varm`, and `.varp`; while stacking variables, it includes observation-aligned structures such as `.obs`, `.obsm`, and `.obsp`.

`uns_merge` uses the same strategies recursively for nested `.uns` mappings:

- `None`: keep no `.uns` entries.
- `"same"`: keep entries equal across all inputs at that nested position.
- `"unique"`: keep entries with only one possible value at that nested position.
- `"first"`: keep the first value encountered at each position.
- `"only"`: keep entries present in exactly one input.

## Validation Checklist

After combining, verify the properties that drove your parameter choices:

```python
print(combined.shape)
print(combined.obs_names.is_unique, combined.var_names.is_unique)
print(combined.obs.get("batch", None))
print(sorted(combined.uns.keys()))
print(sorted(combined.obsp.keys()))  # if pairwise=True along obs
```

For on-disk concat, read the output in backed mode for a cheap structural check before downstream materialization:

```python
import anndata as ad
combined = ad.read_h5ad("combined.h5ad", backed="r")
print(combined.shape)
combined.file.close()
```
