---
name: nullity-utilities
description: "Guides missingno nullity_filter and nullity_sort DataFrame
  completeness filtering, sorting, examples, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# missingno Nullity Utilities

Use this sub-skill when a task asks how to filter columns by completeness, sort
rows or columns by missingness, or understand the `filter`, `n`, `p`, `sort`,
and `axis` parameters used by `missingno` plots.

## Core APIs

```python
import missingno as msno

filtered = msno.nullity_filter(df, filter="bottom", n=10)
sorted_rows = msno.nullity_sort(df, sort="ascending", axis="columns")
```

Read [references/api-reference.md](references/api-reference.md) for exact
source-backed behavior and [references/workflows.md](references/workflows.md)
for recipes.

## Quick semantics

| API | Use it for | Key behavior |
| --- | --- | --- |
| `nullity_filter(df, filter="top", p=.9, n=5)` | Keep complete-enough columns | Threshold by non-null ratio, then cap to highest-completeness columns. |
| `nullity_filter(df, filter="bottom", p=.5, n=10)` | Keep incomplete columns | Threshold by non-null ratio, then cap to lowest-completeness columns. |
| `nullity_sort(df, sort="ascending", axis="columns")` | Sort rows by row completeness | `axis="columns"` counts across columns for each row. |
| `nullity_sort(df, sort="descending", axis="rows")` | Sort columns by column completeness | `axis="rows"` counts down rows for each column. |

## Plot integration

Plot functions reuse these utilities:

- `matrix` filters columns, then sorts rows with `axis="columns"`.
- `bar` filters columns, then sorts columns with `axis="rows"`.
- `heatmap` filters columns, then sorts columns with `axis="rows"` before
  dropping all-full/all-empty columns for correlation.
- `dendrogram` filters columns but does not sort before clustering.

For rendering and interpretation after filtering, read
[../visualizations/SKILL.md](../visualizations/SKILL.md).

## Common decisions

1. Use `filter="bottom"` when the user wants the least complete columns or the
   variables most likely to reveal missingness problems.
2. Use `filter="top"` when the user wants mostly complete columns or wants to
   hide sparse variables.
3. Combine `p` and `n` when a percentage threshold and a maximum column count are
   both needed. Thresholding happens before the numeric cap.
4. Use `axis="columns"` to sort rows and `axis="rows"` to sort columns; the
   names follow pandas count-axis conventions, not natural-language target names.
5. Route plotting, labels, sparklines, heatmap interpretation, and dendrogram
   interpretation to [../visualizations/SKILL.md](../visualizations/SKILL.md).

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) when:

- `sort` or `axis` raises `ValueError`.
- `filter="top"`/`"bottom"` produces a surprising column set.
- `n` and `p` are combined and the output contains fewer columns than expected.
- A plotting function receives an empty or too-small DataFrame after filtering.
