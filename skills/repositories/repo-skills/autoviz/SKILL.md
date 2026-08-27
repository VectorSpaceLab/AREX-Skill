---
name: autoviz
description: "Routes AutoViz users to automated EDA, data-quality, and
  text/wordcloud workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# AutoViz

Use this skill when a user wants to explore a tabular dataset with AutoViz, fix data-quality problems with `FixDQ`, or generate wordclouds from string columns. Keep this skill router-like: send the user to the most specific sub-skill, then use the bundled references and scripts for details.

## First decision

- If the task is about loading a file or DataFrame and producing plots, use [`sub-skills/eda-visualization/SKILL.md`](sub-skills/eda-visualization/SKILL.md).
- If the task is about data-quality reporting or `FixDQ`, use [`sub-skills/data-quality-fixes/SKILL.md`](sub-skills/data-quality-fixes/SKILL.md).
- If the task is about text columns, NLP cleanup, or wordclouds, use [`sub-skills/text-wordclouds/SKILL.md`](sub-skills/text-wordclouds/SKILL.md).

## Minimal usage shape

```python
from autoviz import AutoViz_Class

AV = AutoViz_Class()
dft = AV.AutoViz(
    filename,
    sep=",",
    depVar="",
    dfte=df,
    header=0,
    verbose=1,
    lowess=False,
    chart_format="svg",
    max_rows_analyzed=150000,
    max_cols_analyzed=30,
    save_plot_dir=None,
)
```

## What to read next

- Read [`references/overview.md`](references/overview.md) for the package surface and the quickest route to the right sub-skill.
- Read [`references/install-and-compatibility.md`](references/install-and-compatibility.md) if imports, `pip check`, `xgboost`, pandas, or interactive-backend dependencies fail.
- Read [`references/chart-formats.md`](references/chart-formats.md) when the user asks for `png`, `svg`, `jpg`, `bokeh`, `server`, or `html` output behavior.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for import, environment, plotting, and text-column failure modes.
- Read [`references/api-reference.md`](references/api-reference.md) when you need exact signatures or helper names.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need to check source freshness or decide whether the skill should be refreshed.
- Read [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) when you need the managed router placement metadata used during import.
- Read [`scripts/inspect_install.py`](scripts/inspect_install.py) when you need a quick runtime snapshot from a prepared environment.

## Common routing cues

- `AutoViz_Class`, `AutoViz_Main`, `filename`, `dfte`, `chart_format`, `save_plot_dir`, `max_rows_analyzed`, or `max_cols_analyzed` usually mean the EDA sub-skill.
- `FixDQ`, `data_cleaning_suggestions`, duplicate rows, infinity, rare categories, mixed types, or leakage usually mean the data-quality sub-skill.
- `wordcloud`, `nltk`, `textblob`, `emoji`, `stopwords`, `discrete string`, or NLP columns usually mean the text sub-skill.
- If the user asks about installation, package versions, or why `import autoviz` fails, route to the relevant references first and then return to the right sub-skill.

## Import note

`import autoviz` prints a banner in this repository version. That is expected and not a failure.

## Quick expectations

- The package is CPU-oriented.
- Interactive chart formats depend on `hvplot`, `holoviews`, `panel`, `bokeh`, and `IPython`.
- `data_cleaning_suggestions` uses `pandas_dq`.
- `FixDQ` is the transformer-style path for reusable data-quality cleanup.
- Wordcloud generation may trigger an NLTK download if string columns are present.
- A tiny toy DataFrame can be classified in surprising ways, so use the bundled smoke scripts when debugging.

## What not to do

- Do not point users at the original source checkout as a required runtime dependency.
- Do not suggest source notebooks or repo tests as the primary user workflow when a bundled script exists.
- Do not claim accelerator requirements; this skill's covered workflows are CPU-based.
- Do not hide compatibility warnings in prose when `pip check` or import output shows a concrete failure.

## Handoff shape

When the user is still deciding, keep the response short and route them to the right sub-skill plus the correct reference.
When the user wants action, use the bundled script for that sub-skill, verify the runtime, and then summarize the result in package terms rather than source-file terms.

## Escalation

If the user wants a broader comparison with another package, first finish the AutoViz route and then explain the boundary clearly.
If the issue is really a repository install or compatibility failure, point them to the install-and-compatibility and troubleshooting references before changing the workflow.
