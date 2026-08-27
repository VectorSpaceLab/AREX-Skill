# Configuration Reference

## When to read

Read this for actual settings field names and common configuration patterns.

## Three configuration mechanisms

1. Constructor keyword arguments:

```python
profile = ProfileReport(df, title="My report", pool_size=1, minimal=True)
```

2. A YAML file:

```python
profile = ProfileReport(df, config_file="profiling-config.yml")
```

3. Environment variables with the `PROFILE_` prefix:

```python
import os
os.environ["PROFILE_TITLE"] = "Environment title"
os.environ["PROFILE_PLOT"] = '{"dpi": 1000}'
profile = ProfileReport(df)
```

## Important `Settings` fields

| Area | Fields and notes |
| --- | --- |
| General | `title`, `infer_dtypes`, `show_variable_description`, `pool_size`, `progress_bar`, `sort`, `memory_deep`, `reject_variables` |
| Metadata | `dataset.description`, `creator`, `author`, `copyright_holder`, `copyright_year`, `url`; `variables.descriptions` for column dictionaries |
| Samples/duplicates | `samples.head`, `samples.tail`, `samples.random`, `duplicates.head` |
| Missing values | `missing_diagrams.bar`, `matrix`, `heatmap` |
| Correlations | `correlations.auto`, `pearson`, `spearman`, `kendall`, `phi_k`, `cramers`; each has `calculate`, `threshold`, and related fields |
| Interactions | `interactions.continuous`, `interactions.targets` |
| Variables | `vars.num`, `vars.cat`, `vars.text`, `vars.bool`, `vars.file`, `vars.path`, `vars.image`, `vars.url`, `vars.timeseries` |
| Plots | `plot.image_format`, `plot.dpi`, `plot.scatter_threshold`, `plot.correlation`, `plot.missing`, `plot.cat_freq`, `plot.histogram`, `plot.font_path` |
| Report | `report.precision` |
| HTML | `html.inline`, `html.use_local_assets`, `html.navbar_show`, `html.minify_html`, `html.assets_prefix`, `html.style.theme`, `html.style.logo`, `html.style.primary_colors`, `html.full_width` |
| Notebook | `notebook.iframe.height`, `width`, `attribute` |

## Shorthands

These constructor values expand to groups of settings:

```python
ProfileReport(
    df,
    samples=None,
    duplicates=None,
    correlations=None,
    missing_diagrams=None,
    interactions=None,
)
```

Effect:
- hide samples and duplicates;
- disable correlation computations;
- disable missing diagrams;
- disable continuous interactions.

`explorative=True` enables richer categorical/text details and activates URL,
path, file, and image analysis. `sensitive=True` redacts categorical/text values
and suppresses some direct data exposure, but privacy-specific choices should be
made with the comparison/quality sub-skill.

## Minimal preset

`minimal=True` loads a built-in minimal profile configuration. It disables many
expensive sections and hides samples/duplicates. It is mutually exclusive with
`config_file`; copy the desired settings into a YAML file if you need both
minimal-like behavior and custom config-file reuse.

## Example performance/privacy YAML

```yaml
title: Safe profiling report
infer_dtypes: false
progress_bar: true
samples:
  head: 0
  tail: 0
  random: 0
duplicates:
  head: 0
missing_diagrams:
  bar: false
  matrix: false
  heatmap: false
correlations:
  auto:
    calculate: false
  pearson:
    calculate: false
  spearman:
    calculate: false
  kendall:
    calculate: false
  phi_k:
    calculate: false
  cramers:
    calculate: false
interactions:
  continuous: false
  targets: []
html:
  inline: true
  navbar_show: true
```

Use the bundled `write_minimal_config.py` script to generate and validate a
starter config instead of manually typing a long YAML file.
