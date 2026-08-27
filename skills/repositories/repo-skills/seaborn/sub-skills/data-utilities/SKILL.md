---
name: data-utilities
description: "Use seaborn data utilities and data-shape contracts for long-form,
  wide-form, vector, semantic mapping, and example dataset workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Data Utilities

Use this sub-skill when a task is blocked by seaborn data shape, variable mapping, `load_dataset`, `SEABORN_DATA`, example data caching, or validating a DataFrame before plotting.

## Route Here For

- Long-form/tidy versus wide-form plotting decisions.
- Direct vector/list/array/dict inputs and when named variables require `data=`.
- Semantic mappings: `hue`, `size`, `style`, `row`, `col`, `units`, `weights`.
- `load_dataset`, `get_dataset_names`, `get_data_home`, cache directories, network requirements, and example-data misuse.
- Diagnosing missing columns, null-heavy variables, numeric/categorical axis confusion, and heatmap mask shape.
- Creating synthetic no-network data for reproducible examples.

## Use Another Sub-skill For

- Plot-function parameters after data is valid: `../function-interface/SKILL.md`.
- Grid layout/legend/axes access: `../figure-grids/SKILL.md`.
- Palette/theme selection: `../themes-palettes/SKILL.md`.

## Start With

1. Inspect input object type and columns.
2. Decide long-form, wide-form, or vector mode.
3. Validate every named semantic variable exists in `data`.
4. Check numeric requirements for x/y or matrix data.
5. Avoid network-backed `load_dataset` unless examples or bug reports explicitly require seaborn sample data.

## References

- Data format guide: `references/data-formats.md`.
- Dataset utility behavior: `references/dataset-utilities.md`.
- Failure recovery: `references/troubleshooting.md`.
- Shared data semantics: `../../references/data-semantics.md`.

## Quick Preflight

```bash
python sub-skills/data-utilities/scripts/validate_plot_data.py --csv data.csv --x x_col --y y_col --hue group_col
```

Use `--demo` to validate the script's built-in synthetic data without a CSV.
