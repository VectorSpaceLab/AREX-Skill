---
name: combining-data
description: "Combine AnnData objects in memory or on disk with concat,
  concat_on_disk, AnnCollection, merge strategies, batch labels, duplicate-name
  handling, and lazy collection guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Combining AnnData Objects and Files

Use this sub-skill when the task is to stack, merge, batch-label, lazily view, or write a combined result from multiple `AnnData` inputs. Typical prompts mention `anndata.concat`, partially overlapping genes, preserving dataset labels, duplicate observation names, `.uns` conflicts, `.obsp`/`.varp` pairwise arrays, memory pressure, `experimental.concat_on_disk`, `experimental.AnnCollection`, or loader-style access across batches.

## Quick Routing

- Use [`references/api-reference.md`](references/api-reference.md) for verified signatures and a parameter decision table for `anndata.concat`, `anndata.experimental.concat_on_disk`, and `anndata.experimental.AnnCollection`.
- Use [`references/concat-workflows.md`](references/concat-workflows.md) for recipes covering inner/outer joins, labels and keys, recursive `.uns` merging, pairwise arrays, on-disk concat, and lazy collections.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) for duplicate names, mapping/`keys` conflicts, outer-join fill surprises, unsupported on-disk pairwise concat, `AnnCollection` variable mismatches, and memory pressure.
- Use [`scripts/plan_anndata_concat.py`](scripts/plan_anndata_concat.py) to turn simple JSON batch metadata into recommended concat parameters and risk warnings.

## Default Decision Pattern

1. Identify the input shape: loaded `AnnData` objects, a mapping of named objects, file paths/stores for `.h5ad` or Zarr, or a need for lazy mini-batch access.
2. Pick the concatenation axis: `axis="obs"` stacks observations and aligns variables; `axis="var"` stacks variables and aligns observations.
3. Pick `join`: `join="inner"` keeps only shared labels on the non-concatenated axis; `join="outer"` keeps the union and introduces filled values.
4. Preserve provenance with a mapping input or `keys`, plus `label="batch"` or another categorical column name.
5. Handle duplicate names on the concatenated axis with `index_unique="-"` when original indexes may overlap.
6. Choose `merge` and `uns_merge`: start with `"same"` for conservative shared metadata or `"unique"` for non-conflicting metadata; avoid `"first"` unless first-input-wins is intentional.
7. Choose pairwise behavior: keep `pairwise=False` unless block-diagonal `.obsp` or `.varp` arrays with zero cross-batch blocks are meaningful.
8. Choose execution mode: use `anndata.concat` for loaded objects, `experimental.concat_on_disk` for large existing stores, and `experimental.AnnCollection` for lazy observation-axis access.
9. Validate the result: shape, index uniqueness, label categories, retained metadata keys, fill values, and whether pairwise matrices are present or intentionally omitted.

## Boundary Links

- For constructing or validating individual `AnnData` objects before combining, route to [`../data-model/SKILL.md`](../data-model/SKILL.md).
- For reading/writing `.h5ad` or Zarr files, backed/lazy file lifecycle, or storage-format details around on-disk concat, route to [`../storage-io/SKILL.md`](../storage-io/SKILL.md).
- `AnnLoader` requires optional PyTorch support and is deprecated in favor of `annbatch.Loader`; prefer `AnnCollection` guidance here and route PyTorch loader migration decisions outside this sub-skill.
