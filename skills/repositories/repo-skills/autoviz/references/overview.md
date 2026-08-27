# AutoViz package overview

AutoViz is a Python package for quick exploratory data visualization of tabular data. Its main user surface is `AutoViz_Class.AutoViz`, which accepts either a filename or a pandas DataFrame and produces a sampled, variable-classified set of plots.

## Main modules

| Module | Runtime role |
| --- | --- |
| `autoviz.__init__` | Exposes `AutoViz_Class`, `FixDQ`, and `data_cleaning_suggestions`; prints an import banner in this repository version. |
| `autoviz.AutoViz_Class` | Main public class, main plotting entry point, data-quality report call, and `FixDQ` subclass. |
| `autoviz.AutoViz_Utils` | Static matplotlib/seaborn plotting helpers, file loading, variable classification, problem-type inference, and feature selection. |
| `autoviz.AutoViz_Holo` | HoloViews/Bokeh/Panel implementation for `bokeh`, `server`, and `html` chart formats. |
| `autoviz.AutoViz_NLP` | Text-cleaning helpers and wordcloud generation for string variables. |
| `autoviz.classify_method` | Standalone variable-classification helpers. |

## Primary workflow

1. Import and instantiate `AutoViz_Class`.
2. Provide exactly one data source: a path via `filename`, or a DataFrame via `dfte` with `filename=""`.
3. Set `depVar` only when a target column is available.
4. Choose `chart_format` and `verbose` according to display or file-output needs.
5. Let AutoViz classify variables, run a data-quality report, then draw plots.

## Route by user intent

- Visualization, chart formats, output folders, and large-data sampling: use `sub-skills/eda-visualization/`.
- Reports, cleaning, `FixDQ`, or `pandas_dq`: use `sub-skills/data-quality-fixes/`.
- Text columns, wordclouds, NLTK, or string cleanup: use `sub-skills/text-wordclouds/`.

## Non-goals

- AutoViz is not a model-training framework.
- It does not require GPU hardware for the covered workflows.
- This skill does not depend on the original repository checkout; use the bundled references and scripts instead of source notebooks.
