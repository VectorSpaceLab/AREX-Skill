# Data Model Troubleshooting

Use this matrix when AnnData construction, slicing, or mutation fails. Start by printing `adata.shape`, `adata.obs.shape`, `adata.var.shape`, slot keys, and `adata.is_view`; use `scripts/inspect_anndata_structure.py` for an existing object file or a tiny demo.

## Shape And Axis Mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `obs` length error during construction | `len(obs)` differs from `X.shape[0]` or `shape[0]` | Rebuild `obs` with exactly one row per observation; set `obs.index` to intended `obs_names`. |
| `var` length error during construction | `len(var)` differs from `X.shape[1]` or `shape[1]` | Rebuild `var` with exactly one row per variable; set `var.index` to intended `var_names`. |
| `Index of obs must match index of X` | `X` is a DataFrame and explicit `obs.index` differs from `X.index` | Reindex `obs = obs.loc[X.index]` if labels are the same, or choose one source of truth and rebuild. |
| `Index of var must match columns of X` | `X` is a DataFrame and explicit `var.index` differs from `X.columns` | Reindex `var = var.loc[X.columns]` or rename DataFrame columns before construction. |
| `shape` conflict | `shape=` was passed with non-`None` `X` | Remove `shape`; AnnData derives shape from `X`. Use `shape` only for `X=None`. |
| `X needs to be... not <class ...>` | `X` is not an accepted 2D array-like object | Convert to NumPy, SciPy sparse, pandas DataFrame, or another supported array before construction. |

Quick repair pattern:

```python
n_obs, n_vars = X.shape
obs = obs.reindex(expected_obs_names) if set(obs.index) >= set(expected_obs_names) else obs
var = var.reindex(expected_var_names) if set(var.index) >= set(expected_var_names) else var
assert len(obs) == n_obs
assert len(var) == n_vars
adata = ad.AnnData(X=X, obs=obs, var=var)
```

Only reindex when the labels truly refer to the same observations or variables; otherwise rebuild the annotation table from the same source as `X`.

## Aligned Container Mismatches

| Slot | Failure shape | Correct shape | Recovery |
| --- | --- | --- | --- |
| `layers[key]` | Not equal to `adata.shape` | `(n_obs, n_vars)` | Recompute layer from current `X`, subset layer rows/columns to current names, or store non-aligned data in `uns`. |
| `obsm[key]` | First dimension not `n_obs` | `(n_obs, k...)` | Reorder/subset rows to `obs_names`; for DataFrames, ensure index equals `adata.obs_names`. |
| `varm[key]` | First dimension not `n_vars` | `(n_vars, k...)` | Reorder/subset rows to `var_names`; for DataFrames, ensure index equals `adata.var_names`. |
| `obsp[key]` | Not square observation matrix | `(n_obs, n_obs)` | Recompute graph after observation filtering or subset both axes with the same observation indexer. |
| `varp[key]` | Not square variable matrix | `(n_vars, n_vars)` | Recompute or subset both axes with the same variable indexer. |

Diagnosis helper:

```python
for key, value in adata.layers.items():
    print("layers", key, value.shape, "expected", adata.shape)
for key, value in adata.obsm.items():
    print("obsm", key, value.shape, "expected first", adata.n_obs)
for key, value in adata.varm.items():
    print("varm", key, value.shape, "expected first", adata.n_vars)
for key, value in adata.obsp.items():
    print("obsp", key, value.shape, "expected", (adata.n_obs, adata.n_obs))
for key, value in adata.varp.items():
    print("varp", key, value.shape, "expected", (adata.n_vars, adata.n_vars))
```

If data were filtered outside AnnData, apply the same row/column masks to every aligned object before assignment. If many objects must be combined after repair, route combination choices to `../combining-data/SKILL.md`.

## Non-Unique Names

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Warning about non-unique observation names | Duplicate `obs.index` values | Inspect duplicates, decide whether they are true repeated observations, then call `adata.obs_names_make_unique()` or assign a meaningful unique index. |
| Warning about non-unique variable names | Duplicate `var.index` values | Prefer stable unique feature IDs; otherwise call `adata.var_names_make_unique()`. |
| Label-based slicing returns confusing results | Duplicate names make a label ambiguous | Make names unique before slicing or use positional/integer masks intentionally. |

Use helper methods when suffixing is acceptable:

```python
adata.obs_names_make_unique(join="-")
adata.var_names_make_unique(join="-")
```

For biological or business identifiers, prefer explicit IDs over automatic suffixes when downstream interpretation matters.

## MultiIndex Columns Rejected

AnnData rejects DataFrames with MultiIndex columns in constructor-facing tables and in DataFrame values stored in `obsm`/`varm`.

Recovery options:

```python
if isinstance(df.columns, pd.MultiIndex):
    df = df.copy()
    df.columns = ["|".join(map(str, col)) for col in df.columns]
```

Keep the delimiter and original levels documented in `uns` if the hierarchy matters:

```python
adata.uns["original_column_levels"] = [list(level) for level in original.columns.levels]
```

## `ImplicitModificationWarning` And Views

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `Trying to modify attribute ... of view, initializing view as actual` | Code assigns into a sliced AnnData view | If independent mutation was intended, write `subset = adata[mask, :].copy()` before assigning. |
| Warning when assigning `view.obs[...]`, `view.layers[...]`, or `view.X[...]` | Copy-on-modify actualizes the view | Accept it only if actualization is intended; otherwise mutate the parent explicitly. |
| Warning about transforming to string index | Constructor converted index values, often integers, to strings | Use explicit string indexes before construction when names matter. |

Explain copy-on-modify this way: slicing returns a lightweight view of the parent; assigning into the view warns and turns the view into a real object, so future edits apply to that object. Do not rely on view mutation as a parent-update mechanism.

Safe patterns:

```python
# Independent subset
subset = adata[mask, :].copy()
subset.obs["flag"] = True

# Intentional parent update
adata.obs.loc[adata.obs_names[mask], "flag"] = True
```

## Backed Mode Mutation Mistakes

This sub-skill can identify backed state but should not own storage lifecycle repairs.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `adata.isbacked` is true and `.copy()` asks for a filename | Object was opened in backed mode | Use `adata.to_memory()` for in-memory work or route on-disk copying to `../storage-io/SKILL.md`. |
| Mutating backed arrays does not behave like normal in-memory mutation | Data live in an `.h5ad` or store-backed object | Load to memory before complex edits, or use storage-aware write workflows in `../storage-io/SKILL.md`. |
| File handle/path errors while inspecting data | Backed file lifecycle issue | Close/reopen through storage APIs; route details to `../storage-io/SKILL.md`. |

Recovery for data-model tasks:

```python
if getattr(adata, "isbacked", False):
    adata = adata.to_memory(copy=True)
```

Then validate shape and aligned slots again before continuing.

## Dtype, Categorical, And Index Surprises

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Integer indexes become strings | AnnData normalizes indexes for consistent label lookup | Create intended string names explicitly before construction. |
| Categories disappear after slicing | `anndata.settings.remove_unused_categories=True` removes unused categories from views | If all categories must remain, restore categories after copying or adjust settings intentionally for the operation. |
| Object dtype columns or strings behave unexpectedly in storage | Pandas dtype choices interact with write/read conversion | Normalize dtypes before storage; route write-specific issues to `../storage-io/SKILL.md`. |
| Sparse `to_df()` uses too much memory | `to_df()` densifies sparse matrices | Inspect shape and density first; extract only needed variables or use sparse-aware calculations. |

## `.raw` Problems

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `.raw` is `None` | No raw snapshot was set | Set `adata.raw = adata.copy()` before destructive normalization or variable filtering. |
| `.raw.var_names` includes genes missing from `adata.var_names` | `.raw` keeps its own variable axis | This is expected; use `adata.raw[:, gene].X` to access original variables. |
| Assigning `.raw` raises a type or observation-count error | Raw must be initialized from an AnnData with matching observations | Build a matching AnnData snapshot or clear with `adata.raw = None`. |
| Layer was used as if it were raw | Layers follow current variables; raw can preserve removed variables | Use `layers` for current-shape alternative matrices and `.raw` for a historical snapshot. |

## Repair Case: Inconsistent `X`, `obs`, `var`, `obsm`, And `layers`

1. Choose the authoritative `X` or DataFrame matrix.
2. Set `expected_obs_names` from `X.index` if `X` is a DataFrame, otherwise from the source observation table.
3. Set `expected_var_names` from `X.columns` if `X` is a DataFrame, otherwise from the source variable table.
4. Reorder or rebuild `obs` and `var` to those names.
5. For every `layers[key]`, require exactly `X.shape`; drop, recompute, or subset mismatched layers.
6. For every `obsm[key]`, require first dimension `len(expected_obs_names)` and matching DataFrame index when applicable.
7. Construct `AnnData`, then run the inspection script and final uniqueness checks.

## Repair Case: Mutating A Sliced View

When a user asks why this warns:

```python
view = adata[adata.obs["batch"] == "a", :]
view.obs["flag"] = True
```

Answer:

- `view` starts as `is_view=True`.
- Assignment to `.obs` triggers copy-on-modify and emits `ImplicitModificationWarning`.
- The view becomes an actual independent object after the assignment.
- The parent `adata` is not the intended mutation target.
- Use `view = adata[mask, :].copy()` before editing, or update `adata.obs.loc[...]` if the parent should change.
