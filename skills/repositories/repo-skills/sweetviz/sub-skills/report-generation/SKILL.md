---
name: report-generation
description: "Generate and render single-DataFrame Sweetviz reports safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sweetviz report-generation router

Use this sub-skill when the task is to profile one pandas `DataFrame` with Sweetviz, optionally mark one target feature, then save or display the resulting `DataframeReport`.

## Load order

1. Read `references/workflows.md` for single-DataFrame `analyze()` recipes, target/pairwise decisions, HTML/notebook rendering, and output validation.
2. Read `references/api-reference.md` when exact signatures, source shapes, layout/scale parameters, Comet hooks, or verbosity behavior matter.
3. Read `references/troubleshooting.md` when report construction, target validation, pairwise analysis, browser/notebook output, Comet, or font warnings fail.
4. Run `scripts/sweetviz_smoke_report.py --help` or the smoke examples in `references/workflows.md` when a deterministic local report-generation check is useful.

## Scope

This sub-skill covers:

- `sweetviz.analyze(source, target_feat=None, feat_cfg=None, pairwise_analysis='auto')` for one DataFrame; `source` may be a DataFrame or `[df, "Display name"]` / `(df, "Display name")`.
- `DataframeReport.show_html(filepath='SWEETVIZ_REPORT.html', open_browser=True, layout='widescreen', scale=None)`.
- `DataframeReport.show_notebook(w=None, h=None, scale=None, layout=None, filepath=None, file_layout=None, file_scale=None)`.
- Optional `DataframeReport.log_comet(experiment)` and Sweetviz auto-Comet logging only when the external `comet_ml` package and credentials/service are configured.
- Target checks, pairwise `on`/`auto`/`off` selection, browser suppression, layout/scale choices, and generated HTML validation.

## Route elsewhere

- Two-dataset reports, train/test profiling, and intra-DataFrame split comparisons belong in `../dataset-comparison/`.
- Detailed `FeatureConfig`, type inference, low-cardinality numeric forcing, config overrides, duplicate columns, mixed types, and input preflight belong in `../configuration-and-data-handling/`.
- Install/import/package-data issues belong in the root troubleshooting reference `../../references/troubleshooting.md` if that file is present.

## Critical cautions

- Do not pass `verbosity` to public `sweetviz.analyze()` or `sweetviz.compare()`; those public functions do not accept it in the verified installed API. Use config defaults or `DataframeReport(...)` only when verbosity control is required.
- Targets must exist, must not be skipped, must have no missing values, and must be boolean or numeric after Sweetviz type detection/forcing.
- `pairwise_analysis='auto'` can print a threshold warning and return before building a usable full report on wide DataFrames. Choose `pairwise_analysis='off'` for fast deterministic reports or `'on'` only when the user explicitly wants pairwise associations and accepts the cost.
- Use `open_browser=False` for scripts, CI, remote servers, and agent runs unless the user explicitly asks to launch a browser.
