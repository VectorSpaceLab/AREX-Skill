---
name: sweetviz
description: "Use Sweetviz to generate pandas EDA reports, compare tabular
  datasets, configure feature typing, and troubleshoot HTML/notebook output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sweetviz repo skill

Use this skill when a task involves Sweetviz, pandas exploratory data analysis reports, target-aware tabular profiling, train/test dataset comparison, feature type overrides, Sweetviz config files, or Sweetviz HTML/notebook output troubleshooting.

## Quick start

1. Install Sweetviz in the active project environment:

   ```bash
   python -m pip install sweetviz
   ```

   For source checkouts or local fixes, use an editable install from that checkout:

   ```bash
   python -m pip install -e .
   ```

2. Verify the public import and signatures before writing guidance that depends on exact parameters:

   ```python
   import sweetviz as sv
   print(sv.__version__)
   print(sv.analyze)
   ```

   Or run the bundled environment checker:

   ```bash
   python scripts/check_sweetviz_install.py --json
   ```

3. Route to a sub-skill for the actual workflow.

## Route map

- Use `sub-skills/report-generation/` when the user wants to create a Sweetviz report from one pandas `DataFrame`, choose a target, save HTML with `show_html()`, embed with `show_notebook()`, control layout/scale, avoid browser launches, or understand optional Comet logging.
- Use `sub-skills/dataset-comparison/` when the user wants to compare train/test DataFrames, baseline/current datasets, or two groups from one DataFrame with `compare()` or `compare_intra()`.
- Use `sub-skills/configuration-and-data-handling/` when the user mentions `FeatureConfig`, skipped/forced feature types, wrong type inference, config overrides, quiet/progress-only output, duplicate columns, target NaNs, mixed types, CJK fonts, or preflight validation.

Common tasks often need two routes: validate/force feature types with `configuration-and-data-handling`, then render with `report-generation` or compare with `dataset-comparison`.

## Public API orientation

Sweetviz 2.3.3 exposes these primary objects from `import sweetviz as sv`:

- `sv.analyze(source, target_feat=None, feat_cfg=None, pairwise_analysis='auto')`
- `sv.compare(source, compare, target_feat=None, feat_cfg=None, pairwise_analysis='auto')`
- `sv.compare_intra(source_df, condition_series, names, target_feat=None, feat_cfg=None, pairwise_analysis='auto')`
- `sv.FeatureConfig(skip=None, force_cat=None, force_text=None, force_num=None)`
- `sv.DataframeReport` with `show_html()`, `show_notebook()`, and `log_comet()` methods
- `sv.config_parser` for INI-style defaults such as verbosity, layouts, CJK fonts, and type thresholds

Do not pass `verbosity=` to public `sv.analyze()` or `sv.compare()` in this version. Use `[General] default_verbosity` through `sv.config_parser` or the lower-level `DataframeReport(..., verbosity=...)` path when that trade-off is intentional.

## Shared references and scripts

- Read [compatibility and assets](references/compatibility-and-assets.md) for package dependencies, Python support, optional extras, packaged templates/fonts/styles, and why there is no Sweetviz CLI route.
- Read [troubleshooting](references/troubleshooting.md) for install/import failures, shadowed modules, package-data/template errors, font/browser/notebook issues, optional Comet behavior, and broad data compatibility symptoms.
- Read [repo provenance](references/repo-provenance.md) before deciding whether this skill is current for a Sweetviz checkout or should be refreshed.
- Run [check_sweetviz_install.py](scripts/check_sweetviz_install.py) to verify importability, version metadata, public signatures, packaged assets, and optional tiny HTML rendering without opening a browser.

## Cautions

- Targets must exist in the source data, must not be skipped, must contain no missing values, and must be boolean or numeric after Sweetviz type detection/forcing.
- Numeric columns with at most the configured distinct-value threshold infer as categorical by default. Force known numeric low-cardinality columns with `FeatureConfig(force_num=[...])` when needed.
- `pairwise_analysis='auto'` can warn and return early for wide data; use `'off'` for deterministic smoke reports or `'on'` only when the user explicitly wants associations and accepts the cost.
- Sweetviz has no console entry point in this package version. Use the Python API or bundled skill helper scripts.
- Optional Comet.ml logging is external and credentialed. Do not require it for local report generation or verification unless the user explicitly asks for Comet integration.
